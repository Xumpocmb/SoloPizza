from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from .models import Review


class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(widget=forms.HiddenInput(), validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        model = Review
        fields = ["text", "rating"]
        widgets = {
            "text": forms.Textarea(attrs={"class": "form-textarea review-textarea", "placeholder": "Напишите ваш отзыв...", "rows": 4}),
        }
        labels = {"text": "Ваш отзыв", "rating": "Ваша оценка"}


class ReviewModerationForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["status", "moderation_comment"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "moderation_comment": forms.Textarea(attrs={"class": "form-textarea", "rows": 3, "placeholder": "Причина отклонения (если необходимо)"}),
        }
        labels = {
            "status": "Статус модерации",
            "moderation_comment": "Комментарий модератора",
        }
