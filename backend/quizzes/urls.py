from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register("quizzes", views.QuizView)


urlpatterns = [
    path("", include(router.urls)),
    path("search/", views.QuizSearchView.as_view(), name="quiz-search"),
]