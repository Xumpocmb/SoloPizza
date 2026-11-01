(function () {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    const burger = document.querySelector('.burger');

    function setSidebarState(open) {
        if (!sidebar || !overlay) {
            return;
        }

        sidebar.classList.toggle('open', open);
        overlay.classList.toggle('show', open);
        sidebar.setAttribute('aria-hidden', open ? 'false' : 'true');
        document.body.classList.toggle('menu-open', open);

        if (burger) {
            const label = open ? burger.dataset.labelClose : burger.dataset.labelOpen;
            burger.classList.toggle('active', open);
            burger.setAttribute('aria-expanded', open ? 'true' : 'false');
            if (label) {
                burger.setAttribute('aria-label', label);
            }
        }
    }

    window.toggleSidebar = function () {
        if (!sidebar) {
            return;
        }
        setSidebarState(!sidebar.classList.contains('open'));
    };

    window.toggleSubmenu = function (id, button) {
        const submenu = document.getElementById(id);
        if (!submenu) {
            return;
        }

        const willOpen = !submenu.classList.contains('open');

        // Аккордеон: одновременно открыто только одно подменю.
        document.querySelectorAll('.submenu.open').forEach(function (item) {
            if (item === submenu) {
                return;
            }
            item.classList.remove('open');
            const control = document.querySelector('[aria-controls="' + item.id + '"]');
            if (control) {
                control.setAttribute('aria-expanded', 'false');
            }
        });

        submenu.classList.toggle('open', willOpen);
        if (button) {
            button.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        if (sidebar) {
            sidebar.querySelectorAll('a').forEach(function (link) {
                link.addEventListener('click', function () {
                    setSidebarState(false);
                });
            });
        }

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                setSidebarState(false);
            }
        });
    });

    // Переключатель темы
    const themeToggle = document.getElementById('themeToggle');

    if (themeToggle) {
        if (localStorage.getItem('theme') === 'dark') {
            document.documentElement.classList.add('dark');
            themeToggle.checked = true;
        }

        themeToggle.addEventListener('change', function () {
            if (this.checked) {
                document.documentElement.classList.add('dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('theme', 'light');
            }
        });
    }
})();
