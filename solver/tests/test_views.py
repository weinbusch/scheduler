import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from solver.models import Schedule

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

    def test_add_schedule_view(self):
        r = self.client.get(reverse("add_schedule"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "solver/schedule_form.html")

    def test_unauthorized_add_schedule_redirects_to_login(self):
        self.client.logout()
        r = self.client.get(reverse("add_schedule"))
        self.assertRedirects(
            r, reverse("auth:login") + "?next=" + reverse("add_schedule")
        )

    def test_post_to_add_schedule(self):
        data = {
            "start": datetime.date.today(),
            "end": datetime.date.today(),
            "users": [self.user.pk],
        }
        r = self.client.post(reverse("add_schedule"), data)
        self.assertEqual(r.status_code, 302)

    def test_create_schedule_with_users(self):
        data = {
            "start": "2022-01-01",
            "end": "2022-12-31",
            "users": [self.user.pk],
        }
        self.client.post(reverse("add_schedule"), data)
        s = Schedule.objects.get(
            start=datetime.date(2022, 1, 1), end=datetime.date(2022, 12, 31)
        )
        self.assertEqual(s.users.first(), self.user)

    def test_user_is_set_as_schedule_owner(self):
        data = {
            "start": datetime.date.today(),
            "end": datetime.date.today(),
            "users": [self.user.pk],
        }
        self.client.post(reverse("add_schedule"), data)
        schedule = Schedule.objects.first()
        self.assertEqual(self.user, schedule.owner)

    def test_schedule_settings(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date.today(),
            end=datetime.date.today(),
        )
        r = self.client.get(reverse("schedule_settings", args=[s.pk]))
        self.assertTemplateUsed(r, "solver/schedule_settings.html")

    def test_save_schedule_settings(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date.today(),
            end=datetime.date.today(),
        )
        data = dict(
            start="2022-10-01",
            end="2022-10-11",
            users=[],
        )
        r = self.client.post(reverse("schedule_settings", args=[s.pk]), data)
        self.assertEqual(r.status_code, 302)
        s.refresh_from_db()
        self.assertEqual(s.start, datetime.date(2022, 10, 1))
        self.assertEqual(s.end, datetime.date(2022, 10, 11))

    def test_get_schedule_preferences(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date.today(),
            end=datetime.date.today(),
        )
        r = self.client.get(reverse("schedule_preferences", args=[s.pk]))
        self.assertTemplateUsed(r, "solver/schedule_preferences.html")

    def test_get_schedule_assignments(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date.today(),
            end=datetime.date.today(),
        )
        r = self.client.get(reverse("schedule_assignments", args=[s.pk]))
        self.assertTemplateUsed(r, "solver/schedule_assignments.html")

    def test_access_to_schedule_granted_to_members(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date.today(),
            end=datetime.date.today(),
        )
        s.users.add(self.other)
        self.client.force_login(self.other)
        for name in [
            "schedule_settings",
            "schedule_preferences",
            "schedule_assignments",
        ]:
            with self.subTest(name=name):
                url = reverse(name, args=[s.pk])
                r = self.client.get(url)
                self.assertEqual(r.status_code, 200)

    def test_access_to_schedule_restricted_to_owner_and_members(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date.today(),
            end=datetime.date.today(),
        )
        self.client.force_login(self.other)
        for name in [
            "schedule_settings",
            "schedule_preferences",
            "schedule_assignments",
        ]:
            with self.subTest(name=name):
                url = reverse(name, args=[s.pk])
                r = self.client.get(url)
                self.assertTemplateUsed(r, "solver/unauthorized.html")

    def test_unauthorized_access_to_schedule_is_redirected(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date.today(),
            end=datetime.date.today(),
        )
        self.client.logout()
        for name in [
            "schedule_settings",
            "schedule_preferences",
            "schedule_assignments",
        ]:
            with self.subTest(name=name):
                url = reverse(name, args=[s.pk])
                r = self.client.get(url)
                self.assertRedirects(r, reverse("auth:login") + "?next=" + url)
