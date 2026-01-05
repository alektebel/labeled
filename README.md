# Labeled

Platform that allows for decentralized labeling of data. Currently supporting multiclass and binary classification labeling.

## Features

- **Tinder-like Interface**: Swipe left/right for binary classification
- **Multiclass Labeling**: Select from multiple categories for complex classification
- **User Expertise Tracking**: Each user has expertise markers showing their accuracy per category
- **Consensus Algorithm**: Uses weighted voting based on user expertise to determine final labels
- **Sample Data**: Includes sample images for testing (tree, bird, car, building, cat)

## Algorithm

The labeling algorithm is implemented in `labeling_algorithm.ipynb` and includes:

- **User Model**: Tracks user statistics, accuracy, and category-specific expertise
- **Data Item Model**: Manages items to be labeled with consensus calculation
- **Labeling System**: Coordinates the labeling workflow and prioritizes items

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask application:
```bash
python app.py
```

3. Open your browser to `http://localhost:5000`

## Usage

1. Select a user from the login screen (sample users: Alice, Bob, Charlie)
2. For binary classification items: Swipe left (No) or right (Yes)
3. For multiclass items: Click on the appropriate category button
4. View your expertise scores and labeling statistics in real-time

## Project Structure

```
labeled/
├── app.py                      # Flask backend application
├── labeling_algorithm.ipynb    # Jupyter notebook with labeling algorithm
├── requirements.txt            # Python dependencies
├── templates/
│   └── index.html             # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css          # Styling for the interface
│   ├── js/
│   │   └── app.js             # Frontend JavaScript
│   └── sample_data/
│       ├── tree.jpg           # Sample images
│       ├── bird.jpg
│       ├── car.jpg
│       ├── building.jpg
│       └── cat.jpg
```

## How It Works

1. **User Expertise**: Each user starts with no expertise. As they label items, their expertise in each category increases based on label quality.

2. **Weighted Consensus**: When multiple users label the same item, the system uses weighted voting based on user expertise to determine the consensus label.

3. **Item Prioritization**: The system prioritizes showing items that have fewer labels or lower confidence scores.

4. **Binary vs Multiclass**: The interface automatically adapts based on the item type:
   - Binary: Tinder-like swipe interface
   - Multiclass: Category selection buttons
