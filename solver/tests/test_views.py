import json
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from solver.models import DayPreference, Schedule
from solver.serializers import DayPreferenceSerializer

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

    def test_register_view(self):
        self.assert_get_200(reverse("register"))


@fast_password_hashing
class AuthTest(TestCase, AssertionsMixin):
    def test_post_to_register_view(self):
        data = {
            "username": "foo",
            "password1": "A12iofa_sdf!",
            "password2": "A12iofa_sdf!",
        }
        self.assert_post_302(reverse("register"), data, reverse("login"))

    def test_post_creates_user(self):
        data = {
            "username": "foo",
            "password1": "A12iofa_sdf!",
            "password2": "A12iofa_sdf!",
        }
        self.client.post(reverse("register"), data)
        self.assertEqual(User.objects.filter(username="foo").count(), 1)

    def test_post_to_register_view_invalid_data(self):
        data = {
            "username": "foo",
            "password1": "A12iofa_sdf!",
            "password2": "A12iofa",
        }
        self.assert_post_200(reverse("register"), data)

    def test_index_view_redirects_to_login(self):
        self.assert_get_302(
            reverse("index"), to=reverse("login") + "?next=" + reverse("index")
        )

    def test_get_login_view(self):
        self.assert_get_200(reverse("login"))

    def test_post_to_login_view(self):
        User.objects.create_user(username="foo", password="A12iofa_sdf")
        data = {
            "username": "foo",
            "password": "A12iofa_sdf",
        }
        self.assert_post_302(reverse("login"), data, reverse("index"))

    def test_post_to_login_view_invalid_data(self):
        User.objects.create_user(username="foo", password="A12iofa_sdf")
        data = {
            "username": "foo",
            "password": "A12iofa",
        }
        self.assert_post_200(reverse("login"), data)

    def test_get_logout_view_redirects_to_login_page(self):
        self.assert_get_302(reverse("logout"), reverse("login"))


class ViewTests(TestCase, AssertionsMixin):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="foo", password="bar")

    def setUp(self):
        self.client.force_login(self.user)

    def test_get_index(self):
        self.assert_get_200(reverse("login"))

    def test_get_add_schedule(self):
        self.assert_get_200(reverse("add_schedule"))

    def test_post_to_add_schedule(self):
        data = {
            "start": datetime.date.today(),
            "end": datetime.date.today(),
            "users": [self.user.pk],
        }
        self.assert_post_302(reverse("add_schedule"), data)

    def test_get_schedule_detail(self):
        s = Schedule.objects.create(
            start=datetime.date.today(), end=datetime.date.today()
        )
        self.assert_get_200(reverse("schedule", args=[s.pk]))

    def test_post_to_schedule_detail(self):
        s = Schedule.objects.create(
            start=datetime.date.today(), end=datetime.date.today()
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

    def test_get_schedule_solver(self):
        s = Schedule.objects.create(
            start=datetime.date.today(), end=datetime.date.today()
        )
        url = reverse("solution", args=[s.pk])
        self.assert_get_200(url)


@fast_password_hashing
class APITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        u1 = User.objects.create_user(username="foo", password="bar")
        u2 = User.objects.create_user(username="bar", password="bar")
        User.objects.create_user(username="baz", password="baz")
        DayPreference.objects.bulk_create(
            [
                DayPreference(
                    user_preferences_id=pk,
                    start=datetime.date(2022, 7, day),
                )
                for pk, day in zip([1, 1, 2, 3], [6, 7, 8, 9])
            ]
        )
        s = Schedule.objects.create(
            start=datetime.date(2022, 7, 1),
            end=datetime.date(2022, 7, 30),
        )
        s.users.set([u1, u2])
        cls.user = u1
        cls.schedule = s

    def setUp(self):
        self.client.force_login(self.user)

    def test_get_day_preferences_for_schedule(self):
        url = reverse("schedule_day_preferences", args=[self.schedule.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        expected = DayPreferenceSerializer(
            DayPreference.objects.filter(
                user_preferences__user__in=self.schedule.users.all()
            ),
            many=True,
        )
        self.assertListEqual(json.loads(r.content), expected.data)

    def test_method_not_allowed_schedule_day_preferences(self):
        url = reverse("schedule_day_preferences", args=[self.schedule.pk])
        for method in ["delete", "put", "patch", "post"]:
            with self.subTest(method=method):
                client = getattr(self.client, method)
                self.assertEqual(client(url).status_code, 405)

    def test_get_day_preferences_for_user(self):
        url = reverse("user_day_preferences")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        expected = DayPreferenceSerializer(
            DayPreference.objects.filter(user_preferences__user=self.user),
            many=True,
        )
        self.assertListEqual(json.loads(r.content), expected.data)

    def test_method_not_allowed_user_day_preferences(self):
        url = reverse("user_day_preferences")
        for method in ["delete", "put", "patch"]:
            with self.subTest(method=method):
                client = getattr(self.client, method)
                self.assertEqual(client(url).status_code, 405)

    def test_create_new_user_day_preference(self):
        url = reverse("user_day_preferences")
        data = {"start": "2022-07-08", "available": True}
        r = self.client.post(url, data=data)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(
            DayPreference.objects.filter(user_preferences__user=self.user).last().start,
            datetime.date(2022, 7, 8),
        )

    def test_delete_day_preference(self):
        url = reverse("day_preference", args=[1])
        r = self.client.delete(url)
        self.assertEqual(r.status_code, 204)
        with self.assertRaises(DayPreference.DoesNotExist):
            DayPreference.objects.get(id=1)

    def test_method_not_allowed_day_preference(self):
        url = reverse("day_preference", args=[1])
        for method in ["get", "post", "put", "patch"]:
            with self.subTest(method=method):
                client = getattr(self.client, method)
                self.assertEqual(client(url).status_code, 405)

    def test_day_preference_not_authorized(self):
        day = DayPreference.objects.get(user_preferences__user__username="bar")
        url = reverse("day_preference", args=[day.pk])
        r = self.client.delete(url)
        self.assertEqual(r.status_code, 403)
