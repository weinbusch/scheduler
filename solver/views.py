from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import logout_then_login
from django.forms import ModelForm, DateInput, CheckboxSelectMultiple
from django.shortcuts import render, reverse, redirect, get_object_or_404

from rest_framework import exceptions
from rest_framework import generics
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response

from solver.models import (
    DayPreference,
    Schedule,
    ScheduleException,
    Assignment,
)
from solver.serializers import DayPreferenceSerializer, AssignmentSerializer
from solver.permissions import DayPreferenceChangePermission


@login_required
def index(request):
    schedules = request.user.my_schedules.all().union(
        request.user.schedules.all(),
    )
    return render(
        request,
        "solver/index.html",
        context={"schedules": schedules},
    )


# API views


class DayPreferencesAPIView(generics.ListCreateAPIView):
    serializer_class = DayPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_schedule(self):
        pk = self.kwargs.get("pk")
        return get_object_or_404(Schedule, pk=pk)

    def check_user(self, schedule):
        if self.request.user not in schedule.users.all():
            raise exceptions.PermissionDenied

    def get_queryset(self):
        schedule = self.get_schedule()
        self.check_user(schedule)
        qs = DayPreference.objects.filter(
            schedule=schedule,
            active=True,
            user__in=schedule.users.all(),
        )
        user_id = self.request.query_params.get("user")
        if user_id is not None:
            qs = qs.filter(user_id=user_id)
        return qs

    def perform_create(self, serializer):
        schedule = self.get_schedule()
        self.check_user(schedule)
        data = serializer.validated_data
        try:
            instance = DayPreference.objects.get(
                user=data["user"], schedule=schedule, start=data["start"]
            )
        except DayPreference.DoesNotExist:
            instance = None
        serializer.instance = instance
        serializer.save(active=True, schedule=schedule)


day_preferences_api = DayPreferencesAPIView.as_view()


class DayPreferenceAPI(generics.UpdateAPIView):
    serializer_class = DayPreferenceSerializer
    queryset = DayPreference.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
        DayPreferenceChangePermission,
    ]

    def delete(self, *args, **kwargs):
        obj = self.get_object()
        obj.active = False
        obj.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


day_preference_api = DayPreferenceAPI.as_view()


class ScheduleAPIView(generics.GenericAPIView):
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


schedule_api = ScheduleAPIView.as_view()


class AssignmentAPIView(generics.ListAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_schedule(self):
        pk = self.kwargs.get("pk")
        return get_object_or_404(Schedule, pk=pk)

    def check_user(self, schedule):
        if self.request.user not in schedule.users.all():
            raise exceptions.PermissionDenied

    def get_queryset(self):
        schedule = self.get_schedule()
        self.check_user(schedule)
        qs = Assignment.objects.filter(schedule=schedule)
        return qs


assignments_api = AssignmentAPIView.as_view()


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


@login_required
def add_schedule(request):
    if request.method == "POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            return redirect(obj.get_absolute_url())
    else:
        form = ScheduleForm()
    return render(request, "solver/schedule_form.html", dict(form=form))


@login_required
def update_schedule(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if request.user != schedule.owner and request.user not in schedule.users.all():
        return render(request, "solver/unauthorized.html")
    if request.method == "POST":
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            obj = form.save()
            return redirect(obj.get_absolute_url())
    else:
        form = ScheduleForm(instance=schedule)
    return render(
        request, "solver/schedule_form.html", dict(form=form, object=schedule)
    )


@login_required
def assignments(request, pk):
    s = get_object_or_404(Schedule, pk=pk)
    if request.user != s.owner and request.user not in s.users.all():
        return render(request, "solver/unauthorized.html")
    return render(
        request,
        "solver/assignments.html",
        context=dict(schedule=s),
    )


# Auth views


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in ["username", "password"]:
            self.fields[fieldname].widget.template_name = "auth/input.html"


class LoginView(BaseLoginView):
    template_name = "auth/login.html"
    authentication_form = LoginForm


login_user = LoginView.as_view()


def logout_user(request):
    return logout_then_login(request, reverse("auth:login"))


class RegisterForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in ["username", "password1", "password2"]:
            self.fields[fieldname].widget.template_name = "auth/input.html"


def register_user(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("auth:login"))
    else:
        form = RegisterForm()
    return render(request, "auth/register.html", context=dict(form=form))
