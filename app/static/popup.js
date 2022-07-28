function show_popup(el) {
    var pos = el.getBoundingClientRect();
    var popup = document.getElementById("popup");

    popup.innerHTML = el.dataset.post;
    popup.style.display = "block";
    popup.style.left = pos.left + "px";
    popup.style.top = window.pageYOffset + pos.bottom + "px";
}

function hide_popup(el) {
    document.getElementById("popup").style.display = "none";
}