import json

from django.http import JsonResponse, HttpResponseNotFound, HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import logout_then_login
from django.shortcuts import render, reverse, redirect

from solver.models import user_to_domain
from solver.repository import ScheduleRepository
from solver.domain import Schedule, ScheduleException
from solver.forms import (
    DateForm,
    PreferenceForm,
    ScheduleCreateForm,
    ParticipantForm,
    ScheduleSettingsForm,
)

repo = ScheduleRepository()


def has_access_to_schedule(user, schedule):
    return user.is_superuser or user.id == schedule.owner.id


# API views


def api_not_authorized():
    return JsonResponse({"error": "not authorized"}, status=403)


def api_not_found():
    return JsonResponse({"error": "not found"}, status=404)


def api_method_not_allowed():
    return JsonResponse({"error": "method not allowed"}, status=405)


def api_no_content():
    return JsonResponse({}, status=204)


def api_server_error(error):
    return JsonResponse({"error": str(error)}, status=500)


def api_bad_request(errors):
    return JsonResponse({"error": errors}, status=400)


def api_login_required(view):
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return api_not_authorized()
        return view(request, *args, **kwargs)

    return wrapped_view


def api_get_schedule(view):
    def wrapped_view(request, pk, *args, **kwargs):
        schedule = repo.get(pk)
        if schedule is None:
            return api_not_found()
        if not has_access_to_schedule(request.user, schedule):
            return api_not_authorized()
        return view(request, schedule, *args, **kwargs)

    return wrapped_view


def get_json_data(request):
    return json.loads(request.body)


@api_get_schedule
def schedule_api(request, schedule):
    if request.method == "GET":
        data = {
            "days": [{"start": d} for d in sorted(schedule.days)],
            "preferences": [
                {"participant": p, "start": d}
                for p, dates in sorted(schedule.preferences.items())
                for d in sorted(dates)
            ],
            "assignments": [
                {"participant": p, "start": d} for p, d in sorted(schedule.assignments)
            ],
        }
        return JsonResponse(data)
    if request.method == "PATCH":
        try:
            schedule.make_assignments()
        except ScheduleException as e:
            return api_server_error(e)
        finally:
            repo.add(schedule)
        return api_no_content()
    return api_method_not_allowed()


@api_login_required
@api_get_schedule
def schedule_days_api(request, schedule):
    if request.method == "GET":
        data = [{"start": d} for d in sorted(schedule.days)]
        return JsonResponse(data, safe=False)
    if request.method in ["PATCH", "DELETE"]:
        data = get_json_data(request)
        form = DateForm(data)
        if form.is_valid():
            if request.method == "DELETE":
                schedule.remove_day(**form.cleaned_data)
            else:
                schedule.add_day(**form.cleaned_data)
            repo.add(schedule)
            return api_no_content()
        return api_bad_request(form.errors)
    return api_method_not_allowed()


@api_login_required
@api_get_schedule
def schedule_preferences_api(request, schedule):
    if request.method == "GET":
        data = [
            {"participant": p, "start": d}
            for p, dates in sorted(schedule.preferences.items())
            for d in sorted(dates)
        ]
        return JsonResponse(data, safe=False)
    if request.method in ["PATCH", "DELETE"]:
        data = get_json_data(request)
        form = PreferenceForm(data)
        if form.is_valid():
            if request.method == "DELETE":
                schedule.remove_preference(**form.cleaned_data)
            else:
                schedule.add_preference(**form.cleaned_data)
            repo.add(schedule)
            return api_no_content()
        return api_bad_request(form.errors)
    return api_method_not_allowed()


@api_login_required
@api_get_schedule
def schedule_assignments_api(request, schedule):
    data = [{"participant": p, "start": d} for p, d in sorted(schedule.assignments)]
    return JsonResponse(data, safe=False)


# Schedule views


class ScheduleNavigation:

    navigation_items = [
        ("Einstellungen", "schedule_settings"),
        ("Teilnehmer", "schedule_preferences"),
        ("Verteilung", "schedule_assignments"),
    ]

    def __init__(self, schedule, url_name):
        self._items = [
            (label, reverse(name, args=[schedule.id]), name == url_name)
            for label, name in self.navigation_items
        ]

    def __iter__(self):
        return self._items.__iter__()


def schedule_view(view):
    def wrapped_view(request, pk):
        schedule = repo.get(pk)
        if schedule is None:
            return HttpResponseNotFound()
        if not has_access_to_schedule(request.user, schedule):
            return render(request, "solver/unauthorized.html")
        return view(request, schedule)

    return wrapped_view


@login_required
def schedule_list(request):
    if request.user.is_superuser:
        schedules = repo.list_all()
    else:
        schedules = repo.list(request.user.id)
    return render(
        request,
        "solver/index.html",
        context={"schedules": schedules},
    )


@login_required
def add_schedule(request):
    if request.method == "POST":
        form = ScheduleCreateForm(request.POST)
        if form.is_valid():
            s = Schedule(owner=user_to_domain(request.user), **form.cleaned_data)
            s = repo.add(s)
            return redirect(reverse("schedule_settings", args=[s.id]))
    else:
        form = ScheduleCreateForm()
    return render(request, "solver/schedule_form.html", dict(form=form))


@login_required
@schedule_view
def schedule_settings(request, schedule):
    return render(
        request,
        "solver/schedule_settings.html",
        dict(
            schedule=schedule,
            navigation=ScheduleNavigation(schedule, "schedule_settings"),
        ),
    )


@login_required
@schedule_view
def delete_schedule(request, schedule):
    if request.method == "POST":
        repo.delete(schedule)
        return redirect(reverse("index"))
    return render(
        request,
        "solver/delete_schedule.html",
        dict(
            schedule=schedule,
            navigation=ScheduleNavigation(schedule, ""),
        ),
    )


@login_required
@schedule_view
def schedule_preferences(request, schedule):
    if request.method == "POST":
        form = ParticipantForm(request.POST, participants=schedule.participants)
        if form.is_valid():
            schedule.add_participant(**form.cleaned_data)
            repo.add(schedule)
            return redirect(reverse("schedule_preferences", args=[schedule.id]))
    else:
        form = ParticipantForm(participants=schedule.participants)
    return render(
        request,
        "solver/schedule_preferences.html",
        dict(
            schedule=schedule,
            form=form,
            navigation=ScheduleNavigation(schedule, "schedule_preferences"),
        ),
    )


@login_required
@schedule_view
def schedule_assignments(request, schedule):
    if request.method == "POST":
        form = ScheduleSettingsForm(request.POST)
        if form.is_valid():
            schedule.window = form.cleaned_data["window"]
            schedule.clear_assignments()
            repo.add(schedule)
            return redirect(reverse("schedule_assignments", args=[schedule.id]))
    else:
        form = ScheduleSettingsForm(initial={"window": schedule.window})
    return render(
        request,
        "solver/schedule_assignments.html",
        dict(
            schedule=schedule,
            navigation=ScheduleNavigation(schedule, "schedule_assignments"),
            form=form,
        ),
    )


@login_required
@schedule_view
def delete_participant(request, schedule):
    if request.method == "POST":
        name = request.POST.get("participant", None)
        schedule.remove_participant(name)
        repo.add(schedule)
        return redirect(reverse("schedule_preferences", args=[schedule.id]))
    return HttpResponseNotAllowed(["POST"])


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
