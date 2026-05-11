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
        item.description.toLowerCase().includes(keyword),
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

// SHOW ITEMS ON LOAD
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

// SIGNUP MODAL
const openSignup = document.getElementById("openSignup");
const signupModal = document.getElementById("signupModal");
const closeSignup = document.getElementById("closeSignup");

const signupForm = document.getElementById("signupForm");
const goToLogin = document.getElementById("goToLogin");

// OPEN LOGIN
if (openBtn) {
  openBtn.addEventListener("click", () => {
    modal.style.display = "flex";
  });
}

// CLOSE LOGIN
if (closeBtn) {
  closeBtn.addEventListener("click", () => {
    modal.style.display = "none";
  });
}

// OPEN SIGNUP
if (openSignup) {
  openSignup.addEventListener("click", (e) => {
    e.preventDefault();

    signupModal.style.display = "flex";
  });
}

// CLOSE SIGNUP
if (closeSignup) {
  closeSignup.addEventListener("click", () => {
    signupModal.style.display = "none";
  });
}

// SWITCH SIGNUP → LOGIN
if (goToLogin) {
  goToLogin.addEventListener("click", (e) => {
    e.preventDefault();

    signupModal.style.display = "none";

    modal.style.display = "flex";
  });
}

// REGISTER LINK LOGIN → SIGNUP
const registerLink = document.querySelector(".registerText a");

if (registerLink) {
  registerLink.addEventListener("click", (e) => {
    e.preventDefault();

    modal.style.display = "none";

    signupModal.style.display = "flex";
  });
}

// CLOSE OUTSIDE
window.addEventListener("click", (e) => {
  if (e.target === modal) {
    modal.style.display = "none";
  }

  if (e.target === signupModal) {
    signupModal.style.display = "none";
  }
});

// ESC KEY CLOSE
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    modal.style.display = "none";

    signupModal.style.display = "none";
  }
});

// SIGNUP FORM
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
