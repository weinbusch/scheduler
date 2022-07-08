from django.shortcuts import render, reverse, redirect

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import logout_then_login
from django.http import JsonResponse
from django.forms import ModelForm

from solver.models import UserPreferences


@login_required
def index(request):
    return render(request, "solver/index.html")


class UserPreferencesForm(ModelForm):
    class Meta:
        model = UserPreferences
        exclude = ["user", "allowed_days", "excluded_days"]


@login_required
def weekly_preferences(request):
    p = UserPreferences.objects.get(user=request.user)
    if request.method == "POST":
        form = UserPreferencesForm(request.POST, instance=p)
        if form.is_valid():
            form.save()
            return redirect(reverse("index"))
    else:
        form = UserPreferencesForm(instance=p)
    return render(
        request,
        "solver/weekly_preferences.html",
        context=dict(form=form),
    )


@login_required
def day_preferences(request, pk):
    return JsonResponse({"group_id": pk})


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
