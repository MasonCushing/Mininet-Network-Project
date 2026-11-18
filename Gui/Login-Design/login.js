async function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const message = document.getElementById("message");

    try {
        const response = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        const result = await response.json();

        if (response.ok && result.authenticated) {
            message.style.color = "green";
            message.textContent = "Password Correct.";
            window.location.href = result.redirect;
            return;
        }

        message.style.color = "red";
        message.textContent = result.message || "Invalid username or password.";
    } catch (error) {
        message.style.color = "red";
        message.textContent = "Unable to log in. Please try again.";
    }
}