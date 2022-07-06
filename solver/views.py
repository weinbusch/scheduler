from django.shortcuts import render, reverse, redirect

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import logout_then_login


@login_required
def index(request):
    return render(request, "solver/index.html")


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
