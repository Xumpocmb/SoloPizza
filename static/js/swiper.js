document.addEventListener('DOMContentLoaded', function () {
    const container = document.querySelector('.hp-slides .swiper-container');
    if (!container) {
        return;
    }

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const nextBtn = container.querySelector('.swiper-button-next');
    const prevBtn = container.querySelector('.swiper-button-prev');

    new Swiper(container, {
        loop: true,
        speed: 600,
        slidesPerView: 1,
        centeredSlides: true,
        watchOverflow: true,
        keyboard: { enabled: true },
        autoplay: reduceMotion ? false : {
            delay: 4500,
            disableOnInteraction: false,
            pauseOnMouseEnter: true,
        },
        navigation: {
            nextEl: nextBtn,
            prevEl: prevBtn,
        },
        pagination: {
            el: '.hp-slides .swiper-pagination',
            clickable: true,
        },
        a11y: {
            enabled: true,
            prevSlideMessage: prevBtn ? prevBtn.getAttribute('aria-label') : 'Previous slide',
            nextSlideMessage: nextBtn ? nextBtn.getAttribute('aria-label') : 'Next slide',
        },
    });
});