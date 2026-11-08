from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Review


class BookViewTests(TestCase):
    """Тесты страницы «Книга замечаний и предложений»."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("app_reviews:review_list")
        self.user = User.objects.create_user(username="client1", password="Sup3r-secret")
        self.review = Review.objects.create(
            user=self.user,
            text="Очень вкусная пицца, быстро доставили!",
            rating=5,
            status="approved",
            is_published=True,
        )

    def test_book_view_get(self):
        """GET /reviews/ отдает страницу книги замечаний и предложений."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app_reviews/book.html")
        self.assertEqual(list(response.context["comments"]), [self.review])

    def test_book_view_shows_only_approved_and_published(self):
        """В книгу попадают только одобренные и опубликованные отзывы."""
        Review.objects.create(user=self.user, text="Отзыв на модерации", rating=3, status="pending", is_published=True)
        Review.objects.create(user=self.user, text="Отзыв не опубликован", rating=3, status="approved", is_published=False)

        response = self.client.get(self.url)

        self.assertContains(response, "Очень вкусная пицца, быстро доставили!")
        self.assertNotContains(response, "Отзыв на модерации")
        self.assertNotContains(response, "Отзыв не опубликован")

    def test_book_view_empty(self):
        """Если нет замечаний, отображается заглушка."""
        self.review.delete()
        Review.objects.create(user=self.user, text="Отклонённый отзыв", rating=1, status="rejected", is_published=True)

        response = self.client.get(self.url)

        self.assertContains(response, "Пока нет замечаний")


class ReviewsLegalLayoutTests(TestCase):
    """Единый лаконичный каркас публичных страниц отзывов."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="client2", password="Sup3r-secret")
        self.review = Review.objects.create(
            user=self.user,
            text="Проверка дизайна отзывов",
            rating=4,
            status="approved",
            is_published=True,
        )

    def test_review_list_uses_legal_layout(self):
        """GET /reviews/ отдает книгу замечаний в едином каркасе."""
        response = self.client.get(reverse("app_reviews:review_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app_reviews/book.html")
        self.assertTemplateUsed(response, "app_home/legal_base.html")
        self.assertContains(response, "legal-blocks")
        self.assertContains(response, "Книга замечаний и предложений")
        self.assertContains(response, "Проверка дизайна отзывов")

    def test_review_detail_uses_legal_layout(self):
        """GET /reviews/<id>/ отдает отзыв в единообразном каркасе."""
        response = self.client.get(reverse("app_reviews:review_detail", args=[self.review.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app_reviews/review_detail.html")
        self.assertTemplateUsed(response, "app_home/legal_base.html")
        self.assertContains(response, "legal-blocks")
        self.assertContains(response, "Проверка дизайна отзывов")

    def test_add_review_requires_authentication(self):
        """Форма отзыва доступна только авторизованным пользователям."""
        response = self.client.get(reverse("app_reviews:add_review"))

        self.assertEqual(response.status_code, 302)
