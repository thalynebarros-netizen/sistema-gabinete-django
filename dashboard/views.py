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


def get_crm_contacts():
    return Contact.objects.filter(
        Q(source_payload__crm_luva__isnull=False) | Q(source="CRM Luva")
    )


def crm_payload(contact):
    return (contact.source_payload or {}).get("crm_luva", {})


def pct(value, total):
    return round((value / total) * 100, 1) if total else 0


def width(value, max_value):
    return min(100, max(2, int(round((value / max_value) * 100)))) if max_value else 2


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
def strategic_panel(request):
    data = {
        "updated_at": "Abril de 2026",
        "total_map": 21169,
        "total_crm": 3476,
        "municipalities": 146,
        "leaders": 556,
        "supporters": 4264,
        "duplicates": 667,
        "with_phone": 21166,
        "without_city": 4277,
        "sources": [
            ("Edital de Emendas Participativas", 6842, "blue"),
            ("WhatsApp", 5092, "green"),
            ("Instagram", 2609, "purple"),
            ("Apoiadores de redes sociais", 824, "amber"),
            ("Mapeamento", 692, "blue"),
            ("Formulário", 595, "green"),
            ("Visita", 509, "red"),
            ("Facebook", 431, "purple"),
        ],
        "profiles": [
            ("1º Apoiador", 3409, "blue"),
            ("2º Divulgador", 591, "green"),
            ("2º Mobiliza redes", 231, "purple"),
            ("3º Ação de rua", 70, "red"),
            ("2º Ação de rua", 36, "amber"),
        ],
        "cities": [
            ("Campo Grande", 12098, "Muito quente"),
            ("Dourados", 947, "Quente"),
            ("Corumbá", 894, "Quente"),
            ("Paranaíba", 210, "Morno"),
            ("Naviraí", 176, "Morno"),
            ("Aquidauana", 125, "Morno"),
            ("Nova Andradina", 132, "Morno"),
            ("Mundo Novo", 138, "Morno"),
            ("Anastácio", 84, "Morno"),
            ("Ponta Porã", 112, "Morno"),
        ],
        "crm_status": [
            ("Coletando dados", 2829, "blue"),
            ("1 contato", 352, "green"),
            ("Lixo", 109, "red"),
            ("Mapeamento 3.0", 86, "purple"),
            ("Lideranças PT", 27, "green"),
            ("Apresentando redes", 18, "blue"),
        ],
        "leader_categories": [
            ("Liderança de Base", 237, "green"),
            ("Liderança Geral", 123, "blue"),
            ("Liderança Partidária PT", 107, "purple"),
            ("Liderança de Entidades", 86, "amber"),
            ("Liderança de Bairro", 3, "blue"),
        ],
        "emendas_summary": [
            ("Maior execução territorial", "Use o mapa para ver onde o valor destinado se concentra."),
            ("Situação", "Cruze pago, empenhado e indicado para acompanhar pendências."),
            ("Ministérios", "Saúde, MIDR, Educação e Cidades ajudam a separar pauta por área."),
            ("Conferência", "Clique em cada município para ver objetos, situação e valores pagos."),
        ],
    }

    total_general = data["total_map"] + data["total_crm"]
    max_source = max(value for _, value, _ in data["sources"])
    max_profile = max(value for _, value, _ in data["profiles"])
    max_city = max(value for _, value, _ in data["cities"])
    max_status = max(value for _, value, _ in data["crm_status"])

    context = {
        **data,
        "total_general": total_general,
        "phone_pct": pct(data["with_phone"], data["total_map"]),
        "city_pct": pct(data["total_map"] - data["without_city"], data["total_map"]),
        "map_share": pct(data["total_map"], total_general),
        "crm_share": pct(data["total_crm"], total_general),
        "sources_rows": [
            (label, value, color, width(value, max_source))
            for label, value, color in data["sources"]
        ],
        "profile_rows": [
            (label, value, color, width(value, max_profile))
            for label, value, color in data["profiles"]
        ],
        "city_rows": [
            (label, value, zone, width(value, max_city))
            for label, value, zone in data["cities"]
        ],
        "status_rows": [
            (label, value, color, width(value, max_status))
            for label, value, color in data["crm_status"]
        ],
    }
    return render(request, "dashboard/strategic_panel.html", context)


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
