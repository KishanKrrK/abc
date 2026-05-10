// JavaScript for Smart Lost & Found System
console.log("Smart Lost & Found System loaded!");
// Array to store our items in memory
let itemsArray = [];

const form = document.getElementById('itemForm');
const itemsContainer = document.getElementById('itemsContainer');

// Listen for form submission
form.addEventListener('submit', function(event) {
    event.preventDefault();

    const name = document.getElementById('itemName').value;
    const description = document.getElementById('itemDescription').value;
    const status = document.getElementById('itemStatus').value;
    const photoInput = document.getElementById('itemPhoto');
    
    // Handle the photo upload for display
    let photoUrl = '';
    if (photoInput.files && photoInput.files[0]) {
        // Create a temporary URL to display the uploaded image in the browser
        photoUrl = URL.createObjectURL(photoInput.files[0]);
    }

    // Create item object
    const newItem = {
        id: Date.now(), // unique ID based on timestamp
        name: name,
        description: description,
        status: status,
        photoUrl: photoUrl
    };

    // Add to array and re-render
    itemsArray.push(newItem);
    renderItems();
    
    // Reset the form
    form.reset();
});

// Function to update item status (Found <-> Not Found)
function toggleStatus(id) {
    // Find the item
    const itemIndex = itemsArray.findIndex(item => item.id === id);
    if (itemIndex > -1) {
        // Swap status
        itemsArray[itemIndex].status = itemsArray[itemIndex].status === 'Lost' ? 'Found' : 'Lost';
        renderItems();
    }
}
// Function to render all items to the DOM
function renderItems() {
    // Clear current container
    itemsContainer.innerHTML = '';

    itemsArray.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card';

        // Determine badge class
        const badgeClass = item.status === 'Lost' ? 'status-lost' : 'status-found';
        
        // Use uploaded image, or a placeholder if none was provided
        const imageSource = item.photoUrl ? item.photoUrl : 'https://via.placeholder.com/250x200?text=No+Image';

        card.innerHTML = `
            <img src="${imageSource}" alt="${item.name}">
            <div class="card-content">
                <span class="status-badge ${badgeClass}">${item.status}</span>
                <h3>${item.name}</h3>
                <p>${item.description}</p>
                <button class="toggle-btn" onclick="toggleStatus(${item.id})">
                    Change Status
                </button>
            </div>
        `;

        itemsContainer.appendChild(card);
    });
}