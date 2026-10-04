/**
 * Уведомления о новых заказах для сотрудников на странице списка заказов.
 * Опрашивает лёгкий JSON-эндпоинт и показывает тост + звук + счётчик непрочитанных заказов.
 */
(function () {
    'use strict';

    var configNode = document.getElementById('order-poll-config');
    var config = configNode ? JSON.parse(configNode.textContent) : {};
    var POLL_URL = config.url;
    if (!POLL_URL) {
        return;
    }

    var POLL_INTERVAL_MS = 10000;
    var TOAST_LIFETIME_MS = 15000;
    var TOASTS_PER_FLUSH = 5;
    var HINT_LIFETIME_MS = 60000;

    var T = window.ORDER_POLL_TRANSLATIONS || {};
    var TEXT = {
        newOrder: T.newOrder || 'Новый заказ',
        orders: T.orders || 'Заказы',
        refresh: T.refresh || 'Обновить',
        open: T.open || 'Открыть',
        soundHint: T.soundHint || 'Нажмите, чтобы включить звук уведомлений',
        soundOn: '🔔',
        soundOff: '🔕'
    };

    var since = Number(config.since) || 0;
    var baseTitle = document.title;
    var queue = [];
    var newCount = 0;
    var inFlight = false;
    var stopped = false;

    /* ---------- Звук ---------- */

    var audioContext = null;
    var soundEnabled = true;

    function getAudioContext() {
        if (!soundEnabled || typeof window.AudioContext === 'undefined' && typeof window.webkitAudioContext === 'undefined') {
            return null;
        }
        try {
            if (!audioContext) {
                var Ctor = window.AudioContext || window.webkitAudioContext;
                audioContext = new Ctor();
            }
            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }
            return audioContext;
        } catch (e) {
            return null;
        }
    }

    function playTone(ctx, frequency, startAt, duration) {
        var oscillator = ctx.createOscillator();
        var gain = ctx.createGain();
        oscillator.type = 'sine';
        oscillator.frequency.value = frequency;
        gain.gain.setValueAtTime(0.0001, startAt);
        gain.gain.exponentialRampToValueAtTime(0.25, startAt + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, startAt + duration);
        oscillator.connect(gain);
        gain.connect(ctx.destination);
        oscillator.start(startAt);
        oscillator.stop(startAt + duration + 0.02);
    }

    function playAlert() {
        var ctx = getAudioContext();
        if (!ctx) {
            return false;
        }
        var startAt = ctx.currentTime;
        for (var i = 0; i < 3; i++) {
            playTone(ctx, 932.33, startAt + i * 0.45, 0.12);
            playTone(ctx, 698.46, startAt + i * 0.45 + 0.16, 0.22);
        }
        return true;
    }

    function alertWithFallback() {
        if (playAlert()) {
            return;
        }
        showHint();
    }

    /* ---------- Уведомления ---------- */

    function getContainer() {
        var container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            document.body.appendChild(container);
        }
        return container;
    }

    function dismissLater(node, lifetime) {
        setTimeout(function () {
            node.classList.add('hide');
            node.addEventListener('transitionend', function () {
                node.remove();
            });
            setTimeout(function () {
                node.remove();
            }, 600);
        }, lifetime);
    }

    function showOrderToast(order) {
        var parts = [];
        if (order.customer_name) {
            parts.push(order.customer_name);
        }
        if (order.delivery_type) {
            parts.push(order.delivery_type);
        }
        if (order.total_price) {
            parts.push(order.total_price);
        }
        if (order.phone_number) {
            parts.push(order.phone_number);
        }

        var toast = document.createElement('div');
        toast.className = 'notification info notification-new-order';
        toast.setAttribute('role', 'alert');
        toast.innerHTML =
            '<div class="notification-new-order__body">' +
            '<strong class="notification-new-order__title"></strong>' +
            '<span class="notification-new-order__meta"></span>' +
            '</div>' +
            '<a class="notification-new-order__link" target="_blank" rel="noopener"></a>' +
            '<button type="button" class="close-btn">&times;</button>';
        toast.querySelector('.notification-new-order__title').textContent = TEXT.newOrder + ' #' + order.number;
        toast.querySelector('.notification-new-order__meta').textContent = parts.join(' · ');
        var link = toast.querySelector('.notification-new-order__link');
        link.textContent = TEXT.open;
        link.href = order.detail_url;

        toast.querySelector('.close-btn').addEventListener('click', function () {
            toast.remove();
        });

        getContainer().appendChild(toast);
        dismissLater(toast, TOAST_LIFETIME_MS);
    }

    function showHint() {
        if (document.getElementById('order-sound-hint')) {
            return;
        }
        var hint = document.createElement('div');
        hint.id = 'order-sound-hint';
        hint.className = 'notification info';
        hint.setAttribute('role', 'alert');
        hint.textContent = TEXT.soundHint;
        getContainer().appendChild(hint);
        hint.addEventListener('click', function () {
            if (getAudioContext() && audioContext.state === 'running') {
                hint.remove();
            }
        });
        dismissLater(hint, HINT_LIFETIME_MS);
    }

    function flushToasts() {
        if (document.hidden) {
            return;
        }
        var shown = 0;
        while (queue.length && shown < TOASTS_PER_FLUSH) {
            showOrderToast(queue.shift());
            shown += 1;
        }
    }

    /* ---------- Панель непрочитанных заказов ---------- */

    function getBar() {
        var bar = document.getElementById('new-orders-bar');
        if (bar) {
            return bar;
        }
        bar = document.createElement('div');
        bar.id = 'new-orders-bar';
        bar.className = 'new-orders-bar';
        bar.hidden = true;
        bar.innerHTML =
            '<span class="new-orders-bar__label"></span>' +
            '<button type="button" class="new-orders-bar__refresh"></button>' +
            '<button type="button" class="new-orders-bar__sound"></button>';

        bar.querySelector('.new-orders-bar__label').textContent = TEXT.orders + ' (' + newCount + ')';
        bar.querySelector('.new-orders-bar__refresh').textContent = TEXT.refresh;
        bar.querySelector('.new-orders-bar__refresh').addEventListener('click', function () {
            window.location.reload();
        });

        var soundButton = bar.querySelector('.new-orders-bar__sound');
        soundButton.textContent = soundEnabled ? TEXT.soundOn : TEXT.soundOff;
        soundButton.addEventListener('click', function () {
            soundEnabled = !soundEnabled;
            soundButton.textContent = soundEnabled ? TEXT.soundOn : TEXT.soundOff;
            if (soundEnabled) {
                getAudioContext();
            }
        });

        document.body.appendChild(bar);
        return bar;
    }

    function updateIndicators() {
        if (newCount > 0) {
            var bar = getBar();
            bar.hidden = false;
            bar.querySelector('.new-orders-bar__label').textContent = TEXT.orders + ' (' + newCount + ')';
            document.title = '(' + newCount + ') ' + baseTitle;
        } else {
            var existing = document.getElementById('new-orders-bar');
            if (existing) {
                existing.hidden = true;
            }
            document.title = baseTitle;
        }
    }

    /* ---------- Обработка новых заказов ---------- */

    function handleNewOrders(orders) {
        orders.forEach(function (order) {
            queue.push(order);
        });
        newCount += orders.length;
        updateIndicators();
        alertWithFallback();
        flushToasts();
    }

    /* ---------- Polling ---------- */

    function poll() {
        if (inFlight || stopped || document.readyState === 'loading') {
            return;
        }
        inFlight = true;
        var url = POLL_URL + (POLL_URL.indexOf('?') === -1 ? '?' : '&') + 'since=' + encodeURIComponent(since);

        fetch(url, {
            credentials: 'same-origin',
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        })
            .then(function (response) {
                if (response.status === 401 || response.status === 403) {
                    stopped = true;
                    throw new Error('access denied');
                }
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(function (data) {
                var serverTime = Number(data.server_time);
                if (!isNaN(serverTime) && serverTime > since) {
                    since = serverTime;
                }
                if (data.orders && data.orders.length) {
                    handleNewOrders(data.orders);
                }
            })
            .catch(function () {
                // Сеть недоступна или сессия истекла — следующая попытка через интервал
            })
            .then(function () {
                inFlight = false;
            });
    }

    document.addEventListener('visibilitychange', function () {
        if (!document.hidden) {
            poll();
            flushToasts();
        }
    });

    // Браузеры разрешают звук только после действия пользователя
    document.addEventListener(
        'click',
        function () {
            getAudioContext();
        },
        {once: true}
    );

    poll();
    setInterval(poll, POLL_INTERVAL_MS);
})();