import math
import json
import unittest
import datetime
import collections

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse

from solver.solver import get_schedule
from solver.models import DayPreference, Schedule

User = get_user_model()


class SchedulerTest(unittest.TestCase):
    def test_each_day_is_assigned_one_family(self):
        """Test a simple case with two families and four days"""
        days = [
            datetime.date.today(),
            datetime.date.today() + datetime.timedelta(days=1),
            datetime.date.today() + datetime.timedelta(days=2),
            datetime.date.today() + datetime.timedelta(days=3),
        ]
        families = ["foo", "bar"]
        available_dates = {f: days for f in families}
        schedule = get_schedule(days, families, available_dates)
        self.assertTrue(all([f in families for _, f in schedule]))

    def test_equal_number_of_assignements(self):
        """Test each family is assigned an equal number of days"""
        n = 100
        families = ["foo", "bar", "baz", "bak"]
        days = [
            datetime.date.today() + datetime.timedelta(days=x)
            for x in range(len(families) * n)
        ]
        available_dates = {f: days for f in families}
        schedule = get_schedule(days, families, available_dates)
        counts = collections.Counter([f for _, f in schedule])
        self.assertTrue(all([counts[f] == n for f in families]))

    def test_uneven_number_of_days(self):
        """Test with 2 families and 3 days"""
        days = [datetime.date.today() + datetime.timedelta(days=x) for x in range(3)]
        families = ["foo", "bar"]
        available_dates = {f: days for f in families}
        schedule = get_schedule(days, families, available_dates)
        counts = collections.Counter([f for _, f in schedule])
        self.assertTrue(
            (counts["foo"] == 2 and counts["bar"] == 1)
            or (counts["foo"] == 1 and counts["bar"] == 2)
        )

    def test_no_family_more_than_two_less_than_maximum(self):
        """If the number of days is not dividable by the number of families,
        no family should have less than floor(days/families) number of
        assignments

        """
        for n in range(9, 12):
            with self.subTest(n=n):
                families = ["foo", "bar", "baz"]
                days = [
                    datetime.date.today() + datetime.timedelta(days=x) for x in range(n)
                ]
                available_dates = {f: days for f in families}
                schedule = get_schedule(days, families, available_dates)
                counts = collections.Counter([f for _, f in schedule])
                self.assertTrue(
                    all([counts[f] >= math.floor(n / len(families)) for f in families])
                )

    def test_with_constraints(self):
        """First family is only available on the first and last day"""
        days = [
            datetime.date.today(),
            datetime.date.today() + datetime.timedelta(days=1),
            datetime.date.today() + datetime.timedelta(days=2),
            datetime.date.today() + datetime.timedelta(days=3),
        ]
        families = ["foo", "bar"]
        available_dates = {"foo": [days[0], days[3]], "bar": days}
        schedule = get_schedule(days, families, available_dates)
        self.assertListEqual([f for _, f in schedule], ["foo", "bar", "bar", "foo"])

    def test_infeasible_constraints(self):
        """First family is only available on a single day"""
        days = [
            datetime.date.today(),
            datetime.date.today() + datetime.timedelta(days=1),
            datetime.date.today() + datetime.timedelta(days=2),
            datetime.date.today() + datetime.timedelta(days=3),
        ]
        families = ["foo", "bar"]
        available_dates = {"foo": [days[0]], "bar": days}
        with self.assertRaises(Exception):
            get_schedule(days, families, available_dates)


class ModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="foo", password="1234")

    def test_user_creation_also_creates_user_preferences(self):
        self.assertIsNotNone(self.user.user_preferences)

    def test_day_preference_available(self):
        p = DayPreference.objects.create(
            user_preferences=self.user.user_preferences,
            start=datetime.date.today(),
        )
        self.assertTrue(p.available)

    def test_day_preferences_unique_date(self):
        p = self.user.user_preferences
        s = datetime.date(2022, 7, 11)
        DayPreference.objects.create(user_preferences=p, start=s)
        with self.assertRaises(IntegrityError):
            DayPreference.objects.create(user_preferences=p, start=s)

    def test_available_dates(self):
        p = self.user.user_preferences
        d = datetime.date(2022, 7, 3)
        days = [d + datetime.timedelta(days=delta) for delta in [0, 2, 4]]
        DayPreference.objects.bulk_create(
            [DayPreference(user_preferences=p, start=day) for day in days]
        )
        self.assertListEqual(
            p.get_available_dates(
                start=datetime.date(2022, 7, 4), end=datetime.date(2022, 7, 6)
            ),
            [datetime.date(2022, 7, 5)],
        )

    def test_schedule_start_end_date(self):
        Schedule.objects.create(
            start=datetime.date(2022, 7, 12),
            end=datetime.date(2022, 8, 12),
        )

    def test_schedule_users_many_to_many(self):
        u1 = self.user
        u2 = User.objects.create_user(username="bar", password="1234")
        Schedule.objects.create(
            start=datetime.date(2022, 7, 12),
            end=datetime.date(2022, 8, 12),
        ).users.set([u1, u2])
        Schedule.objects.create(
            start=datetime.date(2022, 7, 12), end=datetime.date(2022, 8, 12)
        ).users.set([u1])
        self.assertEqual(u1.schedules.count(), 2)
        self.assertEqual(u2.schedules.count(), 1)

    def test_schedule_days(self):
        s = Schedule(
            start=datetime.date(2022, 7, 11),  # a monday
            end=datetime.date(2022, 7, 18),  # the next monday
        )
        self.assertListEqual(
            s.days(),
            [datetime.date(2022, 7, x) for x in [11, 12, 13, 14, 15, 18]],
        )

    def test_schedule_solve(self):
        u1 = User.objects.create(username="bar", password="1234")
        u2 = User.objects.create(username="baz", password="1234")
        user_sequence = [u1, u1, u2, u2, u1, u2]
        s = Schedule.objects.create(
            start=datetime.date(2022, 7, 11),  # a monday
            end=datetime.date(2022, 7, 18),  # the next monday
        )
        days = s.days()
        s.users.set([u1, u2])
        DayPreference.objects.bulk_create(
            [
                DayPreference(user_preferences=u.user_preferences, start=s)
                for u, s in zip(user_sequence, days)
            ]
        )
        self.assertListEqual(
            [
                {"start": d, "title": u.username}
                for d, u in zip(
                    days,
                    user_sequence,
                )
            ],
            s.solve(),
        )


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


# https://docs.djangoproject.com/en/4.0/topics/testing/overview/#password-hashing
@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]
)
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


class APITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        u1 = User.objects.create_user(username="foo", password="bar")
        u2 = User.objects.create_user(username="bar", password="bar")
        u3 = User.objects.create_user(username="baz", password="baz")
        DayPreference.objects.bulk_create(
            [
                DayPreference(
                    user_preferences=u1.user_preferences,
                    start=datetime.date(2022, 7, 6),
                    available=True,
                ),
                DayPreference(
                    user_preferences=u1.user_preferences,
                    start=datetime.date(2022, 7, 7),
                    available=False,
                ),
                DayPreference(
                    user_preferences=u2.user_preferences,
                    start=datetime.date(2022, 7, 8),
                    available=True,
                ),
                DayPreference(
                    user_preferences=u3.user_preferences,
                    start=datetime.date(2022, 7, 9),
                    available=True,
                ),
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
        self.assertListEqual(
            json.loads(r.content),
            [
                {
                    "id": 1,
                    "username": "foo",
                    "start": "2022-07-06",
                    "available": True,
                    "url": reverse("day_preference", args=[1]),
                },
                {
                    "id": 2,
                    "username": "foo",
                    "start": "2022-07-07",
                    "available": False,
                    "url": reverse("day_preference", args=[2]),
                },
                {
                    "id": 3,
                    "username": "bar",
                    "start": "2022-07-08",
                    "available": True,
                    "url": reverse("day_preference", args=[3]),
                },
            ],
        )

    def test_get_user_day_preferences(self):
        url = reverse("user_day_preferences")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertListEqual(
            json.loads(r.content),
            [
                {
                    "id": 1,
                    "username": "foo",
                    "start": "2022-07-06",
                    "available": True,
                    "url": reverse("day_preference", args=[1]),
                },
                {
                    "id": 2,
                    "username": "foo",
                    "start": "2022-07-07",
                    "available": False,
                    "url": reverse("day_preference", args=[2]),
                },
            ],
        )

    def test_post_to_day_preferences(self):
        url = reverse("user_day_preferences")
        data = {"start": "2022-07-08", "available": True}
        r = self.client.post(url, data=data)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(
            DayPreference.objects.last().start,
            datetime.date(2022, 7, 8),
        )

    def test_method_not_allowed_day_preference_list(self):
        url = reverse("user_day_preferences")
        for method in ["delete", "put", "patch"]:
            with self.subTest(method=method):
                client = getattr(self.client, method)
                self.assertEqual(client(url).status_code, 405)

    def test_update_day_preference(self):
        url = reverse("day_preference", args=[1])
        data = {"id": 1, "start": "2022-07-06", "available": False}
        r = self.client.patch(url, data=data, content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(DayPreference.objects.get(id=1).available)

    def test_delete_day_preference(self):
        url = reverse("day_preference", args=[1])
        r = self.client.delete(url)
        self.assertEqual(r.status_code, 204)
        with self.assertRaises(DayPreference.DoesNotExist):
            DayPreference.objects.get(id=1)

    def test_day_preference_not_authorized(self):
        day = DayPreference.objects.get(user_preferences__user__username="bar")
        url = reverse("day_preference", args=[day.pk])
        r = self.client.delete(url)
        self.assertEqual(r.status_code, 403)

    def test_day_reference_read_only_id(self):
        data = {
            "id": 99,
            "start": datetime.date(1900, 7, 6),
            "available": True,
        }
        url = reverse("day_preference", args=[1])
        self.client.patch(url, data=data, content_type="application/json")
        self.assertEqual(DayPreference.objects.filter(id=99).count(), 0)
        self.assertEqual(
            DayPreference.objects.get(pk=1).start, datetime.date(1900, 7, 6)
        )

    def test_day_preference_404(self):
        url = reverse("day_preference", args=[99])
        r = self.client.patch(
            url,
            data={
                "id": 99,
                "start": datetime.date(1900, 1, 1),
                "available": True,
            },
        )
        self.assertEqual(r.status_code, 404)
