import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from solver.models import (
    DayPreference,
    Schedule,
    ScheduleException,
    Assignment,
    get_available_dates,
)


from .utils import fast_password_hashing

User = get_user_model()


@fast_password_hashing
class TestDayPreference(TestCase):
    @classmethod
    def setUpTestData(cls):
        u = User.objects.create_user(username="owner", password="1234")
        s = Schedule.objects.create(owner=u)
        cls.user = u
        cls.schedule = s

    def test_day_preference_date_user_schedule_unique(self):
        s = datetime.date(2022, 7, 11)
        DayPreference.objects.create(user_id=1, schedule_id=1, start=s)
        DayPreference.objects.create(user_id=1, schedule_id=2, start=s)
        DayPreference.objects.create(user_id=2, schedule_id=1, start=s)
        DayPreference.objects.create(
            user_id=1, schedule_id=1, start=s + datetime.timedelta(days=1)
        )
        with self.assertRaises(IntegrityError):
            DayPreference.objects.create(user_id=1, schedule_id=1, start=s)

    def test_available_dates(self):
        DayPreference.objects.bulk_create(
            [
                DayPreference(
                    user=self.user,
                    schedule=self.schedule,
                    start=datetime.date(2022, 7, day),
                )
                for day in [3, 5, 7]
            ]
        )
        self.assertListEqual(
            get_available_dates(
                self.user,
                self.schedule,
                datetime.date(2022, 7, 4),
                datetime.date(2022, 7, 6),
            ),
            [datetime.date(2022, 7, 5)],
        )

    def test_available_dates_excludes_inactive_dates(self):
        DayPreference.objects.bulk_create(
            [
                DayPreference(
                    user=self.user,
                    schedule=self.schedule,
                    start=datetime.date(2022, 7, day),
                    active=active,
                )
                for day, active in zip(
                    range(1, 8), [True, True, True, True, False, False, False]
                )
            ]
        )
        self.assertListEqual(
            get_available_dates(
                self.user,
                self.schedule,
                datetime.date(2022, 7, 1),
                datetime.date(2022, 7, 7),
            ),
            [d.start for d in DayPreference.objects.filter(active=True)],
        )


@fast_password_hashing
class TestSchedule(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="owner", password="1234")

    def test_schedule_start_end_date(self):
        Schedule.objects.create(
            owner=self.user,
            start=datetime.date(2022, 7, 12),
            end=datetime.date(2022, 8, 12),
        )

    def test_schedule_users_many_to_many(self):
        u1 = User.objects.create_user(username="foo", password="1234")
        u2 = User.objects.create_user(username="bar", password="1234")
        Schedule.objects.create(
            owner=self.user,
            start=datetime.date(2022, 7, 12),
            end=datetime.date(2022, 8, 12),
        ).users.set([u1, u2])
        Schedule.objects.create(
            owner=self.user,
            start=datetime.date(2022, 7, 12),
            end=datetime.date(2022, 8, 12),
        ).users.set([u1])
        self.assertEqual(u1.schedules.count(), 2)
        self.assertEqual(u2.schedules.count(), 1)

    def test_schedule_owner(self):
        u = User.objects.create_user(username="bar", password="1234")
        s = Schedule.objects.create(
            owner=u,
            start=datetime.date(2022, 7, 12),
            end=datetime.date(2022, 8, 12),
        )
        self.assertEqual(u.my_schedules.first(), s)

    def test_schedule_days(self):
        s = Schedule(
            owner=self.user,
            start=datetime.date(2022, 7, 11),  # a monday
            end=datetime.date(2022, 7, 18),  # the next monday
        )
        self.assertListEqual(
            s.days(),
            [datetime.date(2022, 7, x) for x in [11, 12, 13, 14, 15, 18]],
        )

    def test_schedule_solve_calls_solver(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date.today(),
            end=datetime.date.today(),
        )
        with patch("solver.models.get_schedule") as solver_function:
            s.solve()
            solver_function.assert_called_once()

    def test_schedule_solve_calls_solver_with_correct_arguments(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date(2022, 7, 21),
            end=datetime.date(2022, 7, 22),
        )
        u1 = User.objects.create_user(username="foo", password="1234")
        u2 = User.objects.create_user(username="bar", password="1234")
        DayPreference.objects.bulk_create(
            [
                DayPreference(
                    user=u,
                    schedule=s,
                    start=datetime.date(2022, 7, day),
                )
                for u, day in zip([u1, u2], [21, 22])
            ]
        )
        s.users.set([u1, u2])
        with patch("solver.models.get_schedule", autospec=True) as solver_function:
            s.solve()
            solver_function.assert_called_with(
                [datetime.date(2022, 7, day) for day in [21, 22]],
                {u: get_available_dates(u, s, s.start, s.end) for u in [u1, u2]},
            )

    def test_schedule_solve_creates_assignments(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date(2022, 7, 21),
            end=datetime.date(2022, 7, 22),
        )
        u1 = User.objects.create_user(username="foo", password="1234")
        u2 = User.objects.create_user(username="bar", password="1234")
        solution = [
            (datetime.date(2022, 7, 21), u1),
            (datetime.date(2022, 7, 22), u2),
        ]
        with patch(
            "solver.models.get_schedule",
            autospec=True,
            return_value=solution,
        ):
            s.solve()
            a1 = Assignment.objects.get(user=u1)
            self.assertEqual(a1.start, datetime.date(2022, 7, 21))
            a2 = Assignment.objects.get(user=u2)
            self.assertEqual(a2.start, datetime.date(2022, 7, 22))

    def test_schedule_solve_deletes_old_assignments(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date(2022, 7, 21),
            end=datetime.date(2022, 7, 22),
        )
        u1 = User.objects.create_user(username="foo", password="1234")
        Assignment.objects.create(
            schedule=s,
            user=u1,
            start=datetime.date.today(),
        )
        u2 = User.objects.create_user(username="bar", password="1234")
        solution = [
            (datetime.date(2022, 7, 21), u2),
        ]
        with patch(
            "solver.models.get_schedule",
            autospec=True,
            return_value=solution,
        ):
            s.solve()
            self.assertEqual(Assignment.objects.count(), 1)
            self.assertEqual(Assignment.objects.first().user, u2)

    def test_schedule_solve_raises_specific_exception(self):
        s = Schedule.objects.create(
            owner=self.user,
        )
        with patch(
            "solver.models.get_schedule",
            autospec=True,
            side_effect=Exception,
        ):
            with self.assertRaises(ScheduleException):
                s.solve()

    def test_schedule_if_solve_fails_old_assignments_are_deleted(self):
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date(2022, 7, 21),
            end=datetime.date(2022, 7, 22),
        )
        u1 = User.objects.create_user(username="foo", password="1234")
        Assignment.objects.create(
            schedule=s,
            user=u1,
            start=datetime.date.today(),
        )
        with patch(
            "solver.models.get_schedule",
            autospec=True,
            side_effect=Exception,
        ):
            try:
                s.solve()
            except ScheduleException:
                self.assertEqual(Assignment.objects.count(), 0)

    def test_schedule_solve_does_not_delete_other_assignments(self):
        s1 = Schedule.objects.create(
            owner=self.user,
            start=datetime.date(2022, 7, 21),
            end=datetime.date(2022, 7, 22),
        )
        u1 = User.objects.create_user(username="foo", password="1234")
        Assignment.objects.create(
            schedule=s1,
            user=u1,
            start=datetime.date.today(),
        )
        s2 = Schedule.objects.create(
            owner=self.user,
            start=datetime.date(2022, 7, 21),
            end=datetime.date(2022, 7, 22),
        )
        solution = [
            (datetime.date(2022, 7, 21), u1),
        ]
        with patch(
            "solver.models.get_schedule",
            autospec=True,
            return_value=solution,
        ):
            s2.solve()
            self.assertEqual(Assignment.objects.count(), 2)
            self.assertEqual(s1.assignments.count(), 1)

    def test_has_assignments(self):
        u = User.objects.create_user(username="foo", password="1234")
        s = Schedule.objects.create(
            owner=self.user,
            start=datetime.date.today(),
            end=datetime.date.today(),
        )
        Assignment.objects.create(
            user=u,
            schedule=s,
            start=datetime.date.today(),
        )
        self.assertTrue(s.has_assignments)
        s.assignments.all().delete()
        self.assertFalse(s.has_assignments)


@fast_password_hashing
class TestAssignment(TestCase):
    def test_create_assignment(self):
        u = User.objects.create_user(username="foo", password="1234")
        s = Schedule.objects.create(
            owner=u,
            start=datetime.date.today(),
            end=datetime.date.today(),
        )
        a = Assignment.objects.create(
            schedule=s,
            user=u,
            start=datetime.date.today(),
        )
        self.assertEqual(u.assignments.first(), a)
        self.assertEqual(s.assignments.first(), a)

    def test_assignment_unique_constraint(self):
        """there should be only one assignment for each day and schedule"""
        owner = User.objects.create_user(username="owner", password="1234")
        u1 = User.objects.create_user(username="foo", password="123")
        u2 = User.objects.create_user(username="bar", password="123")
        s = Schedule.objects.create(owner=owner)
        s.users.set([u1, u2])
        start = datetime.date.today()
        Assignment.objects.create(schedule=s, user=u1, start=start)
        with self.assertRaises(IntegrityError):
            Assignment.objects.create(schedule=s, user=u2, start=start)
