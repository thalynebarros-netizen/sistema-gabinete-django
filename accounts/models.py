from django.conf import settings
from django.db import models


class StaffProfile(models.Model):
    class Role(models.TextChoices):
        VIEWER = "viewer", "Leitura"
        EDITOR = "editor", "Edição"
        COORDINATOR = "coordinator", "Coordenação"
        ADMIN = "admin", "Administração"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )
    display_name = models.CharField("nome de exibição", max_length=180)
    role = models.CharField(
        "perfil",
        choices=Role.choices,
        default=Role.VIEWER,
        max_length=24,
    )
    active = models.BooleanField("ativo", default=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "perfil da equipe"
        verbose_name_plural = "perfis da equipe"

    def __str__(self):
        return self.display_name or self.user.get_username()
