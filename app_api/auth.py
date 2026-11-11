"""Вход в мобильном приложении через Google и Apple.

Приложение получает от Google/Apple подписанный токен и присылает его сюда. Сервер
проверяет подпись и получателя (aud), находит или создаёт пользователя и выдаёт свои JWT.
Аккаунт общий с сайтом: тот же Google-аккаунт (SocialAccount allauth) — тот же User.
"""

import uuid

import jwt
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.tokens import RefreshToken

from app_cart.models import Cart

APPLE_ISSUER = "https://appleid.apple.com"
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
_apple_keys = jwt.PyJWKClient(APPLE_KEYS_URL)  # кэширует ключи Apple между запросами


class InvalidProviderToken(APIException):
    # не AuthenticationFailed: у эндпоинтов входа нет схемы аутентификации, и DRF превратил бы его в 403
    status_code = 401
    default_detail = "Недействительный токен входа"


class ProviderNotConfigured(Exception):
    """Нет Client ID / bundle id в настройках — вход через провайдера выключен."""


def verify_google(token):
    """Claims проверенного Google id_token: sub, email, email_verified, given_name, family_name."""
    if not settings.GOOGLE_OAUTH_CLIENT_IDS:
        raise ProviderNotConfigured("google")
    try:
        claims = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), audience=settings.GOOGLE_OAUTH_CLIENT_IDS
        )
    except ValueError as error:
        raise InvalidProviderToken("Недействительный токен Google") from error
    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise InvalidProviderToken("Недействительный токен Google")
    return claims


def verify_apple(token):
    """Claims проверенного identity_token Sign in with Apple: sub, email, email_verified."""
    if not settings.APPLE_BUNDLE_ID:
        raise ProviderNotConfigured("apple")
    try:
        key = _apple_keys.get_signing_key_from_jwt(token).key
        return jwt.decode(token, key, algorithms=["RS256"], audience=settings.APPLE_BUNDLE_ID, issuer=APPLE_ISSUER)
    except jwt.PyJWTError as error:
        raise InvalidProviderToken("Недействительный токен Apple") from error


def _verified(claims):
    # Apple присылает email_verified строкой "true", Google — булевым
    return str(claims.get("email_verified", "")).lower() == "true"


def resolve_user(provider, claims, first_name="", last_name=""):
    """Пользователь по аккаунту провайдера; при первом входе — связь с сайтом или новый пользователь."""
    uid = str(claims["sub"])
    account = SocialAccount.objects.select_related("user").filter(provider=provider, uid=uid).first()
    if account is not None:
        return account.user

    User = get_user_model()
    email = (claims.get("email") or "").strip().lower()
    with transaction.atomic():
        user = None
        # Связываем с аккаунтом сайта только по email, подтверждённому с обеих сторон:
        # иначе чужой непроверенный email на сайте открыл бы доступ к чужим заказам.
        if email and _verified(claims):
            address = EmailAddress.objects.select_related("user").filter(email__iexact=email, verified=True).first()
            user = address.user if address else None
        if user is None:
            email_taken = bool(email) and User.objects.filter(email__iexact=email).exists()
            user = User.objects.create_user(
                username=f"{provider}_{uid}"[:150],
                email="" if email_taken else email,
                first_name=(first_name or claims.get("given_name") or "")[:150],
                last_name=(last_name or claims.get("family_name") or "")[:150],
            )
            user.set_unusable_password()
            user.save(update_fields=["password"])
            if email and not email_taken:
                EmailAddress.objects.create(user=user, email=email, verified=_verified(claims), primary=True)
        SocialAccount.objects.create(user=user, provider=provider, uid=uid, extra_data=claims)
    return user


def merge_guest_cart(user, cart_token):
    """Гостевая корзина (X-Cart-Token) переходит к пользователю; одинаковые позиции суммируются."""
    try:
        guest = Cart.objects.get(token=uuid.UUID(str(cart_token)), user__isnull=True)
    except (ValueError, Cart.DoesNotExist):
        return
    with transaction.atomic():
        own = Cart.objects.select_for_update().filter(user=user).first()
        if own is None:
            guest.user = user
            guest.save(update_fields=["user", "updated_at"])
            return
        if own.branch_id != guest.branch_id:
            own.change_branch(guest.branch)  # последний выбор филиала — гостевой
        for item in guest.items.prefetch_related("addons"):
            own.add_item(
                product=item.item, variant=item.item_variant, board1=item.board1, board2=item.board2,
                sauce=item.sauce, addons=list(item.addons.all()), drink=item.drink, quantity=item.quantity,
            )
        guest.delete()


def issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}
