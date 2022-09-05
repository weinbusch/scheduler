from django.db.models import Q

from solver.models import Schedule


class ScheduleRepository:
    def list(self, user_id=None):
        qs = self._queryset()
        if user_id is not None:
            qs = qs.filter(Q(users__id=user_id) | Q(owner_id=user_id))
        return [o.to_domain() for o in qs]

    def get(self, pk):
        try:
            return self._queryset().get(pk=pk).to_domain()
        except Schedule.DoesNotExist:
            return None

    def _queryset(self):
        return Schedule.objects.all()

    def add(self, s):
        return Schedule.update_from_domain(s)
