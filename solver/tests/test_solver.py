import pytest
import datetime
from collections import Counter
from itertools import groupby

from solver.solver import get_schedule

days = {datetime.date(2022, 1, d) for d in range(1, 31)}


def test_problem_can_be_solved_by_an_equal_number_of_assignments():
    preferences = {name: days for name in "abc"}
    assignments = get_schedule(days, preferences)
    counter = Counter(name for day, name in assignments)
    assert counter == {name: 10 for name in preferences}


def test_problem_requires_an_unequal_number_of_assignments():
    preferences = {name: days for name in "abcd"}
    assignments = get_schedule(days, preferences)
    counter = Counter(name for day, name in assignments)
    assert all(7 <= x <= 8 for x in counter.values())


def test_respect_preferences():
    preferences = {
        "a": {day for day in days if day.day % 2 == 0},
        "b": {day for day in days if day.day % 2 == 1},
    }
    assignments = get_schedule(days, preferences)
    assert {day for day, name in assignments if name == "a"} == preferences["a"]
    assert {day for day, name in assignments if name == "b"} == preferences["b"]


def test_infeasible_preferences():
    available = days.copy()
    available.pop()
    preferences = {name: available for name in "ab"}
    with pytest.raises(Exception, match="infeasible"):
        get_schedule(days, preferences)


def test_solution_contains_consecutive_assignments():
    preferences = {name: days for name in "ab"}
    assignments = get_schedule(days, preferences)
    assert any(
        len(list(g)) > 1 for k, g in groupby(name for day, name in assignments)
    ), "No consecutive elements"


def test_no_consecutive_assignments():
    preferences = {name: days for name in "ab"}
    assignments = get_schedule(days, preferences, window=2)
    assert all(
        len(list(g)) == 1 for k, g in groupby(name for day, name in assignments)
    ), "Found consecutive elements"
