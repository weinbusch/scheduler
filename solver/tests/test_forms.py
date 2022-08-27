import datetime
from django.test import TestCase

from django.contrib.auth import get_user_model

from solver.views import ScheduleForm

from .utils import fast_password_hashing


User = get_user_model()


@fast_password_hashing
class ScheduleFormTest(TestCase):
    def test_create_schedule(self):
        user = User.objects.create_user(username="foo", password="1234")
        data = dict(
            start="2022-01-01",
            end="2022-12-31",
            users=[user.pk],
        )
        form = ScheduleForm(data)
        self.assertTrue(form.is_valid())
        s = form.save(commit=False)
        s.owner = user
        s.save()
        form.save_m2m()
        self.assertEqual(s.start, datetime.date(2022, 1, 1))
        self.assertQuerysetEqual(s.users.all(), [user])
