const options = [
    "H1","H2","H3","H4","H5",
    "H6","H7","H8","H9","H10",
    "H11","H12","H13","H14","H15",
    "H16","H17","H18","H19","H20",
    "H21","H22","H23","H24","H25",
    "H26","H27","H28","H29","H30",
    "H31","H32","H33","H34","H35",
    "H36","H37","H38","H39","H40",
    "H41","H42","H43","H44","H45",
    "H46","H47","H48","H49","H50",
    "H51",
];

document.querySelectorAll(".dropdown-menu").forEach(menu => {
    const searchInput = menu.querySelector("input");
    const dropdown = menu.querySelector(".dropdown-list");

    function displayOptions(filteredOptions) {
        dropdown.innerHTML = "";

        if (filteredOptions.length === 0) {
            const emptyMessage = document.createElement("div");
            emptyMessage.className = "dropdown-empty";
            emptyMessage.textContent = "No matching hosts";
            dropdown.appendChild(emptyMessage);
            return;
        }

        filteredOptions.forEach(option => {
            const item = document.createElement("button");
            item.type = "button";
            item.textContent = option;
            item.addEventListener("click", () => {
                searchInput.value = option;
                dropdown.style.display = "none";
            });
            dropdown.appendChild(item);
        });
    }

    function filterOptions() {
        const search = searchInput.value.toLowerCase();
        const filteredOptions = options.filter(option =>
            option.toLowerCase().includes(search)
        );

        displayOptions(filteredOptions);
        dropdown.style.display = "block";
    }

    searchInput.addEventListener("focus", filterOptions);
    searchInput.addEventListener("input", filterOptions);
});

document.addEventListener("click", function(event) {
    if (!event.target.closest(".dropdown-menu")) {
        document.querySelectorAll(".dropdown-list").forEach(dropdown => {
            dropdown.style.display = "none";
        });
    }
});