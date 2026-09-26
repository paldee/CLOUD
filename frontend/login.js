// ==========================================
// login.js — AgriChain Login Handler
// Powered by i18n & DynamoDB
// ==========================================

const loginForm = document.getElementById("loginForm");
const passwordInput = document.getElementById("password");
const togglePassword = document.getElementById("togglePassword");
const loginMessage = document.getElementById("loginMessage");
const submitBtn = loginForm.querySelector("button[type=submit]");

function updatePasswordToggleAria() {
    if (togglePassword && passwordInput) {
        const hidden = passwordInput.type === "password";
        togglePassword.setAttribute("aria-label", hidden ? window.t("show") : window.t("hide"));
    }
}

window.addEventListener("appLanguageChanged", () => {
    updatePasswordToggleAria();
});

// Toggle Password Visibility
togglePassword.addEventListener("click", () => {
    const hidden = passwordInput.type === "password";
    passwordInput.type = hidden ? "text" : "password";
    togglePassword.querySelector(".eye-off").style.display = hidden ? "none" : "block";
    togglePassword.querySelector(".eye-on").style.display = hidden ? "block" : "none";
    updatePasswordToggleAria();
});

// Clear password on page load / back-nav
passwordInput.value = "";
window.addEventListener("pageshow", () => { passwordInput.value = ""; });

// Login Form Submit
loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    loginMessage.textContent = "";

    const usernameInput = document.getElementById("email").value.trim();
    const password = passwordInput.value;

    if (!usernameInput || !password) {
        loginMessage.style.color = "#d93025";
        loginMessage.textContent = window.t("loginRequired");
        return;
    }

    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = window.t("loading");

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: usernameInput, password: password })
        });

        const data = await response.json();

        if (data.success) {
            localStorage.setItem("currentUser", JSON.stringify(data.user));
            loginMessage.style.color = "#2d5028";
            loginMessage.textContent = window.t("loginSuccess");
            setTimeout(() => { location.href = "dashboard.html"; }, 900);
        } else {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            loginMessage.style.color = "#d93025";
            loginMessage.textContent = data.message || window.t("loginInvalid");
        }
    } catch (err) {
        console.error("Login fetch error:", err);
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
        loginMessage.style.color = "#d93025";
        loginMessage.textContent = window.t("loginError");
    }
});

updatePasswordToggleAria();
