from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import logout_then_login
from django.shortcuts import render, reverse, redirect

from rest_framework import generics
from rest_framework import mixins

from solver.models import UserPreferences, DayPreference
from solver.serializers import DayPreferenceSerializer
from solver.permissions import DayPreferenceChangePermission


@login_required
def index(request):
    return render(request, "solver/index.html")


class DayPreferencesListAPIView(generics.ListCreateAPIView):
    serializer_class = DayPreferenceSerializer

    def get_queryset(self):
        user = self.request.user
        return DayPreference.objects.filter(user_preferences__user=user)

    def perform_create(self, serializer):
        user = self.request.user
        prefs = UserPreferences.objects.get(user=user)
        return serializer.save(user_preferences=prefs)


day_preferences = DayPreferencesListAPIView.as_view()


class DayPreferenceUpdateDeleteAPIView(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    generics.GenericAPIView,
):
    serializer_class = DayPreferenceSerializer
    queryset = DayPreference.objects.all()
    permission_classes = [DayPreferenceChangePermission]

    def patch(self, *args, **kwargs):
        return self.partial_update(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.destroy(*args, **kwargs)


day_preference = DayPreferenceUpdateDeleteAPIView.as_view()


class LoginView(BaseLoginView):
    template_name = "auth/login.html"


login_user = LoginView.as_view()


def logout_user(request):
    return logout_then_login(request, reverse("login"))


def register_user(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("login"))
    else:
        form = UserCreationForm()
    return render(request, "auth/register.html", context=dict(form=form))
