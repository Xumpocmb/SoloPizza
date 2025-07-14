from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Review
from .forms import ReviewForm, ReviewModerationForm
from django.contrib.auth.decorators import permission_required


def review_list(request):
    reviews = Review.objects.filter(is_published=True, status="approved").select_related("user")
    return render(request, "app_reviews/review_list.html", {"reviews": reviews})


def review_detail(request, pk):
    review = get_object_or_404(Review, pk=pk, is_published=True)
    return render(request, "app_reviews/review_detail.html", {"review": review})


@login_required
def add_review(request):
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            messages.success(request, "Ваш отзыв отправлен на модерацию! Мы его опубликуем, как только он пройдет проверку!")
            return redirect("app_reviews:review_list")
    else:
        form = ReviewForm()

    return render(request, "app_reviews/add_review.html", {"form": form})


@permission_required("app_reviews.can_moderate")
def moderation_list(request):
    reviews = Review.objects.filter(status="pending").order_by("created_at")
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "app_reviews/moderation_list.html",
        {
            "page_obj": page_obj,
        },
    )


@permission_required("app_reviews.can_moderate")
def moderate_review(request, pk):
    review = get_object_or_404(Review, pk=pk)

    if request.method == "POST":
        form = ReviewModerationForm(request.POST, instance=review)

        if form.is_valid():
            review = form.save(commit=False)
            review.moderator = request.user
            review.moderation_date = timezone.now()
            review.save()

            messages.success(request, "Отзыв успешно отмодерирован")
            return redirect("app_reviews:moderation_list")
    else:
        form = ReviewModerationForm(instance=review)

    return render(
        request,
        "app_reviews/moderate_review.html",
        {
            "review": review,
            "form": form,
        },
    )
