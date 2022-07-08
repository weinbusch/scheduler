import datetime


def date_range(start, end):
    current = start
    while current <= end:
        yield current
        current = current + datetime.timedelta(days=1)


def parse_date_list(xs):
    """parses a list 'xs' to yield a list of datetime.date objects

    The elements of 'xs' must be either datetime.date objects or
    strings having the format YYYY-MM-DD. Otherwise a ValueError is
    raised.

    """
    return [
        x
        if isinstance(x, datetime.date)
        else datetime.datetime.strptime(x, "%Y-%m-%d").date()
        for x in xs
    ]
