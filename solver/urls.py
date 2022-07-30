from django.urls import path, include

from solver import views

auth_patterns = [
    path("login", views.login_user, name="login"),
    path("logout", views.logout_user, name="logout"),
    path("register", views.register_user, name="register"),
]

api_patterns = [
    path("schedules/<int:pk>", views.schedule_api, name="schedule"),
    path(
        "schedules/<int:pk>/days",
        views.day_preferences_api,
        name="day_preferences",
    ),
    path(
        "days/<int:pk>",
        views.day_preference_api,
        name="day_preference",
    ),
]

urlpatterns = [
    path("", views.index, name="index"),
    path("schedules/add", views.add_schedule, name="add_schedule"),
    path("schedules/<int:pk>", views.update_schedule, name="schedule"),
    path("", include((auth_patterns, "solver"), namespace="auth")),
    path("api/", include((api_patterns, "solver"), namespace="api")),
]
