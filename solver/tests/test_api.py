import json
import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from solver.models import (
    DayPreference,
    Schedule,
    ScheduleException,
)
from solver.serializers import DayPreferenceSerializer

from .utils import fast_password_hashing

User = get_user_model()


@fast_password_hashing
class DayPreferencesAPITests(TestCase):
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
        s2.users.set([u2, u3])
        DayPreference.objects.bulk_create(
            [
                DayPreference(
                    user=u,
                    schedule=s,
                    start=datetime.date(2022, 7, day),
                )
                for u, s, day in zip(
                    [u1, u1, u2, u2, u3],
                    [s1, s1, s1, s2, s2],
                    [6, 7, 8, 9, 9],
                )
            ]
        )
        cls.user = u1
        cls.schedule = s1

    def setUp(self):
        self.client.force_login(self.user)

    def list_url(self, pk):
        return reverse("api:day_preferences", args=[pk])

    def test_get_day_preferences_api_list_view(self):
        url = self.list_url(self.schedule.pk)
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertListEqual(
            json.loads(r.content),
            DayPreferenceSerializer(
                DayPreference.objects.filter(schedule=self.schedule),
                many=True,
            ).data,
        )

    def test_filter_user(self):
        url = self.list_url(self.schedule.pk)
        r = self.client.get(url, data={"user": self.user.id})
        self.assertEqual(r.status_code, 200)
        self.assertListEqual(
            json.loads(r.content),
            DayPreferenceSerializer(
                DayPreference.objects.filter(
                    schedule=self.schedule,
                    user=self.user,
                ),
                many=True,
            ).data,
        )

    def test_day_preference_unauthorized(self):
        url = self.list_url(self.schedule.pk)
        self.client.logout()
        r = self.client.get(url)
        self.assertEqual(r.status_code, 403)

    def test_only_members_can_get_day_preferences_from_schedule(self):
        url = self.list_url(2)
        r = self.client.get(url)
        self.assertEqual(r.status_code, 403)

    def test_create_day_preference(self):
        url = self.list_url(self.schedule.pk)
        data = {
            "user": self.user.pk,
            "schedule": self.schedule.pk,
            "start": "2022-07-30",
        }
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 201)
        self.assertTrue(
            DayPreference.objects.filter(
                user=self.user,
                schedule=self.schedule,
                start=datetime.date(2022, 7, 30),
            ).exists()
        )

    def test_only_members_can_create(self):
        url = self.list_url(2)
        data = {
            "user": self.user.pk,
            "schedule": self.schedule.pk,
            "start": "2022-07-30",
        }
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 403)

    def test_delete_day_preference(self):
        url = reverse("api:day_preference", args=[1])
        r = self.client.delete(url)
        self.assertEqual(r.status_code, 204)
        with self.assertRaises(DayPreference.DoesNotExist):
            DayPreference.objects.get(id=1)

    def test_only_user_can_delete_day_preference(self):
        day = DayPreference.objects.filter(user__username="bar").first()
        url = reverse("api:day_preference", args=[day.pk])
        r = self.client.delete(url)
        self.assertEqual(r.status_code, 403)


@fast_password_hashing
class ScheduleAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="foo", password="1234")
        cls.schedule = Schedule.objects.create(
            start=datetime.date.today(), end=datetime.date.today()
        )

    def url(self, pk=None):
        if pk is None:
            pk = self.schedule.pk
        return reverse("api:schedule", args=[pk])

    def setUp(self):
        self.client.force_login(self.user)

    def test_patch_schedule_calls_solve(self):
        url = self.url()
        with patch.object(Schedule, "solve") as solve_function:
            r = self.client.patch(url)
            self.assertEqual(r.status_code, 204)
            solve_function.assert_called_once()

    def test_patch_schedule_not_found(self):
        url = self.url(99)
        r = self.client.patch(url)
        self.assertEqual(r.status_code, 404)

    def test_patch_schedule_not_authorized(self):
        url = self.url()
        self.client.logout()
        r = self.client.patch(url)
        self.assertEqual(r.status_code, 403)

    def test_patch_schedule_captures_specific_exception(self):
        url = self.url()
        with patch.object(
            Schedule,
            "solve",
            side_effect=ScheduleException("foo"),
        ):
            r = self.client.patch(url)
            self.assertEqual(r.status_code, 500)
            self.assertDictEqual(json.loads(r.content), {"error": "foo"})

    def test_patch_schedule_raises_unspecific_exception(self):
        url = self.url()
        with patch.object(
            Schedule,
            "solve",
            side_effect=Exception,
        ):
            with self.assertRaises(Exception):
                self.client.patch(url)
