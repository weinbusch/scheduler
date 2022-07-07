import math
import scipy


def get_schedule(days, families, available_dates):
    """get_schedule(days, families, available_dates)

    Parameters:

        days: list of datetime.date objects indicating all dates to
              which a family has to be assigned to

        families: list of family names (strings)

        available_dates: dictionary of family name/date list pairs
                         indicating on which dates each family is
                         available. If a family is not included in the
                         dictionary, its date list is considered
                         empty. If a given date is not included in a
                         family's date list, that family is *not*
                         available on this date and *cannot* be
                         assigned to this date. This might lead to an
                         infeasible model, if too many dates are
                         unavailable

    Returns:

        schedule: list of datetime.date/family name pairs

    Note: The optimizer works under the following constraints:

    1. each date must be assigned to exactly one family.

    2. the maximum number of dates assigned to any given family must
       not exceed math.ceil(len(days)/len(families)) and must not be
       lower than math.floor(len(days)/len(families)).

    3. a family cannot be assigned to a date that is not listed in its
       available dates.

    """
    constraints = make_constraints(days, families, available_dates)
    result = run_model(len(days) * len(families), constraints)
    return make_schedule(result, days, families)


def run_model(n, constraints):
    c = [1 for _ in range(n)]
    r = scipy.optimize.milp(
        c=c,
        integrality=c,
        constraints=constraints,
        bounds=(0, 1),
    )
    if not r.success:
        raise Exception(r.message)
    return r.x


def make_schedule(a, days, families):
    m = a.reshape(len(days), len(families))
    return [
        (days[i], families[j])
        for i, row in enumerate(m)
        for j, x in enumerate(row)
        if x == 1
    ]


def make_constraints(days, families, available_dates):
    constraints = []

    # 1. For each day there must be exactly 1 assigned family

    for day in days:
        constraint = scipy.optimize.LinearConstraint(
            [1 if d == day else 0 for d in days for _ in families], 1, 1
        )
        constraints.append(constraint)

    # 2. No family should do more than days/families and less than
    # (days/families)-1 of assignments

    max_assignments = math.ceil(len(days) / len(families))

    for family in families:
        constraint = scipy.optimize.LinearConstraint(
            [1 if f == family else 0 for _ in days for f in families],
            max_assignments - 1,
            max_assignments,
        )
        constraints.append(constraint)

    # 3. Availability

    for family in families:
        constraint = scipy.optimize.LinearConstraint(
            [
                1 if f == family and day not in available_dates.get(family, []) else 0
                for day in days
                for f in families
            ],
            0,
            0,
        )
        constraints.append(constraint)

    """TODO:
    - a family should not be assigned more than once every n days
    """

    return constraints
