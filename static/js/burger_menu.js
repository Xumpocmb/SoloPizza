$(document).ready(function () {
    const $burgerMenu = $('#burger-menu');
    const $sidebar = $('#sidebar');
    const $sidebarOverlay = $('.sidebar-overlay');

    $burgerMenu.click(function () {
        $burgerMenu.toggleClass('active');
        $sidebar.toggleClass('active');
        $('body').toggleClass('lock');
    });

    $('.sidebar-overlay').click(function () {
        $sidebar.removeClass('active');
        $sidebarOverlay.removeClass('active');
        $('body').removeClass('lock');
    });

    // Открытие подменю при клике
    $('.sidebar ul li > a').click(function (event) {
        if ($(this).next('.submenu').length) {
            $(this).next('.submenu').slideToggle();
            event.stopPropagation();
            event.preventDefault();
        }
    });
});
