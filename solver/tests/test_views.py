import pytest
import datetime

from django.contrib.auth import get_user_model
from django.urls import reverse

from solver.models import user_to_domain
from solver.repository import ScheduleRepository
from solver.domain import Schedule
from solver.views import ScheduleNavigation

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


def test_get_schedule_list(authenticated_client, django_user):
    for d in range(10):
        schedule = Schedule(owner=user_to_domain(django_user))
        repo.add(schedule)
    r = authenticated_client.get(reverse("index"))
    assert r.status_code == 200
    assert len(r.context["schedules"]) == 10
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
        "exclude_weekends": False,
    }
    r = authenticated_client.post(reverse("add_schedule"), data)
    assert r.status_code == 302
    [schedule] = repo.list_all()
    assert schedule.id is not None
    assert schedule.owner.id == django_user.id
    assert schedule.days == {datetime.date(2022, 1, x) for x in range(1, 7)}


def test_navigation_object(django_user):
    s = Schedule(owner=user_to_domain(django_user))
    s = repo.add(s)
    navigation = ScheduleNavigation(s, "schedule_settings")
    assert [x for x in navigation] == [
        ("Einstellungen", reverse("schedule_settings", args=[s.id]), True),
        ("Teilnehmer", reverse("schedule_preferences", args=[s.id]), False),
        ("Verteilung", reverse("schedule_assignments", args=[s.id]), False),
    ]


@pytest.mark.parametrize(
    "url_name, template_name",
    [
        ("schedule_settings", "solver/schedule_settings.html"),
        ("schedule_preferences", "solver/schedule_preferences.html"),
        ("schedule_assignments", "solver/schedule_assignments.html"),
    ],
)
def test_schedule_detail_views(
    url_name, template_name, authenticated_client, django_user
):
    s = Schedule(owner=user_to_domain(django_user))
    repo.add(s)
    r = authenticated_client.get(reverse(url_name, args=[s.id]))
    assert r.status_code == 200
    assert_template_used(r, template_name)


def test_edit_schedule_assignment_settings(authenticated_client, django_user):
    s = Schedule(owner=user_to_domain(django_user), window=1)
    s = repo.add(s)
    assert s.window == 1
    data = {"window": 3}
    r = authenticated_client.post(
        reverse("schedule_assignments", args=[s.id]), data=data
    )
    assert r.status_code == 302
    t = repo.get(s.id)
    assert t.window == 3


def test_edit_schedule_settings_clears_assignments(authenticated_client, django_user):
    s = Schedule(owner=user_to_domain(django_user), window=1)
    s.add_preference("foo", datetime.date(2022, 1, 1))
    s.add_assignment("foo", datetime.date(2022, 1, 1))
    s = repo.add(s)
    data = {"window": 3}
    authenticated_client.post(reverse("schedule_assignments", args=[s.id]), data=data)
    s = repo.get(s.id)
    assert s.assignments == set()


def test_delete_schedule(authenticated_client, django_user):
    s = Schedule(owner=user_to_domain(django_user))
    s = repo.add(s)
    r = authenticated_client.get(reverse("delete_schedule", args=[s.id]))
    assert r.status_code == 200
    assert_template_used(r, "solver/delete_schedule.html")
    r = authenticated_client.post(reverse("delete_schedule", args=[s.id]))
    assert r.status_code == 302
    assert repo.list_all() == []


def test_add_participant(authenticated_client, django_user):
    s = Schedule(
        owner=user_to_domain(django_user),
        start=datetime.date(2022, 1, 1),
        end=datetime.date(2022, 1, 8),
    )
    repo.add(s)
    r = authenticated_client.post(
        reverse("schedule_preferences", args=[s.id]),
        data={"name": "foo", "weekdays": [0, 5]},
    )
    assert r.status_code == 302
    s = repo.get(s.id)
    assert "foo" in s.participants
    assert len(s.preferences["foo"]) == 2


def test_delete_participant(authenticated_client, django_user):
    s = Schedule(owner=user_to_domain(django_user))
    s.add_participant("foo")
    s.add_participant("bar")
    s = repo.add(s)
    url = reverse("delete_participant", args=[s.id])
    r = authenticated_client.post(url, data={"participant": "foo"})
    assert r.status_code == 302
    s = repo.get(s.id)
    assert "foo" not in s.participants


@pytest.mark.parametrize(
    "url_name",
    ["schedule_settings", "schedule_preferences", "schedule_assignments"],
)
def test_schedule_views_not_found(url_name, client, django_user):
    client.force_login(django_user)
    r = client.get(reverse(url_name, args=[1]))
    assert r.status_code == 404


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
