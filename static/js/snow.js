document.addEventListener('DOMContentLoaded', function () {
    const numSnowflakes = 25;
    for (let i = 0; i < numSnowflakes; i++) {
        createSnowflake();
    }

    function createSnowflake() {
        try {
            const snowflake = document.createElement('div');
            snowflake.classList.add('snowflake');

            // Случайный выбор символа снежинки (только настоящие символы снежинок)
            const snowflakeSymbol = '&#10052;'; // Только один вид снежинки
            snowflake.innerHTML = snowflakeSymbol;

            // Установка случайной позиции по горизонтали
            snowflake.style.left = Math.random() * 100 + 'vw';

            // Установка случайного сноса (дрейфа) влево или вправо

            // Установка случайного вращения за время анимации

            // Установка случайной продолжительности анимации
            snowflake.style.animationDuration = '15s'; // Фиксированная продолжительность для медленного падения

            // Установка случайной задержки анимации
            snowflake.style.animationDelay = Math.random() * 10 + 's'; // Случайная задержка до 10 секунд

            // Установка случайной прозрачности (от 0.3 до 0.8, чтобы снежинки не были слишком тусклыми или прозрачными)
            snowflake.style.opacity = '0.7'; // Фиксированная прозрачность

            // Установка случайного размера
            snowflake.style.fontSize = '18px'; // Фиксированный размер

            document.body.appendChild(snowflake);

        } catch (e) {
            console.error("Ошибка при создании снежинки:", e);
        }
    }
});
