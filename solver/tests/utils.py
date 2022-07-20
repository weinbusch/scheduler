from django.test import override_settings

# https://docs.djangoproject.com/en/4.0/topics/testing/overview/#password-hashing
fast_password_hashing = override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]
)
