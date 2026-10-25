function setCookie(cname, cvalue, exdays) {
    const d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    let expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}
function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for(let i = 0; i <ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

function switch_mode() {
    if (getCookie("mode") == "dark") {
        setCookie("mode", "light", 14);
        document.documentElement.classList.remove("dark");
        document.getElementById("mode-indicator").textContent = "light_mode";
    }

    else {
        // (getCookie("mode") == "light") 
        setCookie("mode", "dark", 14);
        document.documentElement.classList.add("dark");
        document.getElementById("mode-indicator").textContent = "dark_mode";
    }
}

if (getCookie("locale") == "") setCookie("locale", "en", 365 * 24 * 60 * 60);

function switch_lang() {
    if (getCookie("locale") == "en") {
        setCookie("locale", "vi", 365 * 24 * 60 * 60);
        window.location.href = window.location.href;
    } else {
        setCookie("locale", "en", 365 * 24 * 60 * 60);
        window.location.href = window.location.href;
    }
}

function toggle_menu() {
    document.getElementById("mobile_menu").classList.add("open");   
}

function user_menu() {
    if (document.getElementById('usermenu_btn').dataset.mode == "login") window.location.href = "/login";
    else {
        // console.log("USER MENU");
        const usermenu = document.getElementById("usermenu");
        usermenu.classList.toggle("hidden");
    }
}

if (getCookie("mode") == "") {
    const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (isDarkMode) {
        setCookie("mode", "dark", 14);
    }
    else setCookie("mode", "light", 14)
}

if (getCookie("mode") == "dark") {
    document.documentElement.classList.add("dark");
}

// Prepare the modes
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("lang_toggler").textContent = getCookie("locale").toUpperCase();

    if (getCookie("mode") == "dark") document.getElementById("mode-indicator").textContent = "dark_mode";
});

document.addEventListener("mousedown", (e) => {
    if (!document.getElementById("mobile_menu").contains(e.target)) {
        document.getElementById("mobile_menu").classList.remove("open");
    }

    if (!document.getElementById("usermenu").classList.contains("hidden") && !document.getElementById("usermenu").contains(e.target) && !document.getElementById("usermenu_btn").contains(e.target)) {
        document.getElementById("usermenu").classList.add("hidden");
    }
});