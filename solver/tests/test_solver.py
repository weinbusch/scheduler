import math
import unittest
import datetime
import collections

from solver.solver import get_schedule
from solver.domain import Schedule


def test_make_assignments():
    """Test a simple case with two families and four days"""
    s = Schedule(start=datetime.date(2022, 1, 1), end=datetime.date(2022, 1, 5))
    s.add_preference("foo", datetime.date(2022, 1, 1))
    s.add_preference("foo", datetime.date(2022, 1, 3))
    s.add_preference("bar", datetime.date(2022, 1, 2))
    s.add_preference("bar", datetime.date(2022, 1, 4))
    s.make_assignments()
    assert s.assignments == {
        ("foo", datetime.date(2022, 1, 1)),
        ("bar", datetime.date(2022, 1, 2)),
        ("foo", datetime.date(2022, 1, 3)),
        ("bar", datetime.date(2022, 1, 4)),
    }


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
        schedule = get_schedule(days, available_dates)
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
        schedule = get_schedule(days, available_dates)
        counts = collections.Counter([f for _, f in schedule])
        self.assertTrue(all([counts[f] == n for f in families]))

    def test_uneven_number_of_days(self):
        """Test with 2 families and 3 days"""
        days = [datetime.date.today() + datetime.timedelta(days=x) for x in range(3)]
        families = ["foo", "bar"]
        available_dates = {f: days for f in families}
        schedule = get_schedule(days, available_dates)
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
                schedule = get_schedule(days, available_dates)
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
        available_dates = {"foo": [days[0], days[3]], "bar": days}
        schedule = get_schedule(days, available_dates)
        self.assertListEqual([f for _, f in schedule], ["foo", "bar", "bar", "foo"])

    def test_infeasible_constraints(self):
        """First family is only available on a single day"""
        days = [
            datetime.date.today(),
            datetime.date.today() + datetime.timedelta(days=1),
            datetime.date.today() + datetime.timedelta(days=2),
            datetime.date.today() + datetime.timedelta(days=3),
        ]
        available_dates = {"foo": [days[0]], "bar": days}
        with self.assertRaises(Exception):
            get_schedule(days, available_dates)
