import datetime
from collections import namedtuple
from dataclasses import dataclass, field

from solver.solver import get_schedule


def date_range(start, end):
    current = start
    while current < end:
        yield current
        current += datetime.timedelta(days=1)


class UnknownParticipant(Exception):
    pass


class AssignmentError(Exception):
    pass


class ScheduleException(Exception):
    pass


User = namedtuple("User", "id username")


@dataclass
class Participant:
    preferences: set = field(default_factory=set)
    assignments: set = field(default_factory=set)


class Schedule:
    def __init__(
        self, id=None, owner=None, start=None, end=None, exclude_weekends=False
    ):
        self.id = id
        self.owner = owner
        self.days = set()
        self._participants = dict()

        if start and end:
            self.days = {
                d
                for d in date_range(start, end)
                if not exclude_weekends or d.weekday() < 5
            }

    @property
    def participants(self):
        return set(self._participants.keys())

    @property
    def preferences(self):
        return {key: val.preferences.copy() for key, val in self._participants.items()}

    @property
    def start(self):
        return min(self.days, default=None)

    @property
    def end(self):
        return max(self.days, default=None)

    @property
    def assignments(self):
        return set(
            (name, date)
            for name, participant in self._participants.items()
            for date in participant.assignments.copy()
        )

    def add_day(self, date):
        self.days.add(date)

    def remove_day(self, date):
        self.days.discard(date)

    def add_participant(self, name):
        if name not in self._participants:
            self._participants[name] = Participant()

    def remove_participant(self, name):
        self._participants.pop(name, None)

    def add_preference(self, name, date):
        if name not in self._participants:
            self._participants[name] = Participant()
        self._participants[name].preferences.add(date)

    def remove_preference(self, name, date):
        if name in self._participants:
            self._participants[name].preferences.discard(date)

    def add_assignment(self, name, date):
        if (
            name not in self._participants
            or date not in self._participants[name].preferences
        ):
            raise AssignmentError
        self._participants[name].assignments.add(date)

    def clear_assignments(self):
        for participant in self._participants.values():
            participant.assignments.clear()

    def make_assignments(self):
        try:
            res = get_schedule(list(self.days), self.preferences)
        except Exception:
            raise ScheduleException
        finally:
            self.clear_assignments()
        for d, p in res:
            self.add_assignment(p, d)

    def has_assignments(self):
        return True if self.assignments else False
