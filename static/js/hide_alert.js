document.addEventListener('DOMContentLoaded', function () {
    // Находим блоки уведомления
    let notifications = document.querySelectorAll('.notification');

    // Закрыть каждое уведомление через 5 секунд
    notifications.forEach(function (notification) {
        setTimeout(function () {
            notification.style.display = 'none';
        }, 5000); // Устанавливаем время в 5000 миллисекунд (5 секунд)

        // Находим кнопку закрытия внутри каждого уведомления
        let closeBtn = notification.querySelector('.alert-close-btn');
        if (closeBtn) {
            // Закрытие конкретного уведомления при клике на крестик
            closeBtn.addEventListener('click', function () {
                notification.style.display = 'none';
            });
        }
    });
});
