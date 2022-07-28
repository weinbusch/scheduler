from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


# @receiver(post_save, sender=User)
# def create_user_preferences(sender, **kwargs):
#     if kwargs.get("created"):
#         user = kwargs["instance"]
#         UserPreferences.objects.create(user=user)
