from django.contrib import admin

from .models import MobilizationGroup


@admin.register(MobilizationGroup)
class MobilizationGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "kind", "member_count", "leader")
    list_filter = ("kind", "city")
    search_fields = ("name", "city", "notes", "leader__full_name")
