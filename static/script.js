function applyTheme(theme) {
    document.getElementById('webPage').setAttribute('data-bs-theme', theme);
}

function autoTheme() {
    const checkSystemTheme = window.matchMedia("(prefers-color-scheme: dark)");
    if (checkSystemTheme.matches) {
        applyTheme("dark");
    } else {
        applyTheme("light");
    }
}

const savedTheme = localStorage.getItem("theme");
if ( localStorage.getItem("theme") === null) {
    autoTheme();
} else {
    applyTheme(savedTheme);
}

document.addEventListener("DOMContentLoaded", () => {
    for (const optionElement of document.querySelectorAll("#SelectTheme option")) {
        optionElement.selected = savedTheme === optionElement.value;
    }

    document.querySelector("#SelectTheme").addEventListener("change", function () {
        if (this.value == "auto") {
            localStorage.removeItem("theme");
            autoTheme();
        } else {
            localStorage.setItem("theme", this.value);
            applyTheme(this.value);
        }
    })
});

