import datetime
from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase
from django.contrib.auth import get_user_model

from solver.models import DayPreference, Schedule

from .utils import fast_password_hashing

User = get_user_model()


class TestDayPreference(TestCase):
    def test_day_preference_date_user_unique(self):
        s = datetime.date(2022, 7, 11)
        DayPreference.objects.create(user_preferences_id=99, start=s)
        with self.assertRaises(IntegrityError):
            DayPreference.objects.create(user_preferences_id=99, start=s)


@fast_password_hashing
class TestUserPreferences(TestCase):
    def test_user_creation_also_creates_user_preferences(self):
        u = User.objects.create_user(username="bar", password="1234")
        self.assertIsNotNone(u.user_preferences)

    def test_available_dates(self):
        u = User.objects.create_user(username="bar", password="1234")
        p = u.user_preferences
        DayPreference.objects.bulk_create(
            [
                DayPreference(
                    user_preferences=p,
                    start=datetime.date(2022, 7, day),
                )
                for day in [3, 5, 7]
            ]
        )
        self.assertListEqual(
            p.get_available_dates(
                start=datetime.date(2022, 7, 4),
                end=datetime.date(2022, 7, 6),
            ),
            [datetime.date(2022, 7, 5)],
        )


@fast_password_hashing
class TestSchedule(TestCase):
    def test_schedule_start_end_date(self):
        Schedule.objects.create(
            start=datetime.date(2022, 7, 12),
            end=datetime.date(2022, 8, 12),
        )

    def test_schedule_users_many_to_many(self):
        u1 = User.objects.create_user(username="foo", password="1234")
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

    def test_schedule_solve_calls_solver(self):
        s = Schedule.objects.create(
            start=datetime.date.today(), end=datetime.date.today()
        )
        with patch("solver.models.get_schedule") as solver_function:
            s.solve()
            solver_function.assert_called_once()

    def test_schedule_solve_calls_solver_with_correct_arguments(self):
        s = Schedule.objects.create(
            start=datetime.date(2022, 7, 21),
            end=datetime.date(2022, 7, 22),
        )
        u1 = User.objects.create_user(username="foo", password="1234")
        u2 = User.objects.create_user(username="bar", password="1234")
        DayPreference.objects.bulk_create(
            [
                DayPreference(
                    user_preferences=u.user_preferences,
                    start=datetime.date(2022, 7, day),
                )
                for u, day in zip([u1, u2], [21, 22])
            ]
        )
        s.users.set([u1, u2])
        with patch("solver.models.get_schedule") as solver_function:
            s.solve()
            solver_function.assert_called_with(
                [datetime.date(2022, 7, day) for day in [21, 22]],
                {
                    u: u.user_preferences.get_available_dates(s.start, s.end)
                    for u in [u1, u2]
                },
            )
