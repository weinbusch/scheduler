import pytest
import datetime

from django.contrib.auth import get_user_model
from django.urls import reverse

from solver.models import user_to_domain
from solver.repository import ScheduleRepository
from solver.domain import Schedule

User = get_user_model()

repo = ScheduleRepository()


@pytest.fixture(autouse=True)
def fast_password_hashing(settings):
    # https://pytest-django.readthedocs.io/en/latest/configuring_django.html#overriding-individual-settings
    # https://docs.djangoproject.com/en/4.0/topics/testing/overview/#password-hashing
    settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]


def assert_template_used(response, name):
    assert name in [t.name for t in response.templates]


@pytest.fixture
def django_user(django_user_model):
    return django_user_model.objects.create_user(username="user", password="1234")


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_user(username="owner", password="1234")


@pytest.fixture
def authenticated_client(client, django_user):
    client.force_login(django_user)
    return client


def test_get_schedule_list(authenticated_client):
    r = authenticated_client.get(reverse("index"))
    assert r.status_code == 200
    assert r.context["schedules"] == []
    assert_template_used(r, "solver/index.html")


def test_schedule_list_unauthenticated(client):
    r = client.get(reverse("index"))
    assert r.status_code == 302


def test_new_schedule_view(authenticated_client):
    r = authenticated_client.get(reverse("add_schedule"))
    assert r.status_code == 200
    assert_template_used(r, "solver/schedule_form.html")


def test_new_schedule_view_unauthenticated(client):
    r = client.get(reverse("add_schedule"))
    assert r.status_code == 302


def test_new_schedule_view_post_creates_schedule(authenticated_client, django_user):
    data = {
        "start": datetime.date(2022, 1, 1),
        "end": datetime.date(2022, 1, 7),
        "exclude_weekends": True,
    }
    r = authenticated_client.post(reverse("add_schedule"), data)
    assert r.status_code == 302
    [schedule] = repo.list()
    assert schedule.id is not None
    assert schedule.owner.id == django_user.id


@pytest.mark.parametrize(
    "url_name, template_name",
    [
        ("schedule_settings", "solver/schedule_settings.html"),
        ("schedule_preferences", "solver/schedule_preferences.html"),
        ("schedule_assignments", "solver/schedule_assignments.html"),
    ],
)
def test_schedule_views(url_name, template_name, authenticated_client, django_user):
    s = Schedule(owner=user_to_domain(django_user))
    repo.add(s)
    r = authenticated_client.get(reverse(url_name, args=[s.id]))
    assert r.status_code == 200
    assert_template_used(r, template_name)


@pytest.mark.parametrize(
    "url_name",
    ["schedule_settings", "schedule_preferences", "schedule_assignments"],
)
def test_schedule_views_unauthenticated(url_name, client, django_user):
    s = Schedule(owner=user_to_domain(django_user))
    repo.add(s)
    r = client.get(reverse(url_name, args=[s.id]))
    assert r.status_code == 302


@pytest.mark.parametrize(
    "url_name",
    ["schedule_settings", "schedule_preferences", "schedule_assignments"],
)
def test_schedule_views_unauthorized(url_name, authenticated_client, owner):
    s = Schedule(owner=user_to_domain(owner))
    repo.add(s)
    r = authenticated_client.get(reverse(url_name, args=[s.id]))
    assert r.status_code == 200
    assert_template_used(r, "solver/unauthorized.html")
