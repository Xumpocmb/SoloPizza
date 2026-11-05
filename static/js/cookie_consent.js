/* Solo Pizza — cookie-баннер: согласие запоминается в cookie sp_cookie_consent. */
(function () {
    var acceptButton = document.getElementById("cookie-consent-accept");
    if (!acceptButton) {
        return;
    }
    acceptButton.addEventListener("click", function () {
        document.cookie = "sp_cookie_consent=1; path=/; max-age=31536000; samesite=lax";
        var banner = document.getElementById("cookie-consent");
        if (banner) {
            banner.remove();
        }
    });
})();
