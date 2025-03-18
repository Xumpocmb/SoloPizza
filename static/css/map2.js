document.addEventListener('DOMContentLoaded', () => {
    // Инициализация карты
    ymaps.ready(() => {
        const map = new ymaps.Map('map', {
            center: [53.15493497705694, 25.995515278775315], // Центр карты
            zoom: 12,
            controls: ['zoomControl', 'geolocationControl'], // Оставляем только кнопки зума и геолокации
        });

        // Данные о полигонах (ваш экспорт)
        const geojsonData = {
            "type": "FeatureCollection",
            "metadata": {
                "name": "SoloPizzaMap",
                "creator": "Yandex Map Constructor"
            },
            "features": [
                {
                    "type": "Feature",
                    "id": 0,
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[25.942110969358477, 53.12016932766892], [25.93597407513279, 53.10193816606688], [25.939557506376563, 53.096410472589916], [25.962581588560337, 53.09372385917507], [25.99223609142947, 53.09693586903646], [26.01660070972597, 53.09346990222358], [26.03126956956558, 53.10385163506802], [26.035248981467824, 53.10666564755931], [26.033021332706674, 53.11197788631779], [26.03195134581119, 53.113808025200335], [26.030976470085015, 53.11515556420641], [26.030559493833916, 53.115160405578564], [26.016772939497297, 53.132076072755034], [26.014547685273303, 53.13481915573152], [26.004318538166377, 53.14607355136876], [25.995669318968474, 53.15526695782747], [25.97906108074842, 53.15067493610756], [25.94417090588214, 53.141773264050315], [25.942110969358477, 53.12016932766892]]]
                    },
                    "properties": {
                        "fill": "#1bad03",
                        "fill-opacity": 0.2,
                        "stroke": "#1bad03",
                        "stroke-width": "3",
                        "stroke-opacity": 0.9
                    }
                },
                {
                    "type": "Feature",
                    "id": 1,
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[26.041105939680737, 53.1721796568612], [26.027549520242882, 53.17089032357466], [25.996007277304113, 53.15533144910388], [26.00495896797535, 53.14568168110727], [26.006249884031014, 53.14425124352615], [26.008155263895578, 53.14225790456097], [26.009811514749774, 53.14069510051188], [26.014658277674922, 53.13477882941135], [26.017644974027398, 53.131193667576326], [26.024903407072255, 53.12227180291621], [26.031369071534876, 53.11473194127535], [26.032166052533935, 53.11366762051099], [26.03317843372217, 53.11207472102129], [26.037774636084155, 53.10694137256191], [26.07457990818629, 53.110482418936925], [26.08522827797556, 53.117979131620935], [26.099138213927016, 53.12129238188111], [26.10450263195672, 53.12464845982193], [26.10772128277472, 53.12893353042655], [26.103515579039176, 53.13791529714654], [26.09552116143435, 53.147914326043896], [26.073861076170626, 53.154892907214865], [26.041105939680737, 53.1721796568612]]]
                    },
                    "properties": {
                        "fill": "#56db40",
                        "fill-opacity": 0.2,
                        "stroke": "#56db40",
                        "stroke-width": "3",
                        "stroke-opacity": 0.9
                    }
                }
            ]
        };

        // Отрисовка зон доставки
        function drawZones() {
            geojsonData.features.forEach(feature => {
                const polygon = new ymaps.Polygon(
                    feature.geometry.coordinates,
                    {},
                    {
                        fillColor: feature.properties['fill'],
                        fillOpacity: parseFloat(feature.properties['fill-opacity']),
                        strokeColor: feature.properties['stroke'],
                        strokeWidth: parseInt(feature.properties['stroke-width']),
                        strokeOpacity: parseFloat(feature.properties['stroke-opacity']),
                        interactive: false, // Делаем полигон некликабельным
                    }
                );
                map.geoObjects.add(polygon);
            });
        }

        // Обновление координат при движении карты
        let currentCoords = map.getCenter();
        map.events.add('boundschange', () => {
            currentCoords = map.getCenter();

            // Обновляем координаты в форме
            document.getElementById('address-lat').value = currentCoords[0];
            document.getElementById('address-lng').value = currentCoords[1];

            // Выполняем обратное геокодирование
            reverseGeocode(currentCoords).then((address) => {
                document.getElementById('selected-address').value = address;
            });
        });

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

        // Инициализация карты
        drawZones();
    });
});