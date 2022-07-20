from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import logout_then_login
from django.forms import ModelForm, DateInput, CheckboxSelectMultiple
from django.shortcuts import render, reverse, redirect
from django.views.generic import CreateView, UpdateView, DetailView

from rest_framework import generics
from rest_framework import mixins
from rest_framework import permissions

from solver.models import UserPreferences, DayPreference, Schedule
from solver.serializers import DayPreferenceSerializer
from solver.permissions import DayPreferenceChangePermission


@login_required
def index(request):
    return render(request, "solver/index.html")


class UserDayPreferencesListAPIView(generics.ListCreateAPIView):
    serializer_class = DayPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return DayPreference.objects.filter(user_preferences__user=user)

    def perform_create(self, serializer):
        user = self.request.user
        prefs = UserPreferences.objects.get(user=user)
        return serializer.save(user_preferences=prefs)


user_day_preferences = UserDayPreferencesListAPIView.as_view()


class ScheduleDayPreferencesListView(generics.ListAPIView):
    serializer_class = DayPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        pk = self.kwargs["pk"]
        schedule = Schedule.objects.get(pk=pk)
        return DayPreference.objects.filter(
            user_preferences__user__in=schedule.users.all()
        )


schedule_day_preferences = ScheduleDayPreferencesListView.as_view()


class DayPreferenceDeleteAPIView(generics.DestroyAPIView):
    serializer_class = DayPreferenceSerializer
    queryset = DayPreference.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
        DayPreferenceChangePermission,
    ]


day_preference = DayPreferenceDeleteAPIView.as_view()


class ScheduleForm(ModelForm):
    class Meta:
        model = Schedule
        fields = ["start", "end", "users"]
        widgets = {
            "start": DateInput(attrs={"class": "p-2 border w-full leading-tight"}),
            "end": DateInput(attrs={"class": "p-2 border w-full leading-tight"}),
            "users": CheckboxSelectMultiple,
        }


class ScheduleCreateView(LoginRequiredMixin, CreateView):
    model = Schedule
    form_class = ScheduleForm


add_schedule = ScheduleCreateView.as_view()


class ScheduleUpdateView(LoginRequiredMixin, UpdateView):
    model = Schedule
    form_class = ScheduleForm


update_schedule = ScheduleUpdateView.as_view()


class ScheduleSolveView(LoginRequiredMixin, DetailView):
    model = Schedule
    template_name = "solver/solution.html"


solve_schedule = ScheduleSolveView.as_view()


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in ["username", "password"]:
            self.fields[fieldname].widget.attrs.update(
                {"class": "p-2 border w-full leading-tight"}
            )


class LoginView(BaseLoginView):
    template_name = "auth/login.html"
    authentication_form = LoginForm


login_user = LoginView.as_view()


def logout_user(request):
    return logout_then_login(request, reverse("login"))


class RegisterForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in ["username", "password1", "password2"]:
            self.fields[fieldname].widget.attrs.update(
                {"class": "p-2 border w-full leading-tight"}
            )


def register_user(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("login"))
    else:
        form = RegisterForm()
    return render(request, "auth/register.html", context=dict(form=form))
