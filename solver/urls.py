from django.urls import path

from solver import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_user, name="login"),
    path("logout", views.logout_user, name="logout"),
    path("register", views.register_user, name="register"),
    path(
        "day_preferences",
        views.day_preferences,
        name="day_preferences",
    ),
    path(
        "day_preference/<int:pk>",
        views.day_preference,
        name="day_preference",
    ),
    path("add_schedule", views.add_schedule, name="add_schedule"),
    path("schedule/<int:pk>", views.update_schedule, name="schedule"),
]
