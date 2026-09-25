// ==========================================
// login.js — AgriChain Login Handler
// เชื่อมต่อ DynamoDB ผ่าน /api/login (server.js)
// ==========================================

// ── i18n translations ──────────────────────
const LOGIN_T = {
    th: {
        brandTitle: "ขับเคลื่อนข้อมูลอัจฉริยะใน<br>ห่วงโซ่อุปทานการเกษตร",
        brandDesc:  "จัดการโลจิสติกส์ ติดตามสินค้าคงคลัง และยกระดับการดำเนินงานด้านการเกษตรด้วยข้อมูลอย่างแม่นยำ",
        welcome:    "ยินดีต้อนรับเข้าสู่ระบบ",
        subtitle:   "กรุณากรอกข้อมูลเพื่อเข้าสู่ระบบ",
        email:      "ชื่อผู้ใช้",
        password:   "รหัสผ่าน",
        forgot:     "ลืมรหัสผ่าน?",
        remember:   "จดจำการเข้าสู่ระบบ",
        login:      "เข้าสู่ระบบ →",
        noAccount:  "ยังไม่มีบัญชีใช่ไหม?",
        register:   "สร้างบัญชีใหม่",
        show:       "แสดงรหัสผ่าน",
        hide:       "ซ่อนรหัสผ่าน",
        success:    "เข้าสู่ระบบสำเร็จ! กำลังนำท่านเข้าสู่หน้าหลัก...",
        invalid:    "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง!",
        error:      "ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้ กรุณาลองใหม่อีกครั้ง",
        loading:    "กำลังตรวจสอบ..."
    },
    en: {
        brandTitle: "Cultivating Intelligence in<br>Global Supply Chains",
        brandDesc:  "Securely manage logistics, track inventory, and optimize agricultural operations with precision data.",
        welcome:    "Welcome to AgriChain",
        subtitle:   "Please enter your details to sign in",
        email:      "Username",
        password:   "Password",
        forgot:     "Forgot password?",
        remember:   "Remember me",
        login:      "Sign in →",
        noAccount:  "Don't have an account?",
        register:   "Create account",
        show:       "Show password",
        hide:       "Hide password",
        success:    "Signed in successfully! Redirecting...",
        invalid:    "Incorrect username or password.",
        error:      "Unable to connect to server. Please try again.",
        loading:    "Signing in..."
    }
};

// ── Language Switcher ──────────────────────
let lang = localStorage.getItem("language") || "th";

function applyLang(l) {
    lang = l;
    localStorage.setItem("language", l);
    document.documentElement.lang = l;
    // อัปเดตข้อความทุก element ที่มี data-i18n
    // ยกเว้น submit button เพราะจะ handle แยก
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.dataset.i18n;
        if (LOGIN_T[l][key] !== undefined) {
            el.innerHTML = LOGIN_T[l][key];
        }
    });
    document.getElementById("thBtn").classList.toggle("active", l === "th");
    document.getElementById("enBtn").classList.toggle("active", l === "en");

    // อัปเดต aria-label ปุ่ม toggle password
    const toggleBtn = document.getElementById("togglePassword");
    if (toggleBtn) {
        const pwInput = document.getElementById("password");
        toggleBtn.setAttribute("aria-label",
            pwInput && pwInput.type === "password" ? LOGIN_T[l].show : LOGIN_T[l].hide
        );
    }
}

document.getElementById("thBtn").addEventListener("click", () => applyLang("th"));
document.getElementById("enBtn").addEventListener("click", () => applyLang("en"));

// ── DOM Elements ───────────────────────────
const loginForm     = document.getElementById("loginForm");
const passwordInput = document.getElementById("password");
const togglePassword = document.getElementById("togglePassword");
const loginMessage  = document.getElementById("loginMessage");
const submitBtn     = loginForm.querySelector("button[type=submit]");

// ── Toggle Password Visibility ─────────────
togglePassword.addEventListener("click", () => {
    const hidden = passwordInput.type === "password";
    passwordInput.type = hidden ? "text" : "password";
    togglePassword.querySelector(".eye-off").style.display = hidden ? "none"  : "block";
    togglePassword.querySelector(".eye-on").style.display  = hidden ? "block" : "none";
    togglePassword.setAttribute("aria-label", hidden ? LOGIN_T[lang].hide : LOGIN_T[lang].show);
});

// ── Clear password on page load / back-nav ─
passwordInput.value = "";
window.addEventListener("pageshow", () => { passwordInput.value = ""; });

// ── Login Form Submit ──────────────────────
loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    loginMessage.textContent = "";

    const usernameInput = document.getElementById("email").value.trim();
    const password      = passwordInput.value;

    if (!usernameInput || !password) {
        loginMessage.style.color = "#d93025";
        loginMessage.textContent = lang === "th"
            ? "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน"
            : "Please enter username and password.";
        return;
    }

    // แสดง loading state
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = LOGIN_T[lang].loading;

    try {
        // ── ยิง API ไปที่ server.js → DynamoDB ──
        const response = await fetch("/api/login", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ username: usernameInput, password: password })
        });

        const data = await response.json();

        if (data.success) {
            // บันทึก user info ลง localStorage
            localStorage.setItem("currentUser", JSON.stringify(data.user));

            loginMessage.style.color   = "#2d5028";
            loginMessage.textContent   = LOGIN_T[lang].success;

            // Redirect ไปหน้า dashboard หลังจาก 900ms
            setTimeout(() => { location.href = "dashboard.html"; }, 900);

        } else {
            // กรณี login ไม่สำเร็จ
            submitBtn.disabled    = false;
            submitBtn.textContent = originalText;

            loginMessage.style.color   = "#d93025";
            loginMessage.textContent   = data.message || LOGIN_T[lang].invalid;
        }

    } catch (err) {
        console.error("Login fetch error:", err);
        submitBtn.disabled    = false;
        submitBtn.textContent = originalText;

        loginMessage.style.color   = "#d93025";
        loginMessage.textContent   = LOGIN_T[lang].error;
    }
});

// ── Apply language on first load ───────────
applyLang(lang);
