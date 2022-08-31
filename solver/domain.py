import datetime
from collections import namedtuple

from solver.solver import get_schedule


def date_range(start, end):
    current = start
    while current < end:
        yield current
        current += datetime.timedelta(days=1)


class UnknownParticipant(Exception):
    pass


User = namedtuple("User", "id username")


class Schedule:
    def __init__(
        self, id=None, owner=None, start=None, end=None, exclude_weekends=False
    ):
        self.id = id
        self.owner = owner
        self.days = set()
        self.preferences = dict()
        self.assignments = set()

        if start and end:
            self.days = {
                d
                for d in date_range(start, end)
                if not exclude_weekends or d.weekday() < 5
            }

    @property
    def participants(self):
        return set(self.preferences.keys())

    def add_day(self, date):
        self.days.add(date)

    def remove_day(self, date):
        self.days.discard(date)

    def add_participant(self, name):
        if name not in self.preferences:
            self.preferences[name] = set()

    def remove_participant(self, name):
        self.preferences.pop(name, None)

    def add_preference(self, name, date):
        if name not in self.preferences:
            raise UnknownParticipant
        self.preferences[name].add(date)

    def remove_preference(self, name, date):
        self.preferences[name].discard(date)

    def add_assignment(self, name, date):
        self.assignments.add((name, date))

    def clear_assignments(self):
        self.assignments.clear()

    def make_assignments(self):
        res = get_schedule(list(self.days), self.preferences)
        self.clear_assignments()
        for d, p in res:
            self.add_assignment(p, d)

    def has_assignments(self):
        return True if self.assignments else False
