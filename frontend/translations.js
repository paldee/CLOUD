/**
 * AgriChain i18n Translation Engine & Unified Dictionary
 * Powered by i18next library with local fallback guarantee.
 */

(function () {
    const resources = {
        th: {
            translation: {
                // Header & Brand
                appName: "AgriChain",
                brandSubtitle: "ระบบวิเคราะห์ห่วงโซ่อุปทานการเกษตร",
                brandTitle: "ขับเคลื่อนข้อมูลอัจฉริยะใน<br>ห่วงโซ่อุปทานการเกษตร",
                brandDesc: "จัดการการดำเนินงาน เพิ่มการมองเห็นข้อมูล และยกระดับประสิทธิภาพของเครือข่ายโลจิสติกส์การเกษตรแบบครบวงจร",
                copyright: "© 2026 AgriChain Logistics Systems สงวนลิขสิทธิ์",

                // Navigation / Sidebar
                dashboard: "แดชบอร์ด",
                supply: "คลังข้อมูล",
                ai: "ผู้ช่วย AI",
                warehouse: "คลังสินค้า",
                account: "บัญชี / ออกจากระบบ",
                logoutConfirm: "คุณต้องการออกจากระบบหรือไม่?",

                // Login Page
                indexTitle: "AgriChain - เข้าสู่ระบบ",
                welcome: "ยินดีต้อนรับเข้าสู่ระบบ",
                subtitle: "กรุณากรอกข้อมูลเพื่อเข้าสู่ระบบ",
                email: "ชื่อผู้ใช้",
                password: "รหัสผ่าน",
                usernamePlaceholder: "exec01 / analyst01 / admin01",
                passwordPlaceholder: "กรอกรหัสผ่านของคุณ",
                forgot: "ลืมรหัสผ่าน?",
                remember: "จดจำการเข้าสู่ระบบ",
                login: "เข้าสู่ระบบ →",
                noAccount: "ยังไม่มีบัญชีใช่ไหม?",
                register: "สร้างบัญชีใหม่",
                show: "แสดงรหัสผ่าน",
                hide: "ซ่อนรหัสผ่าน",
                loginSuccess: "เข้าสู่ระบบสำเร็จ! กำลังนำท่านเข้าสู่หน้าหลัก...",
                loginInvalid: "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง!",
                loginError: "ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้ กรุณาลองใหม่อีกครั้ง",
                loginRequired: "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน",
                loading: "กำลังตรวจสอบ...",

                // Data Warehouse / Dashboard Page
                dashboardTitle: "AgriChain - คลังข้อมูล",
                uploadCenter: "คลังข้อมูล",
                uploadDesc: "นำเข้าและประมวลผลชุดข้อมูลห่วงโซ่อุปทานอย่างปลอดภัย",
                drag: "ลากและวางไฟล์ CSV ที่นี่เพื่ออัปโหลดทันที",
                browse: "หรือคลิกพื้นที่นี้เพื่อเลือกไฟล์จากคอมพิวเตอร์ของคุณ",
                onlyCsvAlert: "กรุณาอัปโหลดเฉพาะไฟล์ .csv เท่านั้น",
                recent: "อัปโหลดล่าสุด",
                searchPlaceholder: "ค้นหาชื่อไฟล์...",
                filename: "ชื่อไฟล์",
                size: "ขนาด",
                status: "สถานะ",
                time: "เวลา",
                success: "สำเร็จ",
                progress: "กำลังอัปโหลด...",
                failed: "ล้มเหลว",
                preview: "ดูตัวอย่างข้อมูล",
                delete: "ลบ",
                deleteConfirm: "คุณแน่ใจหรือไม่ว่าต้องการลบไฟล์นี้จาก S3?",
                deleteSuccess: "ลบไฟล์ออกจาก S3 เรียบร้อยแล้ว",
                deleteError: "ไม่สามารถลบไฟล์ได้",
                fetchError: "ไม่สามารถดึงข้อมูลไฟล์ได้",
                noUploads: "ยังไม่มีประวัติการอัปโหลดไฟล์ (ลากและวางไฟล์ CSV ด้านบนเพื่อเริ่มต้น)",

                // CSV Modal Preview
                modalFilePrefix: "📄 ตัวอย่างข้อมูล: ",
                sampleDataPrefix: "📊 ตัวอย่างข้อมูล: แสดง",
                firstRows: "แถวแรก",
                ofTotal: "จากทั้งหมด",
                rows: "แถว",
                columns: "คอลัมน์",
                fileEmpty: "ไฟล์ว่างเปล่า ไม่มีข้อมูล",

                // AI Assistant Page
                agentTitle: "AgriChain - ผู้ช่วย AI",
                aiHeader: "🤖 ผู้ช่วยวิเคราะห์ข้อมูล AI",
                aiDesc: "สอบถามข้อมูลสินค้า ราคา และห่วงโซ่อุปทานด้วยภาษาธรรมชาติ",
                aiGreeting: "สวัสดีครับ! ผมคือ AgriChain AI ผู้ช่วยวิเคราะห์ข้อมูลของคุณ มีอะไรให้ผมช่วยเหลือเกี่ยวกับสินค้าและห่วงโซ่อุปทานวันนี้ไหมครับ?",
                chatPlaceholder: "พิมพ์คำถามของคุณที่นี่...",
                send: "ส่ง",
                processing: "กำลังประมวลผล...",
                successProcess: "ประมวลผลสำเร็จ",
                aiError: "เกิดข้อผิดพลาดในการเชื่อมต่อกับ AI"
            }
        },
        en: {
            translation: {
                // Header & Brand
                appName: "AgriChain",
                brandSubtitle: "Agricultural Supply Chain Analytics",
                brandTitle: "Cultivating Intelligence in<br>Global Supply Chains",
                brandDesc: "Securely manage logistics, track inventory, and optimize agricultural operations with precision data.",
                copyright: "© 2026 AgriChain Logistics Systems. All rights reserved.",

                // Navigation / Sidebar
                dashboard: "Dashboard",
                supply: "Data Center",
                ai: "AI Assistant",
                warehouse: "Warehouse",
                account: "Account / Sign out",
                logoutConfirm: "Are you sure you want to sign out?",

                // Login Page
                indexTitle: "AgriChain - Sign In",
                welcome: "Welcome to AgriChain",
                subtitle: "Please enter your details to sign in",
                email: "Username",
                password: "Password",
                usernamePlaceholder: "exec01 / analyst01 / admin01",
                passwordPlaceholder: "Enter your password",
                forgot: "Forgot password?",
                remember: "Remember me",
                login: "Sign in →",
                noAccount: "Don't have an account?",
                register: "Create account",
                show: "Show password",
                hide: "Hide password",
                loginSuccess: "Signed in successfully! Redirecting...",
                loginInvalid: "Incorrect username or password.",
                loginError: "Unable to connect to server. Please try again.",
                loginRequired: "Please enter username and password.",
                loading: "Signing in...",

                // Data Warehouse / Dashboard Page
                dashboardTitle: "AgriChain - Data Center",
                uploadCenter: "Data Center",
                uploadDesc: "Safely import and process supply chain datasets.",
                drag: "Drag & drop CSV files here to upload instantly",
                browse: "or click this area to browse from your computer",
                onlyCsvAlert: "Please upload .csv files only.",
                recent: "Recent Uploads",
                searchPlaceholder: "Search files...",
                filename: "File name",
                size: "Size",
                status: "Status",
                time: "Time",
                success: "Completed",
                progress: "Uploading...",
                failed: "Failed",
                preview: "Preview data",
                delete: "Delete",
                deleteConfirm: "Are you sure you want to delete this file from S3?",
                deleteSuccess: "File deleted successfully from S3.",
                deleteError: "Unable to delete file.",
                fetchError: "Unable to load file content.",
                noUploads: "No upload history yet (drag and drop CSV files above to start)",

                // CSV Modal Preview
                modalFilePrefix: "📄 File Preview: ",
                sampleDataPrefix: "📊 Sample Data: Showing",
                firstRows: "first rows",
                ofTotal: "of",
                rows: "rows",
                columns: "columns",
                fileEmpty: "File is empty. No records found.",

                // AI Assistant Page
                agentTitle: "AgriChain - AI Assistant",
                aiHeader: "🤖 AgriChain AI Assistant",
                aiDesc: "Query product data, prices, and supply chain insights in natural language",
                aiGreeting: "Hello! I am AgriChain AI, your intelligent data assistant. How can I help you analyze supply chain, pricing, or product records today?",
                chatPlaceholder: "Type your question here...",
                send: "Send",
                processing: "Thinking & analyzing...",
                successProcess: "Completed successfully",
                aiError: "Error connecting to AI service."
            }
        }
    };

    // Current language from storage or default to Thai
    let currentLang = localStorage.getItem("language") || "th";

    // Initialize i18next if loaded
    if (window.i18next) {
        window.i18next.init({
            lng: currentLang,
            fallbackLng: "th",
            debug: false,
            resources: resources
        });
    }

    /**
     * Translation lookup function
     * @param {string} key - translation key
     * @param {object} [params] - optional interpolation params
     * @returns {string}
     */
    function t(key, params) {
        if (window.i18next && typeof window.i18next.t === "function" && window.i18next.isInitialized) {
            const val = window.i18next.t(key, params);
            if (val && val !== key) return val;
        }

        const lang = localStorage.getItem("language") || currentLang || "th";
        const dict = resources[lang]?.translation || resources.th.translation;
        let str = dict[key] !== undefined ? dict[key] : (resources.th.translation[key] || key);

        if (params && typeof params === "object") {
            Object.keys(params).forEach(pKey => {
                str = str.replace(new RegExp(`{{${pKey}}}`, "g"), params[pKey]);
            });
        }
        return str;
    }

    /**
     * Change application language and update all DOM elements
     * @param {string} lang - 'th' or 'en'
     */
    function setAppLanguage(lang) {
        currentLang = lang;
        localStorage.setItem("language", lang);
        document.documentElement.lang = lang;

        if (window.i18next && typeof window.i18next.changeLanguage === "function") {
            window.i18next.changeLanguage(lang);
        }

        // 1. Text elements with data-i18n
        document.querySelectorAll("[data-i18n]").forEach(el => {
            const key = el.dataset.i18n;
            const text = t(key);
            if (text !== undefined) {
                // If it contains HTML like <br>, use innerHTML
                if (text.includes("<") && text.includes(">")) {
                    el.innerHTML = text;
                } else {
                    el.textContent = text;
                }
            }
        });

        // 2. HTML elements specifically marked with data-i18n-html
        document.querySelectorAll("[data-i18n-html]").forEach(el => {
            const key = el.dataset.i18nHtml;
            el.innerHTML = t(key);
        });

        // 3. Placeholders
        document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
            const key = el.dataset.i18nPlaceholder;
            el.placeholder = t(key);
        });

        // 4. Titles / Tooltips
        document.querySelectorAll("[data-i18n-title]").forEach(el => {
            const key = el.dataset.i18nTitle;
            el.title = t(key);
        });

        // 5. Aria-labels
        document.querySelectorAll("[data-i18n-aria]").forEach(el => {
            const key = el.dataset.i18nAria;
            el.setAttribute("aria-label", t(key));
        });

        // 6. Switch buttons active state
        const thBtn = document.getElementById("thBtn");
        const enBtn = document.getElementById("enBtn");
        if (thBtn) thBtn.classList.toggle("active", lang === "th");
        if (enBtn) enBtn.classList.toggle("active", lang === "en");

        // 7. Page title if marked with data-i18n
        const titleEl = document.querySelector("title[data-i18n]");
        if (titleEl) {
            document.title = t(titleEl.dataset.i18n);
        }

        // 8. Fire event so page-specific JS can react
        window.dispatchEvent(new CustomEvent("appLanguageChanged", { detail: { lang: lang, t: t } }));
    }

    // Attach to window
    window.t = t;
    window.setAppLanguage = setAppLanguage;
    window.I18N_RESOURCES = resources;

    // Run automatically when DOM is ready
    function autoInit() {
        // Bind click events on standard switch buttons if present
        const thBtn = document.getElementById("thBtn");
        const enBtn = document.getElementById("enBtn");

        if (thBtn) {
            thBtn.onclick = (e) => {
                e.preventDefault();
                setAppLanguage("th");
            };
        }
        if (enBtn) {
            enBtn.onclick = (e) => {
                e.preventDefault();
                setAppLanguage("en");
            };
        }

        // Apply current language
        setAppLanguage(currentLang);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", autoInit);
    } else {
        autoInit();
    }
})();
