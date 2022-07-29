import unittest
import json
import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from solver.models import DayPreference, Schedule, Assignment, ScheduleException
from solver.serializers import DayPreferenceSerializer, AssignmentSerializer

from .utils import fast_password_hashing

User = get_user_model()


@fast_password_hashing
class APITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        u1 = User.objects.create_user(username="foo", password="bar")
        u2 = User.objects.create_user(username="bar", password="bar")
        u3 = User.objects.create_user(username="baz", password="baz")
        s1 = Schedule.objects.create(
            start=datetime.date(2022, 7, 1),
            end=datetime.date(2022, 7, 30),
        )
        s1.users.set([u1, u2])
        s2 = Schedule.objects.create()
        s2.users.set([u1, u3])
        DayPreference.objects.bulk_create(
            [
                DayPreference(
                    user=u,
                    schedule=s,
                    start=datetime.date(2022, 7, day),
                )
                for u, s, day in zip(
                    [u1, u1, u2, u1, u3],
                    [s1, s1, s1, s2, s2],
                    [6, 7, 8, 9, 9],
                )
            ]
        )
        cls.user = u1
        cls.schedule = s1

    def setUp(self):
        self.client.force_login(self.user)

    def test_get_day_preferences_api_list_view(self):
        url = reverse("day_preferences")
        test_data = [
            {},
            {"user_id": self.user.pk},
            {"schedule_id": self.schedule.pk},
            {"user_id": self.user.pk, "schedule_id": self.schedule.pk},
        ]
        for query_args in test_data:
            with self.subTest(query_args=query_args):
                r = self.client.get(url, data=query_args)
                self.assertEqual(r.status_code, 200)
                self.assertListEqual(
                    json.loads(r.content),
                    DayPreferenceSerializer(
                        DayPreference.objects.filter(**query_args),
                        many=True,
                    ).data,
                )

    def test_get_day_preferences_for_schedule_404(self):
        url = reverse("schedule_day_preferences", args=[99])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 404)

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
            DayPreference.objects.filter(user=self.user),
            many=True,
        )
        self.assertListEqual(json.loads(r.content), expected.data)

    def test_method_not_allowed_user_day_preferences(self):
        url = reverse("user_day_preferences")
        for method in ["delete", "put", "patch"]:
            with self.subTest(method=method):
                client = getattr(self.client, method)
                self.assertEqual(client(url).status_code, 405)

    @unittest.skip("")
    def test_create_new_user_day_preference(self):
        url = reverse("user_day_preferences")
        data = {"start": "2022-07-08", "available": True}
        r = self.client.post(url, data=data)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(
            DayPreference.objects.filter(user=self.user).last().start,
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
        day = DayPreference.objects.get(user__username="bar")
        url = reverse("day_preference", args=[day.pk])
        r = self.client.delete(url)
        self.assertEqual(r.status_code, 403)


@fast_password_hashing
class AssignmentTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="foo", password="1234")
        cls.schedule = Schedule.objects.create(
            start=datetime.date.today(), end=datetime.date.today()
        )
        Assignment.objects.create(
            schedule=cls.schedule,
            user=cls.user,
            start=datetime.date.today(),
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_get_assignment_list(self):
        s = self.schedule
        url = reverse("assignments", args=[s.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        expected = AssignmentSerializer(
            Assignment.objects.filter(schedule=s), many=True
        )
        self.assertListEqual(json.loads(r.content), expected.data)

    def test_get_assignments_404(self):
        url = reverse("assignments", args=[99])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 404)

    def test_get_assignment_unauthorized(self):
        self.client.logout()
        url = reverse("assignments", args=[1])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 403)


@fast_password_hashing
class ScheduleTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="foo", password="1234")
        cls.schedule = Schedule.objects.create(
            start=datetime.date.today(), end=datetime.date.today()
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_patch_calls_schedule_solve(self):
        url = reverse("solve_schedule", args=[self.schedule.pk])
        with patch.object(Schedule, "solve") as solve_function:
            r = self.client.patch(url)
            self.assertEqual(r.status_code, 204)
            solve_function.assert_called_once()

    def test_method_not_allowed(self):
        url = reverse("solve_schedule", args=[self.schedule.pk])
        for method in ["get", "delete", "put", "post"]:
            with self.subTest(method=method):
                client = getattr(self.client, method)
                self.assertEqual(client(url).status_code, 405)

    def test_schedule_not_found(self):
        url = reverse("solve_schedule", args=[99])
        r = self.client.patch(url)
        self.assertEqual(r.status_code, 404)

    def test_not_authorized(self):
        self.client.logout()
        url = reverse("solve_schedule", args=[self.schedule.pk])
        r = self.client.patch(url)
        self.assertEqual(r.status_code, 403)

    def test_solve_raises_exception(self):
        url = reverse("solve_schedule", args=[self.schedule.pk])
        with patch.object(
            Schedule,
            "solve",
            side_effect=ScheduleException("foo"),
        ):
            r = self.client.patch(url)
            self.assertEqual(r.status_code, 500)
            self.assertDictEqual(json.loads(r.content), {"error": "foo"})

    def test_unspecific_exception(self):
        url = reverse("solve_schedule", args=[self.schedule.pk])
        with patch.object(
            Schedule,
            "solve",
            side_effect=Exception,
        ):
            with self.assertRaises(Exception):
                self.client.patch(url)
