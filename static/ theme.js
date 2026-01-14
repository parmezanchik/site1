const body = document.body;
const toggle = document.getElementById("theme-toggle");

// якщо кнопки немає — нічого не робимо
if (toggle) {

    // при завантаженні сторінки
    if (localStorage.getItem("theme") === "dark") {
        body.classList.add("dark");
        toggle.textContent = "☀️";
    }

    // перемикання теми
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
