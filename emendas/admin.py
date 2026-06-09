from django.contrib import admin

from .models import Emenda


@admin.register(Emenda)
class EmendaAdmin(admin.ModelAdmin):
    list_display = (
        "beneficiary",
        "city",
        "year",
        "ministry",
        "value_destined",
        "value_paid",
        "status",
    )
    list_filter = ("year", "ministry", "status", "city")
    search_fields = ("beneficiary", "city", "object", "source")
