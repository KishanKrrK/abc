let lostItems = JSON.parse(localStorage.getItem("lostItems")) || [];
let foundItems = JSON.parse(localStorage.getItem("foundItems")) || [];

// REPORT FORM
const reportForm = document.querySelector("#report form");

if (reportForm) {
  reportForm.addEventListener("submit", function (e) {
    e.preventDefault();

    let item = {
      name: this.item_name.value,
      description: this.description.value,
      date: this.date_lost.value,
      location: this.location.value,
    };

    lostItems.push(item);

    localStorage.setItem("lostItems", JSON.stringify(lostItems));

    alert("Lost item reported successfully!");

    this.reset();
  });
}

// FOUND FORM
const foundForm = document.querySelector("#found form");

if (foundForm) {
  foundForm.addEventListener("submit", function (e) {
    e.preventDefault();

    let item = {
      name: this.item_name.value,
      description: this.description.value,
      date: this.date_found.value,
      location: this.location.value,
    };

    foundItems.push(item);

    localStorage.setItem("foundItems", JSON.stringify(foundItems));

    alert("Found item reported successfully!");

    this.reset();
  });
}

// SEARCH FORM
const searchForm = document.querySelector("#search form");

if (searchForm) {
  searchForm.addEventListener("submit", function (e) {
    e.preventDefault();

    let keyword = this.querySelector("input").value.toLowerCase();

    let resultsList = document.querySelector("#search ul");

    resultsList.innerHTML = "";

    let results = [...lostItems, ...foundItems];

    let filtered = results.filter(
      (item) =>
        item.name.toLowerCase().includes(keyword) ||
        item.description.toLowerCase().includes(keyword)
    );

    if (filtered.length === 0) {
      resultsList.innerHTML = "<li>No items found</li>";
      return;
    }

    filtered.forEach((item) => {
      let li = document.createElement("li");

      li.textContent = `${item.name} - ${item.location}`;

      resultsList.appendChild(li);
    });
  });
}

// SHOW ALL ITEMS ON PAGE LOAD
document.addEventListener("DOMContentLoaded", () => {
  let resultsList = document.querySelector("#search ul");

  if (!resultsList) return;

  resultsList.innerHTML = "";

  let allItems = [...lostItems, ...foundItems];

  allItems.forEach((item) => {
    let li = document.createElement("li");

    li.textContent = `${item.name} - ${item.location}`;

    resultsList.appendChild(li);
  });
});

// LOGIN MODAL
const openBtn = document.getElementById("openLogin");

const modal = document.getElementById("loginModal");

const closeBtn = document.getElementById("closeLogin");

// OPEN MODAL
if (openBtn) {
  openBtn.addEventListener("click", () => {
    modal.style.display = "flex";
  });
}

// CLOSE MODAL
if (closeBtn) {
  closeBtn.addEventListener("click", () => {
    modal.style.display = "none";
  });
}

// CLOSE ON OUTSIDE CLICK
window.addEventListener("click", (e) => {
  if (e.target === modal) {
    modal.style.display = "none";
  }
});

// CLOSE ON ESC KEY
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    modal.style.display = "none";
  }
});