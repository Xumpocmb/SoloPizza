document.addEventListener('DOMContentLoaded', () => {
    ymaps.ready(initMap);

    function initMap() {
        const map = new ymaps.Map('map', {
            center: [53.132096, 26.016741],
            zoom: 15,
            controls: ['zoomControl', 'geolocationControl'],
            behaviors: []
        });

        const input = document.getElementById('suggest');
        const suggestView = new ymaps.SuggestView(input, {
            boundedBy: [
                [53.1, 25.9], // Нижний левый угол (широта, долгота)
                [53.2, 26.1]  // Верхний правый угол (широта, долгота)
            ],
            type: 'street',

        });

        // Обработчик события выбора адреса из подсказок
        suggestView.events.add('select', function (e) {
            const selectedAddress = e.get('item').value;
            console.log("Выбран адрес: ", selectedAddress);

            // Геокодируем выбранный адрес
            geocodeAddress(selectedAddress, map);
        });


        const geojsonData = {
            "type": "FeatureCollection",
            "features": [
                {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[53.12016932766892, 25.942110969358477], [53.10193816606688, 25.93597407513279], [53.096410472589916, 25.939557506376563], [53.09372385917507, 25.962581588560337], [53.09693586903646, 25.99223609142947], [53.09346990222358, 26.01660070972597], [53.10385163506802, 26.03126956956558], [53.10666564755931, 26.035248981467824], [53.11197788631779, 26.033021332706674], [53.113808025200335, 26.03195134581119], [53.11515556420641, 26.030976470085015], [53.115160405578564, 26.030559493833916], [53.132076072755034, 26.016772939497297], [53.13481915573152, 26.014547685273303], [53.14607355136876, 26.004318538166377], [53.15526695782747, 25.995669318968474], [53.15067493610756, 25.97906108074842], [53.141773264050315, 25.94417090588214], [53.12016932766892, 25.942110969358477]]]
                    },
                    "properties": {
                        "fill": "#1bad03",
                        "fill-opacity": 0.2,
                        "stroke": "#1bad03",
                        "stroke-width": 3,
                        "stroke-opacity": 0.9
                    }
                },
                {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[53.1721796568612, 26.041105939680737], [53.17089032357466, 26.027549520242882], [53.15533144910388, 25.996007277304113], [53.14568168110727, 26.00495896797535], [53.14425124352615, 26.006249884031014], [53.14225790456097, 26.008155263895578], [53.14069510051188, 26.009811514749774], [53.13477882941135, 26.014658277674922], [53.131193667576326, 26.017644974027398], [53.12227180291621, 26.024903407072255], [53.11473194127535, 26.031369071534876], [53.11366762051099, 26.032166052533935], [53.11207472102129, 26.03317843372217], [53.10694137256191, 26.037774636084155], [53.110482418936925, 26.07457990818629], [53.117979131620935, 26.08522827797556], [53.12129238188111, 26.099138213927016], [53.12464845982193, 26.10450263195672], [53.12893353042655, 26.10772128277472], [53.13791529714654, 26.103515579039176], [53.147914326043896, 26.09552116143435], [53.154892907214865, 26.073861076170626], [53.1721796568612, 26.041105939680737]]]
                    },
                    "properties": {
                        "fill": "#56db40",
                        "fill-opacity": 0.2,
                        "stroke": "#56db40",
                        "stroke-width": 3,
                        "stroke-opacity": 0.9
                    }
                }
            ]
        };

        function drawZones() {
            geojsonData.features.forEach(feature => {
                const polygon = new ymaps.Polygon(
                    feature.geometry.coordinates,
                    {},
                    {
                        fillColor: feature.properties.fill,
                        fillOpacity: feature.properties["fill-opacity"],
                        strokeColor: feature.properties.stroke,
                        strokeWidth: feature.properties["stroke-width"],
                        strokeOpacity: feature.properties["stroke-opacity"],
                        interactive: false
                    }
                );
                map.geoObjects.add(polygon);
            });
        }

        function isPointInZone(point) {
            let result = false;
            map.geoObjects.each((object) => {
                if (object.geometry && object.geometry.contains) {
                    if (object.geometry.contains(point)) {
                        result = true;
                    }
                }
            });
            return result;
        }

        function updateAddress() {
            const currentCoords = map.getCenter();
            document.getElementById('address-lat').value = currentCoords[0];
            document.getElementById('address-lng').value = currentCoords[1];

            if (isPointInZone(currentCoords)) {
                document.getElementById('suggest').style.borderColor = 'green';
            } else {
                document.getElementById('suggest').style.borderColor = 'red';
            }

            reverseGeocode(currentCoords).then(address => {
                document.getElementById('suggest').value = address;
            });
        }

        async function reverseGeocode(coords) {
            try {
                const response = await fetch(`https://geocode-maps.yandex.ru/1.x/?apikey=7ba5ea66-ffa8-4bfe-b142-414f7dc61c5d&format=json&geocode=${coords[1]},${coords[0]}`);
                const data = await response.json();
                if (data.response.GeoObjectCollection.featureMember.length > 0) {
                    const fullAddress = data.response.GeoObjectCollection.featureMember[0].GeoObject.metaDataProperty.GeocoderMetaData.text;
                    const addressParts = fullAddress.split(',');

                    const filteredAddress = addressParts.filter((part, index) => index > 2);
                    return filteredAddress.join(', ').trim();
                }
                return 'Адрес не найден';
            } catch (error) {
                console.error('Ошибка при геокодировании:', error);
                return 'Ошибка поиска';
            }
        }

        async function geocodeAddress() {
            const address = document.getElementById('suggest').value;
            if (!address) return;
            try {
                const response = await fetch(`https://geocode-maps.yandex.ru/1.x/?apikey=7ba5ea66-ffa8-4bfe-b142-414f7dc61c5d&format=json&geocode=${encodeURIComponent(address)}`);
                const data = await response.json();
                if (data.response.GeoObjectCollection.featureMember.length > 0) {
                    const coords = data.response.GeoObjectCollection.featureMember[0].GeoObject.Point.pos.split(' ').map(Number).reverse();
                    map.setCenter(coords, 20);
                } else {
                    alert('Адрес не найден');
                }
            } catch (error) {
                console.error('Ошибка при поиске адреса:', error);
            }
        }

        drawZones();
        map.events.add('boundschange', updateAddress);
    }
});

