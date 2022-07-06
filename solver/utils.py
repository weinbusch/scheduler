import datetime


def date_range(start, end):
    current = start
    while current <= end:
        yield current
        current = current + datetime.timedelta(days=1)
