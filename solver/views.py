from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import logout_then_login
from django.forms import ModelForm, DateInput, CheckboxSelectMultiple
from django.shortcuts import render, reverse, redirect, get_object_or_404

from rest_framework import permissions
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.response import Response

from solver.models import (
    DayPreference,
    Schedule,
    ScheduleException,
)
from solver.serializers import DayPreferenceSerializer, AssignmentSerializer


# API views


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def day_preferences_api(request, pk):
    try:
        schedule = Schedule.objects.get(pk=pk)
    except Schedule.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.user != schedule.owner and request.user not in schedule.users.all():
        return Response(status=status.HTTP_403_FORBIDDEN)

    if request.method == "POST":
        serializer = DayPreferenceSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                instance = DayPreference.objects.get(
                    user=data["user"],
                    schedule=schedule,
                    start=data["start"],
                )
            except DayPreference.DoesNotExist:
                instance = None
            serializer.instance = instance
            serializer.save(active=True, schedule=schedule)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    preferences = DayPreference.objects.filter(
        schedule=schedule,
        active=True,
        user__in=schedule.users.all(),
    )
    user_id = request.query_params.get("user")
    if user_id is not None:
        preferences = preferences.filter(user_id=user_id)
    serializer = DayPreferenceSerializer(preferences, many=all)
    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def day_preference_api(request, pk):
    try:
        preference = DayPreference.objects.get(pk=pk)
    except DayPreference.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if (
        request.user != preference.user
        and request.user != preference.schedule.owner
        and request.user not in preference.schedule.users.all()
    ):
        return Response(status=status.HTTP_403_FORBIDDEN)

    if request.method == "DELETE":
        preference.active = False
        preference.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def schedule_api(request, pk):
    try:
        schedule = Schedule.objects.get(pk=pk)
    except Schedule.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.user != schedule.owner and request.user not in schedule.users.all():
        return Response(status=status.HTTP_403_FORBIDDEN)

    try:
        schedule.solve()
    except ScheduleException as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def assignments_api(request, pk):
    try:
        schedule = Schedule.objects.get(pk=pk)
    except Schedule.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.user != schedule.owner and request.user not in schedule.users.all():
        return Response(status=status.HTTP_403_FORBIDDEN)
    assignments = schedule.assignments.all()
    serializer = AssignmentSerializer(assignments, many=all)
    return Response(serializer.data)


# Schedule views


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
def schedule_settings(request, pk):
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
        request, "solver/schedule_settings.html", dict(form=form, object=schedule)
    )


@login_required
def schedule_preferences(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if request.user != schedule.owner and request.user not in schedule.users.all():
        return render(request, "solver/unauthorized.html")
    return render(request, "solver/schedule_preferences.html", dict(object=schedule))


@login_required
def schedule_assignments(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if request.user != schedule.owner and request.user not in schedule.users.all():
        return render(request, "solver/unauthorized.html")
    return render(request, "solver/schedule_assignments.html", dict(object=schedule))


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
