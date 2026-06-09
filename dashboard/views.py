import csv
from collections import Counter, defaultdict

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import render

from contacts.models import Contact, ContactInteraction
from emendas.models import Emenda
from mobilization.models import MobilizationGroup
from whatsapp_integration.models import WhatsAppMessage


@login_required
def home(request):
    emenda_totals = Emenda.objects.aggregate(
        destined=Sum("value_destined"),
        paid=Sum("value_paid"),
    )
    context = {
        "contact_count": Contact.objects.count(),
        "crm_count": Contact.objects.filter(
            Q(source_payload__crm_luva__isnull=False) | Q(source="CRM Luva")
        ).count(),
        "review_count": Contact.objects.filter(source_payload__name_review_required=True).count(),
        "group_count": MobilizationGroup.objects.count(),
        "emenda_count": Emenda.objects.count(),
        "message_count": WhatsAppMessage.objects.count(),
        "emenda_destined": emenda_totals["destined"] or 0,
        "emenda_paid": emenda_totals["paid"] or 0,
    }
    return render(request, "dashboard/home.html", context)


@login_required
def pitep(request):
    context = {
        "pillars": [
            {
                "title": "Base única de contatos",
                "text": "Consolidar mapeamento, CRM, lideranças, grupos, emendas e histórico de atendimento em um banco pesquisável.",
            },
            {
                "title": "Inteligência territorial",
                "text": "Cruzar cidade, bairro, votação, emendas, lideranças e demandas para orientar agenda, comunicação e mobilização.",
            },
            {
                "title": "CRM do gabinete",
                "text": "Registrar contatos, retornos, responsáveis, status, próximos passos e histórico de relacionamento com cada pessoa.",
            },
            {
                "title": "Automação responsável",
                "text": "Preparar fluxos de WhatsApp, lembretes e relatórios sem perder controle humano, consentimento e segurança dos dados.",
            },
        ],
        "phases": [
            ("1", "Organizar dados", "Padronizar planilhas, campos, cidades, telefones e fontes."),
            ("2", "Migrar para Django", "Usar banco de dados, login, permissões e telas internas para a equipe."),
            ("3", "Criar operação diária", "Atendimento, tarefas, segmentos, busca avançada e relatórios para coordenação."),
            ("4", "Automatizar e medir", "WhatsApp API, indicadores de resposta, mapas de calor e análises estratégicas."),
        ],
    }
    return render(request, "dashboard/pitep.html", context)


def get_crm_contacts():
    return Contact.objects.filter(
        Q(source_payload__crm_luva__isnull=False) | Q(source="CRM Luva")
    )


def crm_payload(contact):
    return (contact.source_payload or {}).get("crm_luva", {})


def pct(value, total):
    return round((value / total) * 100, 1) if total else 0


def top_counter_rows(counter, total, limit=10):
    return [
        {
            "label": label or "Nao informado",
            "value": value,
            "percent": pct(value, total),
            "width": min(100, max(2, int(round(pct(value, total))))),
        }
        for label, value in counter.most_common(limit)
    ]


@login_required
def reports(request):
    contacts = list(get_crm_contacts().prefetch_related("interactions"))
    total = len(contacts)
    with_phone = sum(1 for contact in contacts if contact.phone)
    with_city = sum(1 for contact in contacts if contact.city)
    needs_review = sum(1 for contact in contacts if (contact.source_payload or {}).get("name_review_required"))
    with_interaction = sum(1 for contact in contacts if contact.interactions.exists())

    gender_counter = Counter()
    city_counter = Counter()
    source_counter = Counter()
    status_counter = Counter()
    weekday_counter = Counter()
    hour_counter = Counter()
    city_source = defaultdict(Counter)

    for contact in contacts:
        payload = crm_payload(contact)
        gender_counter[(payload.get("genero") or "Nao informado").strip() or "Nao informado"] += 1
        city = contact.city or payload.get("cidade") or "Cidade nao informada"
        source = payload.get("fonte") or contact.source or "Nao informado"
        status = payload.get("status") or contact.profile or "Sem status"
        city_counter[city] += 1
        source_counter[source] += 1
        status_counter[status] += 1
        city_source[city][source] += 1

    for interaction in ContactInteraction.objects.filter(contact__in=contacts):
        weekday_counter[interaction.happened_at.strftime("%a")] += 1
        hour_counter[interaction.happened_at.hour] += 1

    top_cities = top_counter_rows(city_counter, total, 12)
    top_sources = top_counter_rows(source_counter, total, 8)
    top_statuses = top_counter_rows(status_counter, total, 8)
    top_gender = top_counter_rows(gender_counter, total, 6)
    max_city = top_cities[0]["value"] if top_cities else 1

    city_map = []
    for index, row in enumerate(top_cities[:10]):
        city_map.append({
            **row,
            "size": 22 + min(58, int((row["value"] / max_city) * 58)),
            "x": 12 + ((index * 23) % 76),
            "y": 18 + ((index * 31) % 64),
            "source": city_source[row["label"]].most_common(1)[0][0] if city_source[row["label"]] else "Nao informado",
        })

    context = {
        "total": total,
        "with_phone": with_phone,
        "with_city": with_city,
        "needs_review": needs_review,
        "with_interaction": with_interaction,
        "phone_pct": pct(with_phone, total),
        "city_pct": pct(with_city, total),
        "review_pct": pct(needs_review, total),
        "interaction_pct": pct(with_interaction, total),
        "phone_pct_width": min(100, int(round(pct(with_phone, total)))),
        "city_pct_width": min(100, int(round(pct(with_city, total)))),
        "review_pct_width": min(100, int(round(pct(needs_review, total)))),
        "interaction_pct_width": min(100, int(round(pct(with_interaction, total)))),
        "top_cities": top_cities,
        "top_sources": top_sources,
        "top_statuses": top_statuses,
        "top_gender": top_gender,
        "city_map": city_map,
        "weekday_rows": top_counter_rows(weekday_counter, sum(weekday_counter.values()), 7),
        "hour_rows": top_counter_rows(Counter({f"{hour:02d}h": count for hour, count in hour_counter.items()}), sum(hour_counter.values()), 8),
    }
    return render(request, "dashboard/reports.html", context)


@login_required
def export_reports_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="relatorio_crm.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["nome", "telefone", "cidade", "fonte", "status", "genero", "revisar_nome"])
    for contact in get_crm_contacts().order_by("city", "full_name"):
        payload = crm_payload(contact)
        writer.writerow([
            contact.full_name,
            contact.phone,
            contact.city or payload.get("cidade", ""),
            payload.get("fonte") or contact.source,
            payload.get("status") or contact.profile,
            payload.get("genero", ""),
            "sim" if (contact.source_payload or {}).get("name_review_required") else "nao",
        ])
    return response
