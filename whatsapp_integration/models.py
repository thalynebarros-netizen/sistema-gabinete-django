from django.conf import settings
from django.db import models

from contacts.models import Contact


class MessageTemplate(models.Model):
    meta_name = models.CharField("nome do template Meta", max_length=180)
    language_code = models.CharField("idioma", max_length=24, default="pt_BR")
    purpose = models.CharField("objetivo", max_length=180)
    preview_text = models.TextField("prévia")
    active = models.BooleanField("ativo", default=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "template WhatsApp"
        verbose_name_plural = "templates WhatsApp"

    def __str__(self):
        return self.purpose


class WhatsAppMessage(models.Model):
    class Direction(models.TextChoices):
        OUTBOUND = "outbound", "Enviada"
        INBOUND = "inbound", "Recebida"

    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        QUEUED = "queued", "Na fila"
        SENT = "sent", "Enviada"
        DELIVERED = "delivered", "Entregue"
        READ = "read", "Lida"
        FAILED = "failed", "Falhou"
        RECEIVED = "received", "Recebida"

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="whatsapp_messages",
        verbose_name="contato",
    )
    template = models.ForeignKey(
        MessageTemplate,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="template",
    )
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="enviada por",
    )
    provider_message_id = models.CharField("ID do provedor", max_length=240, blank=True)
    direction = models.CharField("direção", choices=Direction.choices, max_length=24)
    status = models.CharField(
        "status",
        choices=Status.choices,
        default=Status.DRAFT,
        max_length=24,
    )
    body_preview = models.TextField("prévia da mensagem", blank=True)
    provider_payload = models.JSONField("payload do provedor", blank=True, default=dict)
    sent_at = models.DateTimeField("enviada em", blank=True, null=True)
    created_at = models.DateTimeField("criada em", auto_now_add=True)

    class Meta:
        verbose_name = "mensagem WhatsApp"
        verbose_name_plural = "mensagens WhatsApp"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.contact} - {self.get_status_display()}"
