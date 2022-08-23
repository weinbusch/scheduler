import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from solver.models import Schedule, Assignment

from .utils import fast_password_hashing

User = get_user_model()


class AssertionsMixin:
    def assert_get_200(self, path):
        r = self.client.get(path)
        self.assertEqual(r.status_code, 200)

    def assert_get_302(self, path, to):
        r = self.client.get(path)
        self.assertRedirects(r, to)

    def assert_post_200(self, path, data):
        r = self.client.post(path, data)
        self.assertEqual(r.status_code, 200)

    def assert_post_302(self, path, data, to=None):
        r = self.client.post(path, data)
        if to is not None:
            self.assertRedirects(r, to)
        else:
            self.assertEqual(r.status_code, 302)


@fast_password_hashing
class AuthTest(TestCase, AssertionsMixin):
    def test_get_register_view(self):
        self.assert_get_200(reverse("auth:register"))

    def test_post_to_register_view(self):
        data = {
            "username": "foo",
            "password1": "A12iofa_sdf!",
            "password2": "A12iofa_sdf!",
        }
        self.assert_post_302(reverse("auth:register"), data, reverse("auth:login"))

    def test_post_creates_user(self):
        data = {
            "username": "foo",
            "password1": "A12iofa_sdf!",
            "password2": "A12iofa_sdf!",
        }
        self.client.post(reverse("auth:register"), data)
        self.assertEqual(User.objects.filter(username="foo").count(), 1)

    def test_post_to_register_view_invalid_data(self):
        data = {
            "username": "foo",
            "password1": "A12iofa_sdf!",
            "password2": "A12iofa",
        }
        self.assert_post_200(reverse("auth:register"), data)

    def test_get_login_view(self):
        self.assert_get_200(reverse("auth:login"))

    def test_post_to_login_view(self):
        User.objects.create_user(username="foo", password="A12iofa_sdf")
        data = {
            "username": "foo",
            "password": "A12iofa_sdf",
        }
        self.assert_post_302(reverse("auth:login"), data, reverse("index"))

    def test_post_to_login_view_invalid_data(self):
        User.objects.create_user(username="foo", password="A12iofa_sdf")
        data = {
            "username": "foo",
            "password": "A12iofa",
        }
        self.assert_post_200(reverse("auth:login"), data)

    def test_get_logout_view_redirects_to_login_page(self):
        self.assert_get_302(reverse("auth:logout"), reverse("auth:login"))


@fast_password_hashing
class ViewTests(TestCase, AssertionsMixin):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="owner", password="1234")
        cls.other = User.objects.create_user(username="other", password="1234")

    def setUp(self):
        self.client.force_login(self.user)

    def test_unauthorized_index_view_redirects_to_login(self):
        self.client.logout()
        self.assert_get_302(
            reverse("index"), to=reverse("auth:login") + "?next=" + reverse("index")
        )

    def test_get_index(self):
        self.assert_get_200(reverse("index"))

    def test_index_view_lists_owned_and_assigned_schedules(self):
        Schedule.objects.create(owner=self.user)
        s2 = Schedule.objects.create(owner=self.other)
        s2.users.add(self.user)
        r = self.client.get(reverse("index"))
        self.assertListEqual(
            [s.id for s in r.context["schedules"]],
            [s.id for s in Schedule.objects.all()],
        )

    def test_index_view_does_not_list_other_schedules(self):
        Schedule.objects.create(owner=self.other)
        r = self.client.get(reverse("index"))
        self.assertEqual(r.context["schedules"].count(), 0)

    def test_get_add_schedule(self):
        self.assert_get_200(reverse("add_schedule"))

    def test_unauthorized_add_schedule_redirects_to_login(self):
        self.client.logout()
        self.assert_get_302(
            reverse("add_schedule"),
            to=reverse("auth:login") + "?next=" + reverse("add_schedule"),
        )

    def test_post_to_add_schedule(self):
        data = {
            "start": datetime.date.today(),
            "end": datetime.date.today(),
            "users": [self.user.pk],
        }
        self.assert_post_302(reverse("add_schedule"), data)

    def test_user_is_set_as_schedule_owner(self):
        data = {
            "start": datetime.date.today(),
            "end": datetime.date.today(),
            "users": [self.user.pk],
        }
        self.client.post(reverse("add_schedule"), data)
        schedule = Schedule.objects.first()
        self.assertEqual(self.user, schedule.owner)

    def test_get_schedule_detail(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date.today(),
            end=datetime.date.today(),
        )
        self.assert_get_200(reverse("schedule", args=[s.pk]))

    def test_unauthorized_schedule_detail_redirects_to_login(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date.today(),
            end=datetime.date.today(),
        )
        url = reverse("schedule", args=[s.pk])
        self.client.logout()
        self.assert_get_302(url, to=reverse("auth:login") + "?next=" + url)

    def test_only_owner_and_members_can_access_schedule_view(self):
        s = Schedule.objects.create(owner=self.other)
        r = self.client.get(s.get_absolute_url())
        self.assertTemplateUsed(r, "solver/unauthorized.html")

    def test_post_to_schedule_detail(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date.today(),
            end=datetime.date.today(),
        )
        url = reverse("schedule", args=[s.pk])
        self.assert_post_302(
            url,
            {
                "start": datetime.date.today(),
                "end": datetime.date.today(),
                "users": [],
            },
            to=url,
        )

    def test_view_assignments(self):
        s = Schedule.objects.create(
            owner=self.user,
        )
        s.users.add(self.user)
        Assignment.objects.create(
            schedule=s,
            user=self.user,
            start=datetime.date.today(),
        )
        url = reverse("assignments", args=[s.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

    def test_only_owner_and_members_can_access_assignments(self):
        s = Schedule.objects.create(owner=self.other)
        r = self.client.get(reverse("assignment", args=[s.pk]))
        self.assertTemplateUsed(r, "solver/unauthorized.html")

    def test_view_assignments_unauthorized(self):
        self.client.logout()
        s = Schedule.objects.create(
            owner=self.user,
        )
        s.users.add(self.user)
        Assignment.objects.create(
            schedule=s,
            user=self.user,
            start=datetime.date.today(),
        )
        url = reverse("assignments", args=[s.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)
