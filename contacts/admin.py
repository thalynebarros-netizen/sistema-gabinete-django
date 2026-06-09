from django.contrib import admin

from .models import Contact, ContactInteraction


class CrmLuvaFilter(admin.SimpleListFilter):
    title = "CRM Luva"
    parameter_name = "crm_luva"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Veio do CRM Luva"),
            ("no", "Nao veio do CRM Luva"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(source_payload__crm_luva__isnull=False)
        if self.value() == "no":
            return queryset.filter(source_payload__crm_luva__isnull=True)
        return queryset


class NameReviewFilter(admin.SimpleListFilter):
    title = "nome para revisar"
    parameter_name = "name_review"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Precisa revisar"),
            ("no", "Nome ok"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(source_payload__name_review_required=True)
        if self.value() == "no":
            return queryset.exclude(source_payload__name_review_required=True)
        return queryset


class ContactInteractionInline(admin.TabularInline):
    extra = 0
    model = ContactInteraction


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    inlines = [ContactInteractionInline]
    list_display = (
        "full_name",
        "phone",
        "city",
        "profile",
        "source",
        "crm_luva_status",
        "needs_name_review",
        "owner",
    )
    list_filter = (
        CrmLuvaFilter,
        NameReviewFilter,
        "state",
        "city",
        "profile",
        "source",
        "consent_status",
    )
    readonly_fields = ("crm_luva_details",)
    search_fields = (
        "full_name",
        "phone",
        "city",
        "source",
        "notes_summary",
        "source_payload",
    )

    @admin.display(description="status Luva")
    def crm_luva_status(self, obj):
        return obj.source_payload.get("crm_luva", {}).get("status", "")

    @admin.display(boolean=True, description="revisar nome")
    def needs_name_review(self, obj):
        return bool(obj.source_payload.get("name_review_required"))

    @admin.display(description="dados do CRM Luva")
    def crm_luva_details(self, obj):
        crm = obj.source_payload.get("crm_luva")
        if not crm:
            return "Este contato nao foi vinculado ao CRM Luva."
        return (
            f"ID: {crm.get('id', '')} | "
            f"Fonte: {crm.get('fonte', '')} | "
            f"Status: {crm.get('status', '')} | "
            f"Responsavel: {crm.get('responsavel', '')}"
        )


@admin.register(ContactInteraction)
class ContactInteractionAdmin(admin.ModelAdmin):
    list_display = ("contact", "channel", "author", "happened_at")
    list_filter = ("channel",)
    search_fields = ("contact__full_name", "summary")
