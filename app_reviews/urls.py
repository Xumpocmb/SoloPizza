from django.urls import path
from app_reviews.views import moderate_review, moderation_list, review_list, add_review, review_detail

app_name = "app_reviews"

urlpatterns = [
    path("", review_list, name="review_list"),
    path("add/", add_review, name="add_review"),
    path("<int:pk>/", review_detail, name="review_detail"),
    path("moderation/", moderation_list, name="moderation_list"),
    path("moderate/<int:pk>/", moderate_review, name="moderate_review"),
]
