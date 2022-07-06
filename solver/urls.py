from django.urls import path

from solver import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_user, name="login"),
    path("logout", views.logout_user, name="logout"),
    path("register", views.register_user, name="register"),
    path(
        "weekly_preferences",
        views.weekly_preferences,
        name="weekly_preferences",
    ),
    path(
        "daily_preferences",
        views.daily_preferences,
        name="daily_preferences",
    ),
]
