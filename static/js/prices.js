$(document).ready(function () {
    let prices = {};

    function loadPrices() {
        $.ajax({
            url: '/catalog/get-prices/',
            method: 'GET',
            success: function (data) {
                prices = data;
                updateOptions();
                calculateTotal();
            },
            error: function () {
                alert('Не удалось загрузить цены. Пожалуйста, попробуйте позже.');
            }
        });
    }

    function updateOptions() {
        $('#size').empty();
        for (const size in prices.sizes) {
            $('#size').append(`<option value="${size}">${size} (${prices.sizes[size].toFixed(2)} руб.)</option>`);
        }

        updateCrustsAndAddons();
    }

    function updateCrustsAndAddons() {
        const selectedSize = $('#size').val();

        $('#crust').empty();
        if (prices.crusts && prices.crusts[selectedSize]) {
            for (const [crust, price] of Object.entries(prices.crusts[selectedSize])) {
                $('#crust').append(`<option value="${crust}">${crust} (${price.toFixed(2)} руб.)</option>`);
            }
        }

        $('.toppings').empty();
        if (prices.addons && prices.addons[selectedSize]) {
            for (const [addon, price] of Object.entries(prices.addons[selectedSize])) {
                $('.toppings').append(`
                    <label>
                        <input type="checkbox" name="topping" value="${addon}"> ${addon} (${price.toFixed(2)} руб.)
                    </label>
                `);
            }
        }
    }

    function calculateTotal() {
        let total = 0;

        const size = $('#size').val();
        total += prices.sizes[size] || 0;

        const crust = $('#crust').val();
        total += prices.crusts[size]?.[crust] || 0;

        $('input[name="topping"]:checked').each(function () {
            const topping = $(this).val();
            total += prices.addons[size]?.[topping] || 0;
        });

        console.log(`Calculating total: ${total.toFixed(2)} руб.`);  // Отладочный вывод
        $('#total-price').text(total.toFixed(2) + ' руб.');
    }

    $('#size').change(function () {
        updateCrustsAndAddons();
        calculateTotal();
    });
    $('#crust').change(calculateTotal);
    $('.toppings').on('change', 'input[name="topping"]', calculateTotal);

    loadPrices();
});
