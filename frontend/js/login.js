const username_input = document.getElementById("username_field");
const password_input = document.getElementById("password_field");

async function login() {
    const username = username_input.value;
    const password = password_input.value;

    const response = await fetch('/loginauth', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: username, password: password }),
        credentials: 'include' // save creds
    });

    if (!response.ok) {
        const data = await response.text();
        document.getElementById("alert").textContent = data;
    } else window.location.href = "/";
}

username_input.addEventListener("keydown", (e) => {
    if (e.key == "Enter") password_input.focus();
});

password_input.addEventListener("keydown", (e) => {
    if (e.key == "Enter") login();
})