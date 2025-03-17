document.addEventListener('DOMContentLoaded', () => {
    // Инициализация карты
    ymaps.ready(() => {
        const map = new ymaps.Map('map', {
            center: [53.15493497705694, 25.995515278775315], // Центр карты
            zoom: 12,
        });

        let marker = null; // Переменная для хранения маркера

        // Зоны доставки
        const zones = [
            {
                branch: 1,
                polygon: [
                    [53.15538848218688, 25.99611490464588],
                    [53.11462732077587, 26.030615722574737],
                    [53.116332304142645, 26.038743201964877],
                    [53.112574936307254, 26.046213118296805],
                    [53.11506935999296, 26.05444580777595],
                    [53.117823862758854, 26.067827467790323],
                    [53.10986852783711, 26.06841219891524],
                    [53.10782091083411, 26.07182316574901],
                    [53.117004983633706, 26.082705519481834],
                    [53.12489078032931, 26.108049355790797],
                    [53.1343415044681, 26.108590086010338],
                    [53.15015938201773, 26.08692359282054],
                    [53.15939290518523, 26.044060140965854],
                    [53.16680629325404, 26.05353284801896],
                    [53.171252299054345, 26.041020571278295],
                    [53.17932499915085, 26.039251700932567],
                    [53.178569632598794, 26.010660248056553],
                    [53.169412182734504, 26.00954976460949],
                    [53.15538485768562, 25.996113223797295],
                ],
            },
            {
                branch: 2,
                polygon: [
                    [53.15493497705694, 25.995515278775315],
                    [53.15251678430249, 25.98783176389341],
                    [53.1465745359495, 25.973002317067937],
                    [53.13732027840905, 25.9473378197616],
                    [53.117464219887836, 25.947437399064],
                    [53.1052200298505, 25.950909865496754],
                    [53.09406867432463, 25.961858845135595],
                    [53.1050342064178, 25.981643498053415],
                    [53.09469257097274, 25.994419886028254],
                    [53.10128176647072, 26.01314678950814],
                    [53.096711029243636, 26.02410708718503],
                    [53.1049453390566, 26.038709920232264],
                    [53.1553487009661, 25.995981022374053],
                    [53.15493375674981, 25.995508127787872],
                ],
            },
        ];

        // Отрисовка зон доставки
        function drawZones() {
            for (const zone of zones) {
                const polygon = new ymaps.Polygon([zone.polygon], {}, {
                    fillColor: 'blue',
                    fillOpacity: 0.2,
                    strokeColor: 'blue',
                    strokeWidth: 2,
                    interactive: false, // Делаем полигон некликабельным
                });
                map.geoObjects.add(polygon);
            }
        }

        // Функция для обратного геокодирования
        async function reverseGeocode(coords) {
            try {
                const response = await fetch(
                    `https://geocode-maps.yandex.ru/1.x/?apikey=7ba5ea66-ffa8-4bfe-b142-414f7dc61c5d&format=json&geocode=${coords[1]},${coords[0]}`
                );
                const data = await response.json();
                if (data.response.GeoObjectCollection.featureMember.length > 0) {
                    return data.response.GeoObjectCollection.featureMember[0].GeoObject.metaDataProperty.GeocoderMetaData.text;
                }
                return 'Адрес не найден';
            } catch (error) {
                console.error('Ошибка при обратном геокодировании:', error);
                return 'Адрес не найден';
            }
        }

        // Обработка клика по карте
        map.events.add('click', async (e) => {
            const coords = e.get('coords');

            // Удаляем предыдущий маркер
            if (marker) {
                map.geoObjects.remove(marker);
            }

            // Добавляем новый маркер
            marker = new ymaps.Placemark(coords);
            map.geoObjects.add(marker);

            // Сохраняем координаты в форму
            document.getElementById('address-lat').value = coords[0];
            document.getElementById('address-lng').value = coords[1];

            // Выполняем обратное геокодирование
            const address = await reverseGeocode(coords);
            document.getElementById('selected-address').value = address;
        });

        // Инициализация карты
        drawZones();
    });
});