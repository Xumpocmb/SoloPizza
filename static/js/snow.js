document.addEventListener('DOMContentLoaded', function () {
    const numSnowflakes = 75;
    for (let i = 0; i < numSnowflakes; i++) {
        createSnowflake();
    }

    function createSnowflake() {
        try {
            const snowflake = document.createElement('div');
            snowflake.classList.add('snowflake');

            // Случайный выбор символа снежинки (только настоящие символы снежинок)
            const snowflakeSymbols = ['&#10052;', '&#10053;', '&#10054;'];
            const randomSymbol = snowflakeSymbols[Math.floor(Math.random() * snowflakeSymbols.length)];
            snowflake.innerHTML = randomSymbol;

            // Установка случайной позиции по горизонтали
            snowflake.style.left = Math.random() * 100 + 'vw';

            // Установка случайного сноса (дрейфа) влево или вправо
            const drift = (Math.random() - 0.5) * 150 + 'px';
            snowflake.style.setProperty('--drift', drift);

            // Установка случайного вращения за время анимации
            const rotation = (Math.random() * 720 - 360) + 'deg'; // от -360 до +360 градусов
            snowflake.style.setProperty('--rotation', rotation);

            // Установка случайной продолжительности анимации
            snowflake.style.animationDuration = Math.random() * 10 + 5 + 's'; // 5 to 15 seconds

            // Установка случайной задержки анимации
            snowflake.style.animationDelay = Math.random() * 5 + 's'; // 0 to 5 seconds delay

            // Установка случайной прозрачности
            const opacity = Math.random() * 0.5 + 0.3; // от 0.3 до 0.8
            snowflake.style.setProperty('--opacity', opacity);
            snowflake.style.opacity = opacity;

            // Установка случайного размера
            snowflake.style.fontSize = Math.random() * 15 + 8 + 'px'; // 8 to 23px

            document.body.appendChild(snowflake);

            // Обработчик для перезапуска анимации
            snowflake.addEventListener('animationiteration', () => {
                snowflake.style.left = Math.random() * 100 + 'vw';
                snowflake.style.setProperty('--drift', (Math.random() - 0.5) * 150 + 'px');
                snowflake.style.setProperty('--rotation', (Math.random() * 720 - 360) + 'deg');
                snowflake.style.animationDuration = Math.random() * 10 + 5 + 's';
                snowflake.style.animationDelay = Math.random() * 5 + 's';
                const newOpacity = Math.random() * 0.5 + 0.3;
                snowflake.style.setProperty('--opacity', newOpacity);
                snowflake.style.opacity = newOpacity;
                snowflake.style.fontSize = Math.random() * 15 + 8 + 'px';
            });
        } catch (e) {
            console.error("Ошибка при создании снежинки:", e);
        }
    }
});
