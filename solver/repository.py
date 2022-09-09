from django.contrib.auth import get_user_model

from solver.models import Schedule

User = get_user_model()


class ScheduleRepository:
    def list(self, user_id=None):
        qs = self._queryset()
        if user_id is not None:
            qs = qs.filter(owner_id=user_id)
            try:
                qs = qs.union(User.objects.get(id=user_id).schedules.all())
            except User.DoesNotExist:
                pass
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

    def delete(self, s):
        return Schedule.objects.filter(id=s.id).delete()
