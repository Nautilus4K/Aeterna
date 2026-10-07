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

// Prepare the modes
document.addEventListener("DOMContentLoaded", () => {
    if (getCookie("mode") == "") {
        const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (isDarkMode) {
            setCookie("mode", "dark", 14);
        }
        else setCookie("mode", "light", 14)
    }

    if (getCookie("mode") == "dark") {
        document.documentElement.classList.add("dark");
        document.getElementById("mode-indicator").textContent = "dark_mode";
    }
});

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