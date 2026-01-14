const body = document.body;
const toggle = document.getElementById("theme-toggle");

if (toggle) {

    if (localStorage.getItem("theme") === "dark") {
        body.classList.add("dark");
        toggle.textContent = "☀️";
    }

    toggle.onclick = () => {
        body.classList.toggle("dark");

        if (body.classList.contains("dark")) {
            localStorage.setItem("theme", "dark");
            toggle.textContent = "☀️";
        } else {
            localStorage.setItem("theme", "light");
            toggle.textContent = "🌙";
        }
    };
}
uvicorn main:app --reload

