import pytest
import datetime
from unittest.mock import patch

from solver.domain import Schedule, AssignmentError, ScheduleException


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


def test_begin_and_end():
    s = Schedule()
    assert s.start is None
    assert s.end is None
    s.add_day(datetime.date(2022, 1, 1))
    s.add_day(datetime.date(2022, 1, 31))
    assert s.start == datetime.date(2022, 1, 1)
    assert s.end == datetime.date(2022, 1, 31)


def test_add_day():
    s = Schedule()
    s.add_day(datetime.date(2022, 1, 1))
    assert s.days == {datetime.date(2022, 1, 1)}


def test_day_is_only_added_once():
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


def test_remove_day_that_does_not_exist_fails_silently():
    s = Schedule()
    s.add_day(datetime.date(2022, 1, 1))
    s.remove_day(datetime.date(2022, 1, 2))
    assert s.days == {datetime.date(2022, 1, 1)}


def test_add_participant():
    s = Schedule()
    s.add_participant("foo")
    s.add_participant("bar")
    assert s.participants == {"foo", "bar"}


def test_add_preference_implicitly_adds_participant():
    s = Schedule()
    s.add_preference("foo", datetime.date(2022, 1, 1))
    assert "foo" in s.participants


def test_add_participant_with_weekdays():
    s = Schedule(start=datetime.date(2022, 1, 1), end=datetime.date(2022, 1, 31))
    s.add_participant("foo", weekdays=[0, 3, 5])
    assert s.preferences["foo"] == {d for d in s.days if d.weekday() in [0, 3, 5]}


def test_add_preferences():
    s = Schedule()
    dates = [datetime.date(2022, 1, d) for d in range(1, 8)]
    for date in dates:
        s.add_preference("foo", date)
    assert s.preferences == {"foo": set(dates)}


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


def test_remove_participant_also_removes_preferences():
    s = Schedule()
    s.add_preference("foo", datetime.date(2022, 1, 1))
    s.remove_participant("foo")
    assert s.preferences == {}


def test_remove_preference():
    s = Schedule()
    for d in range(1, 4):
        s.add_preference("foo", datetime.date(2022, 1, d))
    s.remove_preference("foo", datetime.date(2022, 1, 2))
    assert s.preferences == {
        "foo": {datetime.date(2022, 1, d) for d in range(1, 4) if d != 2}
    }


def test_remove_preference_also_removes_assignment():
    s = Schedule()
    s.add_participant("foo")
    s.add_preference("foo", datetime.date(2022, 1, 1))
    s.add_assignment("foo", datetime.date(2022, 1, 1))
    s.remove_preference("foo", datetime.date(2022, 1, 1))
    assert s.assignments == set()


def test_remove_preference_that_does_not_exist_does_not_raise_any_error():
    s = Schedule()
    s.add_preference("foo", datetime.date(2022, 1, 1))
    s.remove_preference("foo", datetime.date(2022, 1, 2))
    assert s.preferences == {"foo": {datetime.date(2022, 1, 1)}}


def test_add_assignment():
    s = Schedule()
    s.add_preference("foo", datetime.date(2022, 1, 1))
    s.add_assignment("foo", datetime.date(2022, 1, 1))
    assert s.assignments == {("foo", datetime.date(2022, 1, 1))}


def test_remove_participant_also_removes_assignments():
    s = Schedule()
    s.add_preference("foo", datetime.date(2022, 1, 1))
    s.add_assignment("foo", datetime.date(2022, 1, 1))
    s.remove_participant("foo")
    assert s.assignments == set()


def test_clear_assignments():
    s = Schedule()
    s.add_preference("foo", datetime.date(2022, 1, 1))
    s.add_preference("bar", datetime.date(2022, 1, 2))
    s.add_assignment("foo", datetime.date(2022, 1, 1))
    s.add_assignment("bar", datetime.date(2022, 1, 2))
    s.clear_assignments()
    assert s.assignments == set()


def test_assignment_cannot_be_added_if_no_preference_exists():
    s = Schedule()
    s.add_participant("foo")
    with pytest.raises(
        AssignmentError, match="is not in list of preferred dates for foo"
    ):
        s.add_assignment("foo", datetime.date(2022, 1, 1))


def test_assignment_cannot_be_added_if_no_participant_exists():
    s = Schedule()
    with pytest.raises(AssignmentError, match="Participant foo is unknown"):
        s.add_assignment("foo", datetime.date(2022, 1, 1))


def test_has_assignments():
    s = Schedule()
    s.add_preference("foo", datetime.date(2022, 1, 1))
    assert s.has_assignments() is False
    s.add_assignment("foo", datetime.date(2022, 1, 1))
    assert s.has_assignments() is True


def test_call_solver():
    s = Schedule()
    with patch("solver.domain.get_schedule", autospec=True) as f:
        s.make_assignments()
        f.assert_called_once()


def test_schedule_solve_calls_solver_with_correct_arguments():
    s = Schedule(start=datetime.date(2022, 1, 1), end=datetime.date(2022, 1, 8))
    preferences = {
        "foo": {datetime.date(2022, 1, x) for x in [1, 3, 5]},
        "bar": {datetime.date(2022, 1, y) for y in [2, 5, 6]},
    }
    for name, dates in preferences.items():
        for date in dates:
            s.add_preference(name, date)
    with patch("solver.domain.get_schedule", autospec=True) as f:
        s.make_assignments()
        f.assert_called_with(
            list(set(datetime.date(2022, 1, day) for day in range(1, 8))),
            preferences,
            window=None,
        )


def test_schedule_solve_creates_assignments():
    s = Schedule()
    s.add_preference("foo", datetime.date(2022, 7, 21))
    s.add_preference("bar", datetime.date(2022, 7, 22))
    solution = [
        (datetime.date(2022, 7, 21), "foo"),
        (datetime.date(2022, 7, 22), "bar"),
    ]
    with patch(
        "solver.domain.get_schedule",
        autospec=True,
        return_value=solution,
    ):
        s.make_assignments()
        assert s.assignments == {
            ("foo", datetime.date(2022, 7, 21)),
            ("bar", datetime.date(2022, 7, 22)),
        }


def test_schedule_solve_deletes_old_assignments():
    s = Schedule()
    s.add_preference("foo", datetime.date(2022, 7, 21))
    s.add_preference("foo", datetime.date(2022, 7, 22))
    s.add_preference("bar", datetime.date(2022, 7, 22))
    s.add_assignment("foo", datetime.date(2022, 7, 22))
    solution = [
        (datetime.date(2022, 7, 21), "foo"),
        (datetime.date(2022, 7, 22), "bar"),
    ]
    with patch(
        "solver.domain.get_schedule",
        autospec=True,
        return_value=solution,
    ):
        s.make_assignments()
        assert s.assignments == {
            ("foo", datetime.date(2022, 7, 21)),
            ("bar", datetime.date(2022, 7, 22)),
        }


def test_solve_raises_specific_exception():
    s = Schedule()
    with patch(
        "solver.domain.get_schedule",
        autospec=True,
        side_effect=Exception,
    ):
        with pytest.raises(ScheduleException):
            s.make_assignments()


def test_if_solve_fails_old_assignments_are_delted():
    s = Schedule()
    s.add_preference("foo", datetime.date(2022, 7, 21))
    s.add_preference("foo", datetime.date(2022, 7, 22))
    s.add_preference("bar", datetime.date(2022, 7, 22))
    s.add_assignment("foo", datetime.date(2022, 7, 22))
    with patch(
        "solver.domain.get_schedule",
        autospec=True,
        side_effect=Exception,
    ):
        try:
            s.make_assignments()
        except Exception:
            pass
        assert s.assignments == set()
