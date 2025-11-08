from django.apps import AppConfig
import os


def _create_superuser_from_env():
    # Only run when explicitly requested
    if os.environ.get('CREATE_SUPERUSER_ON_STARTUP', '').lower() != 'true':
        return
    try:
        from django.contrib.auth import get_user_model
        from django.db import transaction

        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not username or not password:
            return

        User = get_user_model()
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': True,
                },
            )
            # Ensure flags and password are set even if user existed
            user.email = email or user.email
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save()
    except Exception:
        # Silently ignore to avoid breaking app startup; check logs if needed
        pass


class GatepassConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gatepass'

    def ready(self):
        _create_superuser_from_env()
