from django.contrib import admin

from .models import MessageTemplate, WhatsAppMessage


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ("purpose", "meta_name", "language_code", "active")
    list_filter = ("active", "language_code")
    search_fields = ("purpose", "meta_name", "preview_text")


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ("contact", "direction", "status", "sent_by", "sent_at")
    list_filter = ("direction", "status")
    search_fields = ("contact__full_name", "provider_message_id", "body_preview")
