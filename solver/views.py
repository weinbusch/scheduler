from django.shortcuts import render, reverse, redirect

from django.contrib.auth.forms import UserCreationForm


def register_user(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("register"))
    else:
        form = UserCreationForm()
    return render(request, "auth/register.html", context=dict(form=form))
