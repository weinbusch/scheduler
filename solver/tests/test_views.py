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
        cls.user = User.objects.create_user(username="foo", password="bar")

    def setUp(self):
        self.client.force_login(self.user)

    def test_unauthorized_index_view_redirects_to_login(self):
        self.client.logout()
        self.assert_get_302(
            reverse("index"), to=reverse("auth:login") + "?next=" + reverse("index")
        )

    def test_get_index(self):
        self.assert_get_200(reverse("index"))

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

    def test_get_schedule_detail(self):
        s = Schedule.objects.create(
            start=datetime.date.today(), end=datetime.date.today()
        )
        self.assert_get_200(reverse("schedule", args=[s.pk]))

    def test_unauthorized_schedule_detail_redirects_to_login(self):
        s = Schedule.objects.create(
            start=datetime.date.today(), end=datetime.date.today()
        )
        url = reverse("schedule", args=[s.pk])
        self.client.logout()
        self.assert_get_302(url, to=reverse("auth:login") + "?next=" + url)

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
