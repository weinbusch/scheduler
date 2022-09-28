import logging

from django.contrib.auth import get_user_model

from solver.models import Schedule

User = get_user_model()

logger = logging.getLogger(__name__)


class ScheduleRepository:
    def list(self, user_id):
        qs = self._queryset().filter(owner_id=user_id)
        return [o.to_domain() for o in qs]

    def list_all(self):
        return [o.to_domain() for o in self._queryset()]

    def get(self, pk):
        try:
            logger.debug(f"Get Schedule {pk}")
            return self._queryset().get(pk=pk).to_domain()
        except Schedule.DoesNotExist:
            return None

    def _queryset(self):
        return (
            Schedule.objects.all()
            .select_related("owner")
            .prefetch_related("day_set")
            .prefetch_related("participant_set")
            .prefetch_related("participant_set__preferreddate_set")
            .prefetch_related("participant_set__assigneddate_set")
        )

    def add(self, s):
        logger.debug(f"Add Schedule {s.id}")
        return Schedule.update_from_domain(s)

    def delete(self, s):
        return Schedule.objects.filter(id=s.id).delete()
