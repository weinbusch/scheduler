import json
import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from solver.models import DayPreference, Schedule, Assignment
from solver.serializers import DayPreferenceSerializer, AssignmentSerializer

from .utils import fast_password_hashing

User = get_user_model()


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
        with patch.object(Schedule, "solve", side_effect=Exception):
            r = self.client.patch(url)
            self.assertEqual(r.status_code, 500)
