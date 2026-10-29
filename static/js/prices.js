document.addEventListener("DOMContentLoaded", function () {
    const pathParts = window.location.pathname.split("/");
    const itemSlug = pathParts[pathParts.length - 2];
    fetch(`/catalog/product-data/${itemSlug}`) // Подставь реальный эндпоинт
        .then(response => response.json())
        .then(data => {
            loadSizes(data.sizes);
            loadBoards(data.boards);
            loadAddons(data.addons);
        });

    function loadSizes(sizes) {
        const container = document.querySelector(".price-options");
        container.innerHTML = "";
        sizes.forEach(size => {
            container.innerHTML += `
                        <input type="radio" id="size${size.id}" name="size" value="${size.id}" ${size.default ? 'checked' : ''}>
                        <label for="size${size.id}">${size.name} - ${size.price} р.</label>
                    `;
        });
        document.querySelectorAll("input[name='size']").forEach(input => {
            input.addEventListener("change", updatePrices);
        });
    }

    function loadBoards(boards) {
        const container = document.querySelector(".boards");
        container.innerHTML = "";
        boards.forEach(board => {
            container.innerHTML += `
                        <label><input type="radio" name="board" value="${board.id}"> ${board.name} +${board.price} р.</label><br>
                    `;
        });
    }

    function loadAddons(addons) {
        const container = document.querySelector(".addons");
        container.innerHTML = "";
        addons.forEach(addon => {
            container.innerHTML += `
                        <label><input type="checkbox" name="addon" value="${addon.id}"> ${addon.name} +${addon.price} р.</label><br>
                    `;
        });
    }

    function updatePrices() {
        const selectedSize = document.querySelector("input[name='size']:checked").value;
        fetch(`/catalog/update-prices/?size=${selectedSize}`)
            .then(response => response.json())
            .then(data => {
                loadBoards(data.boards);
                loadAddons(data.addons);
            });
    }
});