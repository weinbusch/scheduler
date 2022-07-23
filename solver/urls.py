from django.urls import path

from solver import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_user, name="login"),
    path("logout", views.logout_user, name="logout"),
    path("register", views.register_user, name="register"),
    path(
        "user/day_preferences",
        views.user_day_preferences,
        name="user_day_preferences",
    ),
    path(
        "schedules/<int:pk>/day_preferences",
        views.schedule_day_preferences,
        name="schedule_day_preferences",
    ),
    path(
        "day_preferences/<int:pk>",
        views.day_preference,
        name="day_preference",
    ),
    path("schedules", views.add_schedule, name="add_schedule"),
    path("schedules/<int:pk>", views.update_schedule, name="schedule"),
    path("schedules/<int:pk>/solution", views.solve_schedule, name="solution"),
    path("schedules/<int:pk>/assignments", views.assignments, name="assignments"),
]
