import pytest
import datetime
from collections import Counter

from solver.solver import get_schedule


def test_equal_number_of_assignments():
    days = [datetime.date(2022, 1, d) for d in range(1, 31)]
    preferences = {name: days for name in "abc"}
    assignments = get_schedule(days, preferences)
    counter = Counter(name for day, name in assignments)
    assert counter == {name: 10 for name in preferences}


def test_unequal_number_of_assignments():
    days = [datetime.date(2022, 1, d) for d in range(1, 31)]
    preferences = {name: days for name in "abcd"}
    assignments = get_schedule(days, preferences)
    counter = Counter(name for day, name in assignments)
    assert counter == {name: 8 if name < "c" else 7 for name in preferences}


def test_respect_preferences():
    days = [datetime.date(2022, 1, d) for d in range(1, 31)]
    preferences = {
        "a": [day for day in days if day.day % 2 == 0],
        "b": [day for day in days if day.day % 2 == 1],
    }
    assignments = get_schedule(days, preferences)
    assert [day for day, name in assignments if name == "a"] == preferences["a"]
    assert [day for day, name in assignments if name == "b"] == preferences["b"]


def test_consecutive_assignments():
    days = [datetime.date(2022, 1, d) for d in range(1, 31)]
    preferences = {name: days for name in "ab"}
    assignments = get_schedule(days, preferences)
    assert assignments == [(day, "a" if day.day < 16 else "b") for day in days]


def test_infeasible_constraints():
    days = [datetime.date(2022, 1, d) for d in range(1, 31)]
    preferences = {name: days[1:-1] for name in "ab"}
    with pytest.raises(Exception):
        get_schedule(days, preferences, window=2)
