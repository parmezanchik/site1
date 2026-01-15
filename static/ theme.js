const toggle = document.getElementById("theme-toggle");

function setTheme(dark) {
    document.body.classList.toggle("dark", dark);
    toggle.textContent = dark ? "☀️" : "🌙";
    localStorage.setItem("theme", dark ? "dark" : "light");
}

const savedTheme = localStorage.getItem("theme");
setTheme(savedTheme === "dark");

toggle.addEventListener("click", () => {
    setTheme(!document.body.classList.contains("dark"));
});
