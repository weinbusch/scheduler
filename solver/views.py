from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import logout_then_login
from django.forms import ModelForm, DateInput, CheckboxSelectMultiple
from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView

from rest_framework import generics
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response

from solver.models import (
    DayPreference,
    Schedule,
    Assignment,
    ScheduleException,
)
from solver.serializers import DayPreferenceSerializer, AssignmentSerializer
from solver.permissions import DayPreferenceChangePermission


@login_required
def index(request):
    return render(request, "solver/index.html")


# API views


def parse_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


class DayPreferencesAPIView(generics.ListAPIView):
    serializer_class = DayPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = DayPreference.objects.all()

        schedule_id = parse_int(self.request.query_params.get("schedule_id"))
        if schedule_id is not None:
            if not self.request.user.schedules.filter(id=schedule_id).exists():
                qs = qs.none()
            qs = qs.filter(schedule_id=schedule_id)

        user_id = parse_int(self.request.query_params.get("user_id"))
        if user_id is not None:
            if user_id != self.request.user.id and schedule_id is None:
                qs = qs.none()
            qs = qs.filter(user_id=user_id)

        return qs


day_preferences = DayPreferencesAPIView.as_view()


class UserDayPreferencesListAPIView(generics.ListCreateAPIView):
    serializer_class = DayPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return DayPreference.objects.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        return serializer.save(user=user)


user_day_preferences = UserDayPreferencesListAPIView.as_view()


class ScheduleDayPreferencesListView(generics.ListAPIView):
    serializer_class = DayPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        pk = self.kwargs["pk"]
        schedule = get_object_or_404(Schedule, pk=pk)
        return DayPreference.objects.filter(user__in=schedule.users.all())


schedule_day_preferences = ScheduleDayPreferencesListView.as_view()


class DayPreferenceDeleteAPIView(generics.DestroyAPIView):
    serializer_class = DayPreferenceSerializer
    queryset = DayPreference.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
        DayPreferenceChangePermission,
    ]


day_preference = DayPreferenceDeleteAPIView.as_view()


class AssignmentsAPIView(generics.ListAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        pk = self.kwargs["pk"]
        schedule = get_object_or_404(Schedule, pk=pk)
        return Assignment.objects.filter(schedule=schedule)


assignments = AssignmentsAPIView.as_view()


class SolveScheduleAPIView(generics.GenericAPIView):
    queryset = Schedule.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, *args, **kwargs):
        schedule = self.get_object()
        try:
            schedule.solve()
        except ScheduleException as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


solve_schedule = SolveScheduleAPIView.as_view()


# Schedule views


class ScheduleForm(ModelForm):
    class Meta:
        model = Schedule
        fields = ["start", "end", "users"]
        widgets = {
            "start": DateInput(
                attrs={"class": "p-2 border w-full leading-tight"},
            ),
            "end": DateInput(
                attrs={"class": "p-2 border w-full leading-tight"},
            ),
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


# Auth views


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
