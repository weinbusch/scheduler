import pytest
import datetime

from solver.domain import Schedule, UnknownParticipant


def test_init_schedule_with_date_range():
    s = Schedule(
        start=datetime.date(2022, 1, 1),
        end=datetime.date(2022, 1, 8),
    )
    expected = {datetime.date(2022, 1, x) for x in range(1, 8)}
    assert s.days == expected


def test_init_schedule_exclude_weekends():
    s = Schedule(
        start=datetime.date(2022, 1, 1),
        end=datetime.date(2022, 1, 8),
        exclude_weekends=True,
    )
    expected = {
        d for d in (datetime.date(2022, 1, x) for x in range(1, 8)) if d.weekday() < 5
    }
    assert s.days == expected


def test_add_day():
    s = Schedule()
    s.add_day(datetime.date(2022, 1, 1))
    assert s.days == {datetime.date(2022, 1, 1)}


def test_day_cannot_be_added_twice():
    s = Schedule()
    s.add_day(datetime.date(2022, 1, 1))
    s.add_day(datetime.date(2022, 1, 2))
    s.add_day(datetime.date(2022, 1, 1))
    assert s.days == {datetime.date(2022, 1, 1), datetime.date(2022, 1, 2)}


def test_remove_day():
    s = Schedule()
    s.add_day(datetime.date(2022, 1, 1))
    s.add_day(datetime.date(2022, 1, 2))
    s.add_day(datetime.date(2022, 1, 3))
    s.remove_day(datetime.date(2022, 1, 2))
    assert s.days == {datetime.date(2022, 1, 1), datetime.date(2022, 1, 3)}


def test_remove_day_that_does_not_exist():
    s = Schedule()
    s.add_day(datetime.date(2022, 1, 1))
    s.remove_day(datetime.date(2022, 1, 2))
    assert s.days == {datetime.date(2022, 1, 1)}


def test_add_participant():
    s = Schedule()
    s.add_participant("foo")
    assert s.participants == {"foo"}


def test_add_participant_does_not_affect_previous_preferences():
    s = Schedule()
    s.add_participant("foo")
    s.add_preference("foo", datetime.date(2022, 1, 1))
    s.add_participant("foo")
    assert s.preferences == {"foo": {datetime.date(2022, 1, 1)}}


def test_remove_participant():
    s = Schedule()
    s.add_participant("foo")
    s.add_participant("bar")
    s.remove_participant("foo")
    assert s.participants == {"bar"}


def test_add_preference():
    s = Schedule()
    s.add_participant("foo")
    s.add_preference("foo", datetime.date(2022, 1, 1))
    assert s.preferences == {"foo": {datetime.date(2022, 1, 1)}}


def test_add_preference_for_unknown_participant():
    s = Schedule()
    with pytest.raises(UnknownParticipant):
        s.add_preference("foo", datetime.date(2022, 1, 1))


def test_remove_preference():
    s = Schedule()
    s.add_participant("foo")
    s.add_preference("foo", datetime.date(2022, 1, 1))
    s.add_preference("foo", datetime.date(2022, 1, 2))
    s.add_preference("foo", datetime.date(2022, 1, 3))
    s.remove_preference("foo", datetime.date(2022, 1, 2))
    assert s.preferences == {"foo": {datetime.date(2022, 1, x) for x in [1, 3]}}


def test_remove_preference_that_does_not_exist():
    s = Schedule()
    s.add_participant("foo")
    s.add_preference("foo", datetime.date(2022, 1, 1))
    s.add_preference("foo", datetime.date(2022, 1, 3))
    s.remove_preference("foo", datetime.date(2022, 1, 2))
    assert s.preferences == {"foo": {datetime.date(2022, 1, x) for x in [1, 3]}}


def test_add_assignment():
    s = Schedule()
    s.add_assignment("foo", datetime.date(2022, 1, 1))
    assert s.assignments == {("foo", datetime.date(2022, 1, 1))}


def test_clear_assignments():
    s = Schedule()
    s.add_assignment("foo", datetime.date(2022, 1, 1))
    s.add_assignment("bar", datetime.date(2022, 1, 2))
    s.clear_assignments()
    assert s.assignments == set()


def test_make_assignments():
    """Test a simple case with two families and four days"""
    s = Schedule(start=datetime.date(2022, 1, 1), end=datetime.date(2022, 1, 5))
    s.add_participant("foo")
    s.add_participant("bar")
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


def test_has_assignments():
    s = Schedule()
    assert s.has_assignments() is False
    s.add_assignment("foo", datetime.date(2022, 1, 1))
    assert s.has_assignments() is True
