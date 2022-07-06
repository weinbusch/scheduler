from django.urls import path

from solver import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_user, name="login"),
    path("register", views.register_user, name="register"),
]
