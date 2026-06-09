from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Contact, ContactInteraction


@login_required
def list_contacts(request):
    query = request.GET.get("q", "").strip()
    contacts = Contact.objects.select_related("owner")
    if query:
        contacts = contacts.filter(
            Q(full_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(city__icontains=query)
            | Q(source__icontains=query)
        )
    return render(
        request,
        "contacts/list.html",
        {
            "contacts": contacts[:100],
            "query": query,
        },
    )


def crm_queryset():
    return Contact.objects.select_related("owner").filter(
        Q(source_payload__crm_luva__isnull=False)
        | Q(source="CRM Luva")
    )


def crm_status(contact):
    return (contact.source_payload or {}).get("crm_luva", {}).get("status") or contact.profile


@login_required
def crm_contacts(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    city = request.GET.get("city", "").strip()
    review = request.GET.get("review", "").strip()

    contacts = crm_queryset()
    if query:
        contacts = contacts.filter(
            Q(full_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(city__icontains=query)
            | Q(source__icontains=query)
            | Q(notes_summary__icontains=query)
        )
    if status:
        contacts = contacts.filter(
            Q(profile=status) | Q(source_payload__crm_luva__status=status)
        )
    if city:
        contacts = contacts.filter(city=city)
    if review == "1":
        contacts = contacts.filter(source_payload__name_review_required=True)

    status_options = sorted(
        {
            value
            for value in crm_queryset().values_list("profile", flat=True)
            if value
        }
        | {
            value
            for value in crm_queryset().values_list("source_payload__crm_luva__status", flat=True)
            if value
        }
    )
    city_options = list(
        crm_queryset()
        .exclude(city="")
        .order_by("city")
        .values_list("city", flat=True)
        .distinct()[:120]
    )

    contacts = list(contacts.order_by("-updated_at", "full_name")[:200])
    for contact in contacts:
        contact.crm_status = crm_status(contact)
        contact.last_interaction = contact.interactions.first()
        contact.needs_review = bool((contact.source_payload or {}).get("name_review_required"))

    return render(
        request,
        "contacts/crm.html",
        {
            "contacts": contacts,
            "query": query,
            "selected_status": status,
            "selected_city": city,
            "review": review,
            "status_options": status_options,
            "city_options": city_options,
            "total_crm": crm_queryset().count(),
            "total_review": crm_queryset().filter(source_payload__name_review_required=True).count(),
        },
    )


@login_required
def crm_contact_detail(request, pk):
    contact = get_object_or_404(
        crm_queryset().prefetch_related("interactions__author"),
        pk=pk,
    )
    if request.method == "POST":
        summary = request.POST.get("summary", "").strip()
        channel = request.POST.get("channel", "WhatsApp").strip() or "WhatsApp"
        next_action = request.POST.get("next_action", "").strip()
        next_date = request.POST.get("next_date", "").strip()

        parts = [summary]
        if next_action:
            parts.append(f"Proxima acao: {next_action}")
        if next_date:
            parts.append(f"Data prevista: {next_date}")

        if any(parts):
            ContactInteraction.objects.create(
                contact=contact,
                author=request.user,
                channel=channel,
                summary="\n".join(part for part in parts if part),
                happened_at=timezone.now(),
            )
            contact.updated_at = timezone.now()
            contact.save(update_fields=["updated_at"])
        return redirect("contacts:crm_detail", pk=contact.pk)

    contact.crm_status = crm_status(contact)
    contact.needs_review = bool((contact.source_payload or {}).get("name_review_required"))
    contact.crm_luva = (contact.source_payload or {}).get("crm_luva", {})
    return render(
        request,
        "contacts/crm_detail.html",
        {"contact": contact},
    )
