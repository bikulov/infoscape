document.documentElement.dataset.theme = localStorage.getItem("theme");

function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
}

function toggleTheme() {
    var theme = localStorage.getItem("theme");
    setTheme((theme == "dark") ? "light" : "dark");
}

function toggleDetails(el) {
    var details = document.getElementById(el.dataset.id);

    if (details.style.display == "block") {
        el.classList.remove("post-unfolded")
        details.style.display = "none";
    } else {
        el.classList.add("post-unfolded");
        details.style.display = "block";
    }
}
