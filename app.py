"""
Flask application for the data labeling platform
"""
from flask import Flask, render_template, jsonify, request, session
from datetime import datetime
import json
import os
from typing import Dict, List, Optional

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

# Import classes from the labeling algorithm
class User:
    def __init__(self, user_id: str, name: str, email: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.total_labels = 0
        self.correct_labels = 0
        self.expertise_by_category = {}
        self.labels_by_category = {}
    
    def get_accuracy(self) -> float:
        if self.total_labels == 0:
            return 0.0
        return self.correct_labels / self.total_labels
    
    def get_category_expertise(self, category: str) -> float:
        return self.expertise_by_category.get(category, 0.0)
    
    def update_label_stats(self, category: str, correct: bool):
        self.total_labels += 1
        if correct:
            self.correct_labels += 1
        
        if category not in self.labels_by_category:
            self.labels_by_category[category] = 0
            self.expertise_by_category[category] = 0.0
        
        self.labels_by_category[category] += 1
        
        if correct:
            self.expertise_by_category[category] = min(
                1.0,
                self.expertise_by_category[category] + (1.0 / max(1, self.labels_by_category[category]))
            )
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'total_labels': self.total_labels,
            'accuracy': self.get_accuracy(),
            'expertise_by_category': self.expertise_by_category,
            'labels_by_category': self.labels_by_category
        }


class DataItem:
    def __init__(self, item_id: str, content: str, content_type: str, 
                 categories: List[str], is_binary: bool = False):
        self.item_id = item_id
        self.content = content
        self.content_type = content_type
        self.categories = categories
        self.is_binary = is_binary
        self.labels = []
        self.consensus_label = None
        self.confidence = 0.0
    
    def add_label(self, user_id: str, label: str, user_expertise: float = 0.5):
        self.labels.append({
            'user_id': user_id,
            'label': label,
            'expertise': user_expertise,
            'timestamp': datetime.now().isoformat()
        })
        self._calculate_consensus()
    
    def _calculate_consensus(self):
        if not self.labels:
            return
        
        label_scores = {}
        total_weight = 0.0
        
        for label_data in self.labels:
            label = label_data['label']
            expertise = label_data['expertise']
            weight = max(0.1, expertise)
            
            if label not in label_scores:
                label_scores[label] = 0.0
            label_scores[label] += weight
            total_weight += weight
        
        if label_scores:
            self.consensus_label = max(label_scores, key=label_scores.get)
            self.confidence = label_scores[self.consensus_label] / total_weight
    
    def to_dict(self) -> Dict:
        return {
            'item_id': self.item_id,
            'content': self.content,
            'content_type': self.content_type,
            'categories': self.categories,
            'is_binary': self.is_binary,
            'labels_count': len(self.labels),
            'consensus_label': self.consensus_label,
            'confidence': self.confidence
        }


class LabelingSystem:
    def __init__(self):
        self.users = {}
        self.data_items = {}
        self.user_labels = {}
    
    def add_user(self, user: User):
        self.users[user.user_id] = user
        if user.user_id not in self.user_labels:
            self.user_labels[user.user_id] = []
    
    def add_data_item(self, item: DataItem):
        self.data_items[item.item_id] = item
    
    def get_next_item_for_user(self, user_id: str) -> Optional[DataItem]:
        if user_id not in self.users:
            return None
        
        labeled_items = set(self.user_labels.get(user_id, []))
        
        unlabeled = [
            item for item_id, item in self.data_items.items()
            if item_id not in labeled_items
        ]
        
        if not unlabeled:
            return None
        
        unlabeled.sort(key=lambda x: (len(x.labels), x.confidence))
        return unlabeled[0]
    
    def submit_label(self, user_id: str, item_id: str, label: str):
        if user_id not in self.users or item_id not in self.data_items:
            return False
        
        user = self.users[user_id]
        item = self.data_items[item_id]
        
        category = label if not item.is_binary else item.categories[0]
        expertise = user.get_category_expertise(category)
        
        item.add_label(user_id, label, expertise)
        
        if user_id not in self.user_labels:
            self.user_labels[user_id] = []
        self.user_labels[user_id].append(item_id)
        
        return True
    
    def get_user_stats(self, user_id: str) -> Optional[Dict]:
        if user_id not in self.users:
            return None
        return self.users[user_id].to_dict()
    
    def get_item_status(self, item_id: str) -> Optional[Dict]:
        if item_id not in self.data_items:
            return None
        return self.data_items[item_id].to_dict()


# Initialize the system
labeling_system = LabelingSystem()

# Create sample users
sample_users = [
    User('user_1', 'Alice Johnson', 'alice@example.com'),
    User('user_2', 'Bob Smith', 'bob@example.com'),
    User('user_3', 'Charlie Brown', 'charlie@example.com'),
]

for user in sample_users:
    labeling_system.add_user(user)

# Load sample data items
sample_items = [
    DataItem('item_1', 'static/sample_data/tree.jpg', 'image', ['tree', 'bird', 'car', 'building'], False),
    DataItem('item_2', 'static/sample_data/bird.jpg', 'image', ['tree', 'bird', 'car', 'building'], False),
    DataItem('item_3', 'static/sample_data/car.jpg', 'image', ['tree', 'bird', 'car', 'building'], False),
    DataItem('item_4', 'static/sample_data/building.jpg', 'image', ['tree', 'bird', 'car', 'building'], False),
    DataItem('item_5', 'static/sample_data/cat.jpg', 'image', ['yes', 'no'], True),
]

for item in sample_items:
    labeling_system.add_data_item(item)


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/login', methods=['POST'])
def login():
    """Simple login endpoint"""
    data = request.json
    user_id = data.get('user_id')
    
    if user_id in labeling_system.users:
        session['user_id'] = user_id
        return jsonify({
            'success': True,
            'user': labeling_system.users[user_id].to_dict()
        })
    
    return jsonify({'success': False, 'error': 'User not found'}), 404


@app.route('/api/user/stats')
def get_user_stats():
    """Get current user's statistics"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    stats = labeling_system.get_user_stats(user_id)
    if stats:
        return jsonify(stats)
    
    return jsonify({'error': 'User not found'}), 404


@app.route('/api/next_item')
def get_next_item():
    """Get the next item for the user to label"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    item = labeling_system.get_next_item_for_user(user_id)
    if item:
        return jsonify(item.to_dict())
    
    return jsonify({'error': 'No more items to label'}), 404


@app.route('/api/submit_label', methods=['POST'])
def submit_label():
    """Submit a label for an item"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    item_id = data.get('item_id')
    label = data.get('label')
    
    if not item_id or not label:
        return jsonify({'error': 'Missing item_id or label'}), 400
    
    success = labeling_system.submit_label(user_id, item_id, label)
    if success:
        return jsonify({'success': True})
    
    return jsonify({'error': 'Failed to submit label'}), 400


@app.route('/api/users')
def list_users():
    """List all users (for demo purposes)"""
    users = [user.to_dict() for user in labeling_system.users.values()]
    return jsonify(users)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
