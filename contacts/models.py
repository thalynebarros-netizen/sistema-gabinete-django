from django.conf import settings
from django.db import models


class Contact(models.Model):
    class ConsentStatus(models.TextChoices):
        PENDING = "pending", "Pendente"
        GRANTED = "granted", "Autorizado"
        OPTED_OUT = "opted_out", "Não receber mensagens"

    external_id = models.CharField("ID externo", max_length=120, blank=True)
    full_name = models.CharField("nome", max_length=240)
    phone = models.CharField("telefone", max_length=32, blank=True)
    city = models.CharField("cidade", max_length=160, blank=True, db_index=True)
    state = models.CharField("estado", max_length=2, default="MS")
    neighborhood = models.CharField("bairro", max_length=180, blank=True)
    profile = models.CharField("perfil", max_length=180, blank=True)
    source = models.CharField("fonte", max_length=180, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="assigned_contacts",
        verbose_name="responsável",
    )
    consent_status = models.CharField(
        "consentimento",
        choices=ConsentStatus.choices,
        default=ConsentStatus.PENDING,
        max_length=24,
    )
    notes_summary = models.TextField("resumo", blank=True)
    source_payload = models.JSONField("dados de origem", blank=True, default=dict)
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "contato"
        verbose_name_plural = "contatos"
        ordering = ("full_name",)

    def __str__(self):
        return self.full_name


class ContactInteraction(models.Model):
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="interactions",
        verbose_name="contato",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="contact_interactions",
        verbose_name="autor",
    )
    channel = models.CharField("canal", max_length=80, default="WhatsApp")
    summary = models.TextField("registro")
    happened_at = models.DateTimeField("data do contato")
    created_at = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "interação"
        verbose_name_plural = "interações"
        ordering = ("-happened_at",)

    def __str__(self):
        return f"{self.contact} - {self.channel}"
