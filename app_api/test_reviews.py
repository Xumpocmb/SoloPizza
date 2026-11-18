from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from app_api.auth import issue_tokens
from app_reviews.models import Review

User = get_user_model()


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class ReviewApiTests(TestCase):
    def setUp(self):
        cache.clear()  # счётчики throttle
        self.anna = User.objects.create_user(username="anna@gmail.com", email="anna@gmail.com", first_name="Анна", last_name="Петрова")
        self.client = APIClient()

    def authed(self, user):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(user)['access']}")
        return client

    def test_list_shows_only_approved_published_without_login_or_email(self):
        Review.objects.create(user=self.anna, text="Вкусно", rating=5, status="approved")
        Review.objects.create(user=self.anna, text="Ждёт модерации", rating=4)
        Review.objects.create(user=self.anna, text="Скрыт", rating=3, status="approved", is_published=False)

        data = self.client.get("/api/v1/reviews/").json()

        self.assertEqual([(r["text"], r["rating"], r["author"]) for r in data], [("Вкусно", 5, "Анна П.")])
        self.assertNotIn("anna@gmail.com", str(data))

    def test_author_without_name_is_guest(self):
        nameless = User.objects.create_user(username="x@gmail.com")
        Review.objects.create(user=nameless, text="Норм", rating=4, status="approved")
        self.assertEqual(self.client.get("/api/v1/reviews/").json()[0]["author"], "Гость")

    def test_guest_cannot_post(self):
        response = self.client.post("/api/v1/reviews/", {"text": "Привет", "rating": 5}, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(Review.objects.exists())

    def test_logged_in_post_goes_to_moderation(self):
        response = self.authed(self.anna).post("/api/v1/reviews/", {"text": "Быстрая доставка", "rating": 5}, format="json")

        self.assertEqual(response.status_code, 201, response.json())
        review = Review.objects.get()
        self.assertEqual((review.user, review.status, review.rating), (self.anna, "pending", 5))
        self.assertEqual(self.client.get("/api/v1/reviews/").json(), [])  # до одобрения в ленте нет

    def test_rating_and_text_are_validated(self):
        client = self.authed(self.anna)
        self.assertIn("rating", client.post("/api/v1/reviews/", {"text": "Ок", "rating": 6}, format="json").json())
        self.assertIn("text", client.post("/api/v1/reviews/", {"text": "", "rating": 4}, format="json").json())
        self.assertFalse(Review.objects.exists())
