function setTheme(theme) {
    var body = document.getElementById("body");
    var savedTheme = localStorage.getItem("theme");
    theme = theme || savedTheme;
    body.dataset.theme = theme;
    localStorage.setItem("theme", theme);
}

function toggleTheme() {
    var theme = localStorage.getItem("theme");
    setTheme((theme == "dark") ? "light" : "dark");
}

function showPopup(el) {
    var pos = el.getBoundingClientRect();
    var popup = document.getElementById("popup");

    popup.innerHTML = el.dataset.post;
    popup.style.display = "block";
    popup.style.left = pos.left + "px";
    popup.style.top = window.pageYOffset + pos.bottom + "px";
}

function hidePopup(el) {
    document.getElementById("popup").style.display = "none";
}
