// State management
let currentUser = null;
let currentItem = null;

// DOM Elements
const loginSection = document.getElementById('login-section');
const labelingSection = document.getElementById('labeling-section');
const userSelect = document.getElementById('user-select');
const loginBtn = document.getElementById('login-btn');
const logoutBtn = document.getElementById('logout-btn');
const userName = document.getElementById('user-name');
const totalLabels = document.getElementById('total-labels');
const accuracy = document.getElementById('accuracy');
const expertiseList = document.getElementById('expertise-list');
const binaryInterface = document.getElementById('binary-interface');
const multiclassInterface = document.getElementById('multiclass-interface');
const noItems = document.getElementById('no-items');
const itemContainer = document.getElementById('item-container');

// Initialize
async function init() {
    await loadUsers();
    setupEventListeners();
}

// Load users for selection
async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        const users = await response.json();
        
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.user_id;
            option.textContent = `${user.name} (${user.email})`;
            userSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    loginBtn.addEventListener('click', handleLogin);
    logoutBtn.addEventListener('click', handleLogout);
    
    // Binary classification buttons
    document.getElementById('swipe-left').addEventListener('click', () => handleBinaryLabel('no'));
    document.getElementById('swipe-right').addEventListener('click', () => handleBinaryLabel('yes'));
}

// Handle login
async function handleLogin() {
    const userId = userSelect.value;
    if (!userId) {
        alert('Please select a user');
        return;
    }
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        
        const data = await response.json();
        if (data.success) {
            currentUser = data.user;
            showLabelingSection();
            updateUserStats();
            loadNextItem();
        } else {
            alert('Login failed');
        }
    } catch (error) {
        console.error('Error logging in:', error);
        alert('Login failed');
    }
}

// Handle logout
function handleLogout() {
    currentUser = null;
    currentItem = null;
    loginSection.classList.remove('hidden');
    labelingSection.classList.add('hidden');
}

// Show labeling section
function showLabelingSection() {
    loginSection.classList.add('hidden');
    labelingSection.classList.remove('hidden');
}

// Update user stats
function updateUserStats() {
    if (!currentUser) return;
    
    userName.textContent = currentUser.name;
    totalLabels.textContent = currentUser.total_labels;
    accuracy.textContent = Math.round(currentUser.accuracy * 100) + '%';
    
    // Update expertise
    updateExpertiseDisplay();
}

// Update expertise display
function updateExpertiseDisplay() {
    if (!currentUser || !currentUser.expertise_by_category || Object.keys(currentUser.expertise_by_category).length === 0) {
        expertiseList.innerHTML = '<p class="text-muted">Start labeling to build your expertise!</p>';
        return;
    }
    
    expertiseList.innerHTML = '';
    for (const [category, score] of Object.entries(currentUser.expertise_by_category)) {
        const item = document.createElement('div');
        item.className = 'expertise-item';
        
        const percentage = Math.round(score * 100);
        item.innerHTML = `
            <div style="flex: 1;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span class="category">${category}</span>
                    <span class="score">${percentage}%</span>
                </div>
                <div class="expertise-bar">
                    <div class="expertise-bar-fill" style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
        expertiseList.appendChild(item);
    }
}

// Load next item
async function loadNextItem() {
    try {
        const response = await fetch('/api/next_item');
        
        if (response.status === 404) {
            showNoItems();
            return;
        }
        
        const item = await response.json();
        currentItem = item;
        displayItem(item);
    } catch (error) {
        console.error('Error loading next item:', error);
        showNoItems();
    }
}

// Display item
function displayItem(item) {
    noItems.classList.add('hidden');
    itemContainer.classList.remove('hidden');
    
    if (item.is_binary) {
        displayBinaryItem(item);
    } else {
        displayMulticlassItem(item);
    }
}

// Display binary classification item
function displayBinaryItem(item) {
    binaryInterface.classList.remove('hidden');
    multiclassInterface.classList.add('hidden');
    
    const img = document.getElementById('item-image-binary');
    img.src = '/' + item.content;
    
    const question = document.getElementById('binary-question');
    question.textContent = `Is this a ${item.categories[0]}?`;
}

// Display multiclass item
function displayMulticlassItem(item) {
    binaryInterface.classList.add('hidden');
    multiclassInterface.classList.remove('hidden');
    
    const img = document.getElementById('item-image-multi');
    img.src = '/' + item.content;
    
    // Create category buttons
    const categoryButtons = document.getElementById('category-buttons');
    categoryButtons.innerHTML = '';
    
    item.categories.forEach(category => {
        const btn = document.createElement('button');
        btn.className = 'btn-category';
        btn.textContent = category.charAt(0).toUpperCase() + category.slice(1);
        btn.addEventListener('click', () => handleMulticlassLabel(category));
        categoryButtons.appendChild(btn);
    });
}

// Handle binary label
async function handleBinaryLabel(label) {
    await submitLabel(label);
}

// Handle multiclass label
async function handleMulticlassLabel(category) {
    await submitLabel(category);
}

// Submit label
async function submitLabel(label) {
    if (!currentItem) return;
    
    try {
        const response = await fetch('/api/submit_label', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                item_id: currentItem.item_id,
                label: label
            })
        });
        
        if (response.ok) {
            // Update user stats
            await updateUserStatsFromServer();
            // Load next item
            await loadNextItem();
        } else {
            alert('Failed to submit label');
        }
    } catch (error) {
        console.error('Error submitting label:', error);
        alert('Failed to submit label');
    }
}

// Update user stats from server
async function updateUserStatsFromServer() {
    try {
        const response = await fetch('/api/user/stats');
        const stats = await response.json();
        currentUser = stats;
        updateUserStats();
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// Show no items message
function showNoItems() {
    itemContainer.classList.add('hidden');
    noItems.classList.remove('hidden');
}

// Initialize app
init();
