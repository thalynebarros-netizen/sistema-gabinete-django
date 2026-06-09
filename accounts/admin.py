from django.contrib import admin

from .models import StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "role", "active", "updated_at")
    list_filter = ("role", "active")
    search_fields = ("display_name", "user__username", "user__email")
