import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from solver.models import DayPreference, Schedule, Assignment
from solver.serializers import DayPreferenceSerializer, AssignmentSerializer

from .utils import fast_password_hashing

User = get_user_model()


@fast_password_hashing
class SerializerTests(TestCase):
    def test_day_preference_serializer(self):
        date = datetime.date(2022, 7, 20)
        u = User.objects.create(username="foo", password="1234")
        d = DayPreference.objects.create(
            user_preferences=u.user_preferences,
            start=date,
        )
        s = DayPreferenceSerializer(d)
        self.assertDictEqual(
            s.data,
            {
                "id": 1,
                "username": "foo",
                "start": "2022-07-20",
                "url": reverse("day_preference", args=[d.pk]),
            },
        )

    def test_assignment_serializer(self):
        d = datetime.date(2022, 7, 20)
        u = User.objects.create_user(username="foo", password="1234")
        s = Schedule.objects.create(start=d, end=d)
        a = Assignment.objects.create(schedule=s, user=u, start=d)
        self.assertDictEqual(
            AssignmentSerializer(a).data,
            {
                "id": a.id,
                "username": u.username,
                "start": "2022-07-20",
            },
        )
