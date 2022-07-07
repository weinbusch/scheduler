from django.conf import settings
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from solver.utils import date_range


weekdays = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class UserPreferences(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)

    allowed_days = models.JSONField(
        default=list,
        encoder=DjangoJSONEncoder,
    )

    excluded_days = models.JSONField(
        default=list,
        encoder=DjangoJSONEncoder,
    )

    def is_available(self, date):
        return getattr(self, weekdays[date.weekday()], False)

    def get_available_dates(self, start, end):
        return [d for d in date_range(start, end) if self.is_available(d)]
