import datetime
import scipy.optimize


def get_schedule(days, preferences, window=None):
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html#scipy.optimize.milp

    window = window or 1

    resources = set(preferences.keys())
    labels = [(d, r) for r in resources for d in days]

    def binary_vector(f):
        return [1 if f(r, d) else 0 for r in resources for d in days]

    # The coefficients of the linear objective function to be minimized
    c = binary_vector(lambda r, d: True)

    # The type of integrality constraint on each decision variable.
    integrality = c

    # Constraints
    constraints = [
        one_resource_per_day(binary_vector, days),
        equal_assignments(binary_vector, resources, days),
        respect_preferences(binary_vector, preferences),
        consecutive_assignments(binary_vector, resources, days, window),
    ]

    # solution
    res = scipy.optimize.milp(c, integrality=integrality, constraints=constraints)

    if res.x is None:
        raise Exception(res.message)

    solution = sorted(label for label, x in zip(labels, res.x) if x == 1)
    return solution


def one_resource_per_day(f, days):
    # Exactly one resource per day
    return ([f(lambda r, d: d == day) for day in days], 1, 1)


def equal_assignments(f, resources, days):
    # Not more than ceil(days/resources) and not less than
    # floor(days/resources) assignments per resouce
    x = len(days) // len(resources)
    return ([f(lambda r, d: r == resource) for resource in resources], x, x + 1)


def respect_preferences(f, preferences):
    # No assignments if day is not in preferences
    return (
        [
            f(lambda r, d: r == resource and d not in available)
            for resource, available in preferences.items()
        ],
        0,
        0,
    )


def consecutive_assignments(f, resources, days, window):
    # Not more than 1 assigment per resource on n consecutive days
    delta = datetime.timedelta(days=window)
    return (
        [
            f(lambda r, d: r == resource and day >= d and day - d < delta)
            for resource in resources
            for day in days
        ],
        0,
        1,
    )
