import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase

from solver.models import DayPreference, Schedule, Assignment
from solver.serializers import DayPreferenceSerializer, AssignmentSerializer

from .utils import fast_password_hashing

User = get_user_model()


@fast_password_hashing
class SerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="foo", password="1234")
        cls.schedule = Schedule.objects.create()

    def test_day_preference_serializer(self):
        date = datetime.date(2022, 7, 20)
        d = DayPreference.objects.create(
            user=self.user,
            schedule=self.schedule,
            start=date,
        )
        serializer = DayPreferenceSerializer(d)
        self.assertDictEqual(
            serializer.data,
            {
                "id": 1,
                "user": self.user.pk,
                "username": self.user.username,
                "schedule": self.schedule.pk,
                "start": "2022-07-20",
                "active": True,
                "url": d.get_absolute_url(),
            },
        )

    def test_save_day_preference_serializer(self):
        data = {
            "user": self.user.id,
            "start": "2022-07-21",
        }
        s = DayPreferenceSerializer(data=data)
        self.assertTrue(s.is_valid())
        s.save(schedule=self.schedule)
        self.assertEquals(
            DayPreference.objects.filter(
                user=self.user,
                schedule=self.schedule,
                start=datetime.date(
                    2022,
                    7,
                    21,
                ),
            ).count(),
            1,
        )

    def test_update_day_preference_serializer(self):
        instance = DayPreference.objects.create(
            user=self.user,
            schedule=self.schedule,
            start=datetime.date.today(),
            active=True,
        )
        data = {"active": False}
        s = DayPreferenceSerializer(instance=instance, partial=True, data=data)
        self.assertTrue(s.is_valid())
        s.save()
        instance.refresh_from_db()
        self.assertFalse(instance.active)


@fast_password_hashing
class AssignmentSerializerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="foo", password="1234")
        cls.schedule = Schedule.objects.create()

    def test_assignment_serializer(self):
        date = datetime.date(2022, 7, 20)
        a = Assignment.objects.create(
            user=self.user,
            schedule=self.schedule,
            start=date,
        )
        serializer = AssignmentSerializer(a)
        self.assertDictEqual(
            serializer.data,
            {
                "id": 1,
                "user": self.user.pk,
                "username": self.user.username,
                "schedule": self.schedule.pk,
                "start": "2022-07-20",
            },
        )
