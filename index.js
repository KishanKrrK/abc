let lostItems = JSON.parse(localStorage.getItem("lostItems")) || [];
let foundItems = JSON.parse(localStorage.getItem("foundItems")) || [];

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

const openBtn = document.getElementById("openLogin");
const modal = document.getElementById("loginModal");
const closeBtn = document.getElementById("closeLogin");

const openSignup = document.getElementById("openSignup");
const signupModal = document.getElementById("signupModal");
const closeSignup = document.getElementById("closeSignup");
const signupForm = document.getElementById("signupForm");
const goToLogin = document.getElementById("goToLogin");

const reportModal = document.getElementById("reportModal");
const openReport = document.getElementById("openReport");
const closeReport = document.getElementById("closeReport");

if (openBtn) {
openBtn.addEventListener("click", () => {
modal.style.display = "flex";
document.body.style.overflow = "hidden";
});
}

if (closeBtn) {
closeBtn.addEventListener("click", () => {
modal.style.display = "none";
document.body.style.overflow = "auto";
});
}

if (openSignup) {
openSignup.addEventListener("click", (e) => {
e.preventDefault();
signupModal.style.display = "flex";
document.body.style.overflow = "hidden";
});
}

if (closeSignup) {
closeSignup.addEventListener("click", () => {
signupModal.style.display = "none";
document.body.style.overflow = "auto";
});
}

if (goToLogin) {
goToLogin.addEventListener("click", (e) => {
e.preventDefault();
signupModal.style.display = "none";
modal.style.display = "flex";
});
}

const registerLink = document.querySelector(".registerText a");

if (registerLink) {
registerLink.addEventListener("click", (e) => {
e.preventDefault();
modal.style.display = "none";
signupModal.style.display = "flex";
});
}

if (signupForm) {
signupForm.addEventListener("submit", function (e) {
e.preventDefault();

const username = document.getElementById("signupUsername").value;
const email = document.getElementById("signupEmail").value;
const password = document.getElementById("signupPassword").value;

let users = JSON.parse(localStorage.getItem("users")) || [];

const userExists = users.some((user) => user.username === username);

if (userExists) {
alert("Username already exists!");
return;
}

users.push({
username,
email,
password,
});

localStorage.setItem("users", JSON.stringify(users));

alert("Signup successful!");

signupForm.reset();

signupModal.style.display = "none";

modal.style.display = "flex";
});
}

if (openReport) {
openReport.addEventListener("click", () => {
reportModal.style.display = "flex";
document.body.style.overflow = "hidden";
});
}

if (closeReport) {
closeReport.addEventListener("click", () => {
reportModal.style.display = "none";
document.body.style.overflow = "auto";
});
}

window.addEventListener("click", (e) => {
if (e.target === modal) {
modal.style.display = "none";
document.body.style.overflow = "auto";
}

if (e.target === signupModal) {
signupModal.style.display = "none";
document.body.style.overflow = "auto";
}

if (e.target === reportModal) {
reportModal.style.display = "none";
document.body.style.overflow = "auto";
}
});

document.addEventListener("keydown", (e) => {
if (e.key === "Escape") {
modal.style.display = "none";
signupModal.style.display = "none";
reportModal.style.display = "none";
document.body.style.overflow = "auto";
}
});