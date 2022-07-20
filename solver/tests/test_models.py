import datetime

from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

from solver.models import DayPreference, Schedule

User = get_user_model()

# https://docs.djangoproject.com/en/4.0/topics/testing/overview/#password-hashing
fast_password_hashing = override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]
)


@fast_password_hashing
class TestUserPreferences(TestCase):
    def test_user_creation_also_creates_user_preferences(self):
        u = User.objects.create_user(username="bar", password="1234")
        self.assertIsNotNone(u.user_preferences)


@fast_password_hashing
class ModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="foo", password="1234")

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
