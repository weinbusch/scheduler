from django.urls import path, include

from solver import views

auth_patterns = [
    path("login", views.login_user, name="login"),
    path("logout", views.logout_user, name="logout"),
    path("register", views.register_user, name="register"),
]

api_patterns = [
    path(
        "schedules/<int:pk>",
        views.schedule_api,
        name="schedule",
    ),
    path(
        "schedules/<int:pk>/days",
        views.schedule_days_api,
        name="schedule_days",
    ),
    path(
        "schedules/<int:pk>/preferences",
        views.schedule_preferences_api,
        name="schedule_preferences",
    ),
    path(
        "schedules/<int:pk>/assignments",
        views.schedule_assignments_api,
        name="schedule_assignments",
    ),
]

schedule_patterns = [
    path("add", views.add_schedule, name="add_schedule"),
    path(
        "<int:pk>/settings",
        views.schedule_settings,
        name="schedule_settings",
    ),
    path(
        "<int:pk>/preferences",
        views.schedule_preferences,
        name="schedule_preferences",
    ),
    path(
        "<int:pk>/assignments",
        views.schedule_assignments,
        name="schedule_assignments",
    ),
    path(
        "<int:pk>/delete",
        views.delete_schedule,
        name="delete_schedule",
    ),
    path(
        "<int:pk>/participants/delete",
        views.delete_participant,
        name="delete_participant",
    ),
]

urlpatterns = [
    path("", views.schedule_list, name="index"),
    path("schedules/", include(schedule_patterns)),
    path("auth/", include((auth_patterns, "solver"), namespace="auth")),
    path("api/", include((api_patterns, "solver"), namespace="api")),
]
