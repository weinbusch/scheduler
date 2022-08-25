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
    Assignment,
)
from solver.serializers import DayPreferenceSerializer, AssignmentSerializer

from .utils import fast_password_hashing

User = get_user_model()


@fast_password_hashing
class DayPreferencesAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        owner = User.objects.create_user(username="owner", password="1234")
        u1 = User.objects.create_user(username="foo", password="bar")
        u2 = User.objects.create_user(username="bar", password="bar")
        u3 = User.objects.create_user(username="baz", password="baz")
        s1 = Schedule.objects.create(
            owner=owner,
            start=datetime.date(2022, 7, 1),
            end=datetime.date(2022, 7, 30),
        )
        s1.users.set([u1, u2])
        s2 = Schedule.objects.create(owner=owner)
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
        cls.owner = owner
        cls.user = u1
        cls.schedule = s1
        cls.other = User.objects.create_user(username="other", password="1234")

    def setUp(self):
        self.client.force_login(self.user)

    def list_url(self, schedule=None):
        if schedule is None:
            schedule = self.schedule
        return reverse("api:day_preferences", args=[schedule.pk])

    def test_get_day_preferences_list(self):
        url = self.list_url()
        r = self.client.get(url)
        self.assertListEqual(
            json.loads(r.content),
            DayPreferenceSerializer(
                DayPreference.objects.filter(schedule=self.schedule),
                many=True,
            ).data,
        )

    def test_list_does_not_contain_inactive_items(self):
        DayPreference.objects.create(
            user=self.user,
            schedule=self.schedule,
            start=datetime.date.today(),
            active=False,
        )
        url = self.list_url()
        r = self.client.get(url)
        self.assertListEqual(
            json.loads(r.content),
            DayPreferenceSerializer(
                DayPreference.objects.filter(
                    schedule=self.schedule,
                    active=True,
                ),
                many=True,
            ).data,
        )

    def test_list_does_not_contain_items_from_non_members(self):
        d = DayPreference.objects.create(
            user=self.other,
            schedule=self.schedule,
            start=datetime.date.today(),
            active=True,
        )
        url = self.list_url()
        r = self.client.get(url)
        data = json.loads(r.content)
        self.assertEqual([x for x in data if x["id"] == d.id], [])

    def test_filter_list_for_user(self):
        url = self.list_url()
        r = self.client.get(url, data={"user": self.user.id})
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

    def test_block_unauthorized_access_to_list(self):
        self.client.logout()
        url = self.list_url()
        r = self.client.get(url)
        self.assertEqual(r.status_code, 403)

    def test_allow_list_access_for_members_only(self):
        url = self.list_url(Schedule.objects.get(pk=2))
        r = self.client.get(url)
        self.assertEqual(r.status_code, 403)

    def test_create_day_preference(self):
        data = {
            "user": self.user.pk,
            "schedule": self.schedule.pk,
            "start": "2022-07-30",
        }
        url = self.list_url()
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 201)
        self.assertTrue(
            DayPreference.objects.filter(
                user=self.user,
                schedule=self.schedule,
                start=datetime.date(2022, 7, 30),
            ).exists()
        )

    def test_only_allow_members_to_create(self):
        data = {
            "user": self.user.pk,
            "schedule": self.schedule.pk,
            "start": "2022-07-30",
        }
        url = self.list_url(Schedule.objects.get(pk=2))
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 403)

    def test_create_updates_active_item_if_it_exists(self):
        start = datetime.date(2022, 8, 1)
        d = DayPreference.objects.create(
            user=self.user,
            schedule=self.schedule,
            start=start,
            active=False,
        )
        data = {
            "user": self.user.pk,
            "start": str(start),
        }
        url = self.list_url()
        r = self.client.post(url, data=data)
        self.assertEqual(r.status_code, 201)
        d.refresh_from_db()
        self.assertTrue(d.active)


@fast_password_hashing
class DayPreferenceAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="owner", password="1234")
        cls.user = User.objects.create_user(username="foo", password="1234")
        cls.schedule = Schedule.objects.create(owner=cls.owner)
        cls.schedule.users.add(cls.user)

    def setUp(self):
        self.client.force_login(self.user)

    def url(self, instance):
        return reverse("api:day_preference", args=[instance.pk])

    def create_day_preference(self, **kwargs):
        data = {
            "user": self.user,
            "schedule": self.schedule,
            "start": datetime.date(2022, 7, 30),
        }
        data.update(kwargs)
        return DayPreference.objects.create(**data)

    def test_patch_day_preference_active_flag(self):
        d = self.create_day_preference()
        r = self.client.patch(
            self.url(d),
            data={"active": False},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        d.refresh_from_db()
        self.assertFalse(d.active)

    def test_only_user_can_patch(self):
        u = User.objects.create_user(username="bar", password="1234")
        self.client.force_login(u)
        d = self.create_day_preference()
        r = self.client.patch(
            self.url(d),
            data={"active": False},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 403)

    def test_delete_day_preference_sets_active_flag(self):
        d = self.create_day_preference(active=True)
        r = self.client.delete(self.url(d))
        self.assertEqual(r.status_code, 204)
        d.refresh_from_db()
        self.assertFalse(d.active)

    def test_member_of_schedule_can_also_delete(self):
        u = User.objects.create_user(username="bar", password="1234")
        self.schedule.users.add(u)
        self.client.force_login(u)
        d = self.create_day_preference()
        r = self.client.delete(self.url(d))
        self.assertEqual(r.status_code, 204)

    def test_other_users_cannot_delete(self):
        u = User.objects.create_user(username="bar", password="1234")
        self.client.force_login(u)
        d = self.create_day_preference()
        r = self.client.delete(self.url(d))
        self.assertEqual(r.status_code, 403)


@fast_password_hashing
class ScheduleAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="owner", password="1234")
        cls.schedule = Schedule.objects.create(
            owner=cls.owner,
            start=datetime.date.today(),
            end=datetime.date.today(),
        )

    def url(self, pk=None):
        if pk is None:
            pk = self.schedule.pk
        return reverse("api:schedule", args=[pk])

    def setUp(self):
        self.client.force_login(self.owner)

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


@fast_password_hashing
class AssignmentsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        owner = User.objects.create_user(username="owner", password="1234")
        u = User.objects.create(username="foo", password="123")
        s = Schedule.objects.create(owner=owner)
        s.users.add(u)
        Assignment.objects.create(
            schedule=s,
            user=u,
            start=datetime.date.today(),
        )
        cls.user = u
        cls.schedule = s

    def setUp(self):
        self.client.force_login(self.user)

    def test_get_list_of_assignments(self):
        url = reverse("api:assignments", args=[self.schedule.pk])
        r = self.client.get(url)
        data = json.loads(r.content)
        self.assertListEqual(
            data,
            AssignmentSerializer(Assignment.objects.all(), many=True).data,
        )

    def test_block_unauthorized_access_to_assignments_list(self):
        self.client.logout()
        url = reverse("api:assignments", args=[self.schedule.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 403)

    def test_only_owner_and_members_can_access_assignments(self):
        other = User.objects.create_user(username="other", password="1234")
        self.client.force_login(other)
        url = reverse("api:assignments", args=[self.schedule.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 403)
