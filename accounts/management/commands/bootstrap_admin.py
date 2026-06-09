import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Cria ou atualiza o usuario administrador a partir de variaveis de ambiente."

    def handle(self, *args, **options):
        username = os.getenv("ADMIN_USERNAME", "thalyne")
        email = os.getenv("ADMIN_EMAIL", "")
        password = os.getenv("ADMIN_PASSWORD", "")

        if not password:
            self.stdout.write(
                self.style.WARNING(
                    "ADMIN_PASSWORD nao definido. Usuario administrador nao foi alterado."
                )
            )
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        user.email = email or user.email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = "criado" if created else "atualizado"
        self.stdout.write(
            self.style.SUCCESS(f"Usuario administrador {action}: {username}")
        )
