import time
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

import jwt
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from app_catalog.models import Category, Product, ProductVariant
from app_home.models import CafeBranch
from app_order.models import Order

User = get_user_model()
APPLE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def apple_token(sub="apple-sub-1", aud="by.solopizza.app", email="user@privaterelay.appleid.com", iss="https://appleid.apple.com"):
    now = int(time.time())
    claims = {"iss": iss, "aud": aud, "sub": sub, "iat": now, "exp": now + 600, "email": email, "email_verified": "true"}
    return jwt.encode(claims, APPLE_KEY, algorithm="RS256")


def google_claims(sub="google-sub-1", email="ivan@gmail.com", verified=True):
    return {
        "iss": "https://accounts.google.com", "sub": sub, "email": email,
        "email_verified": verified, "given_name": "Иван", "family_name": "Петров",
    }


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    GOOGLE_OAUTH_CLIENT_IDS=["web-client-id"],
    APPLE_BUNDLE_ID="by.solopizza.app",
)
class AuthApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        signing_key = SimpleNamespace(key=APPLE_KEY.public_key())
        patcher = mock.patch("app_api.auth._apple_keys.get_signing_key_from_jwt", return_value=signing_key)
        patcher.start()
        self.addCleanup(patcher.stop)

        self.branch = CafeBranch.objects.create(name="Ленина", address="ул. Ленина 9/1", is_active=True)
        category = Category.objects.create(name="Напитки", slug="drinks")
        category.branch.add(self.branch)
        self.cola = Product.objects.create(name="Кола", slug="cola", category=category)
        self.cola_05 = ProductVariant.objects.create(product=self.cola, value="0.5", unit="l", price=Decimal("3.00"))

    def google_login(self, claims, **headers):
        with mock.patch("app_api.auth.google_id_token.verify_oauth2_token", return_value=claims):
            return self.client.post("/api/v1/auth/google/", {"id_token": "x"}, format="json", **headers)

    def auth(self, access):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    # ── Google ──────────────────────────────────────────────────────────

    def test_google_first_login_creates_user_and_second_finds_it(self):
        first = self.google_login(google_claims())
        self.assertEqual(first.status_code, 200, first.json())
        self.assertIn("access", first.json())
        self.assertEqual(first.json()["user"]["first_name"], "Иван")
        second = self.google_login(google_claims())
        self.assertEqual(second.json()["user"]["id"], first.json()["user"]["id"])
        self.assertEqual(User.objects.count(), 1)

    def test_google_account_from_website_is_the_same_user(self):
        site_user = User.objects.create_user(username="ivan", email="ivan@gmail.com")
        SocialAccount.objects.create(user=site_user, provider="google", uid="google-sub-1")
        self.assertEqual(self.google_login(google_claims()).json()["user"]["id"], site_user.pk)

    def test_links_to_site_account_only_by_verified_email(self):
        verified = User.objects.create_user(username="verified", email="ivan@gmail.com")
        EmailAddress.objects.create(user=verified, email="ivan@gmail.com", verified=True, primary=True)
        self.assertEqual(self.google_login(google_claims()).json()["user"]["id"], verified.pk)

        unverified = User.objects.create_user(username="unverified", email="petr@gmail.com")
        EmailAddress.objects.create(user=unverified, email="petr@gmail.com", verified=False, primary=True)
        data = self.google_login(google_claims(sub="google-sub-2", email="petr@gmail.com")).json()
        self.assertNotEqual(data["user"]["id"], unverified.pk)
        self.assertEqual(data["user"]["email"], "")  # чужой email не дублируем

    def test_invalid_google_token_is_401(self):
        with mock.patch("app_api.auth.google_id_token.verify_oauth2_token", side_effect=ValueError("bad")):
            response = self.client.post("/api/v1/auth/google/", {"id_token": "x"}, format="json")
        self.assertEqual(response.status_code, 401)
        wrong_issuer = self.google_login({**google_claims(), "iss": "https://evil.example"})
        self.assertEqual(wrong_issuer.status_code, 401)

    @override_settings(GOOGLE_OAUTH_CLIENT_IDS=[])
    def test_google_not_configured_is_503(self):
        self.assertEqual(self.client.post("/api/v1/auth/google/", {"id_token": "x"}, format="json").status_code, 503)

    # ── Apple ───────────────────────────────────────────────────────────

    def test_apple_login_checks_signature_audience_and_issuer(self):
        ok = self.client.post(
            "/api/v1/auth/apple/", {"identity_token": apple_token(), "first_name": "Анна"}, format="json"
        )
        self.assertEqual(ok.status_code, 200, ok.json())
        self.assertEqual(ok.json()["user"]["first_name"], "Анна")
        self.assertTrue(SocialAccount.objects.filter(provider="apple", uid="apple-sub-1").exists())

        for bad in (apple_token(aud="other.app"), apple_token(iss="https://evil.example")):
            response = self.client.post("/api/v1/auth/apple/", {"identity_token": bad}, format="json")
            self.assertEqual(response.status_code, 401)
        forged = jwt.encode({"sub": "x", "aud": "by.solopizza.app"}, rsa.generate_private_key(65537, 2048), algorithm="RS256")
        self.assertEqual(self.client.post("/api/v1/auth/apple/", {"identity_token": forged}, format="json").status_code, 401)

    # ── Токены и профиль ────────────────────────────────────────────────

    def test_me_requires_token_and_shows_last_order_phone(self):
        self.assertEqual(self.client.get("/api/v1/me/").status_code, 401)
        data = self.google_login(google_claims()).json()
        user = User.objects.get(pk=data["user"]["id"])
        Order.objects.create(
            user=user, branch=self.branch, customer_name="Иван", phone_number="+375291112233",
            delivery_type="pickup", payment_method="cash",
        )
        self.auth(data["access"])
        self.assertEqual(self.client.get("/api/v1/me/").json()["phone"], "+375291112233")
        patched = self.client.patch("/api/v1/me/", {"first_name": "Ваня", "email": "hack@x.by"}, format="json").json()
        self.assertEqual((patched["first_name"], patched["email"]), ("Ваня", "ivan@gmail.com"))

    def test_refresh_rotates_and_logout_blacklists(self):
        refresh = self.google_login(google_claims()).json()["refresh"]
        rotated = self.client.post("/api/v1/auth/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(rotated.status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/refresh/", {"refresh": refresh}, format="json").status_code, 401)
        new_refresh = rotated.json()["refresh"]
        self.assertEqual(self.client.post("/api/v1/auth/logout/", {"refresh": new_refresh}, format="json").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/refresh/", {"refresh": new_refresh}, format="json").status_code, 401)

    def test_delete_account_keeps_orders(self):
        data = self.google_login(google_claims()).json()
        order = Order.objects.create(
            user_id=data["user"]["id"], branch=self.branch, customer_name="Иван", phone_number="+375291112233",
            delivery_type="pickup", payment_method="cash",
        )
        self.auth(data["access"])
        self.assertEqual(self.client.delete("/api/v1/me/").status_code, 204)
        self.assertFalse(User.objects.filter(pk=data["user"]["id"]).exists())
        order.refresh_from_db()
        self.assertIsNone(order.user_id)

    # ── Корзина при входе ───────────────────────────────────────────────

    def guest_cart_with_cola(self, quantity):
        token = self.client.post("/api/v1/cart/", {"branch_id": self.branch.pk}, format="json").json()["token"]
        self.client.post(
            "/api/v1/cart/items/", {"product_id": self.cola.pk, "variant_id": self.cola_05.pk, "quantity": quantity},
            format="json", HTTP_X_CART_TOKEN=token,
        )
        return token

    def test_guest_cart_becomes_user_cart_on_login(self):
        token = self.guest_cart_with_cola(2)
        access = self.google_login(google_claims(), HTTP_X_CART_TOKEN=token).json()["access"]
        self.auth(access)
        self.assertEqual(self.client.get("/api/v1/cart/").json()["items_count"], 2)

    def test_guest_cart_merges_into_existing_user_cart(self):
        access = self.google_login(google_claims(), HTTP_X_CART_TOKEN=self.guest_cart_with_cola(2)).json()["access"]
        self.client.credentials()
        token = self.guest_cart_with_cola(3)
        self.google_login(google_claims(), HTTP_X_CART_TOKEN=token)
        self.auth(access)
        cart = self.client.get("/api/v1/cart/").json()
        self.assertEqual((len(cart["items"]), cart["items_count"]), (1, 5))
        self.client.credentials()
        self.assertEqual(self.client.get("/api/v1/cart/", HTTP_X_CART_TOKEN=token).status_code, 404)

    def test_user_has_one_cart(self):
        self.auth(self.google_login(google_claims()).json()["access"])
        first = self.client.post("/api/v1/cart/", {"branch_id": self.branch.pk}, format="json")
        second = self.client.post("/api/v1/cart/", {"branch_id": self.branch.pk}, format="json")
        self.assertEqual((first.status_code, second.status_code), (201, 200))
        self.assertEqual(first.json()["token"], second.json()["token"])
