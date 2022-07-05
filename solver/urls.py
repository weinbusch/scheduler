from django.urls import path

from solver import views

urlpatterns = [
    path("register", views.register_user, name="register"),
]
