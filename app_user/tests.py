from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase
from django.urls import reverse


class UserModelTests(TestCase):
    """У штатного User не должно быть самодельных полей телефона и адреса."""

    def test_user_has_no_phone_and_address_fields(self):
        field_names = {field.name for field in get_user_model()._meta.get_fields()}

        self.assertNotIn("phone", field_names)
        self.assertNotIn("address", field_names)


class RegistrationTests(TestCase):
    def test_registration_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("app_user:register"),
            {
                "username": "newuser",
                "password1": "Sup3r-secret",
                "password2": "Sup3r-secret",
            },
        )

        self.assertRedirects(response, reverse("app_user:login"))
        self.assertTrue(get_user_model().objects.filter(username="newuser").exists())


class LoginTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="pizza-fan",
            password="Sup3r-secret",
        )

    def test_authenticate_by_username(self):
        self.assertEqual(
            authenticate(username="pizza-fan", password="Sup3r-secret"),
            self.user,
        )

    def test_login_creates_authenticated_session(self):
        response = self.client.post(
            reverse("app_user:login"),
            {"username": "pizza-fan", "password": "Sup3r-secret"},
        )

        self.assertRedirects(response, reverse("app_home:home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)
