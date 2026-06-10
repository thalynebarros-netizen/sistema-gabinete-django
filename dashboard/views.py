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


def heat_radius(value, max_value, base=14, spread=48):
    return round(base + min(spread, ((value / max_value) ** 0.5) * spread), 1) if max_value else base


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
    zone_colors = {
        "Muito quente": "#e02424",
        "Quente": "#c4780a",
        "Morno": "#1d6ef5",
        "Frio": "#0d7a4e",
        "Muito frio": "#94a3b8",
    }
    city_positions = {
        "Campo Grande": (315, 276),
        "Dourados": (284, 414),
        "Corumb?": (120, 173),
        "Parana?ba": (497, 219),
        "Navira?": (335, 463),
        "Aquidauana": (195, 273),
        "Nova Andradina": (419, 405),
        "Mundo Novo": (353, 518),
        "Anast?cio": (202, 282),
        "Ponta Por?": (236, 457),
        "Tr?s Lagoas": (468, 324),
        "Coxim": (270, 126),
        "Chapad?o do Sul": (460, 154),
        "Rio Brilhante": (304, 373),
        "Sidrol?ndia": (264, 322),
        "Bodoquena": (152, 291),
        "Amambai": (249, 492),
        "Bonito": (168, 336),
        "Aral Moreira": (232, 489),
        "Nioaque": (207, 323),
    }
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
            ("Formul?rio", 595, "green"),
            ("Visita", 509, "red"),
            ("Facebook", 431, "purple"),
        ],
        "profiles": [
            ("1? Apoiador", 3409, "blue"),
            ("2? Divulgador", 591, "green"),
            ("2? Mobiliza redes", 231, "purple"),
            ("3? A??o de rua", 70, "red"),
            ("2? A??o de rua", 36, "amber"),
        ],
        "cities": [
            ("Campo Grande", 12098, "Muito quente"),
            ("Dourados", 947, "Quente"),
            ("Corumb?", 894, "Quente"),
            ("Parana?ba", 210, "Morno"),
            ("Navira?", 176, "Morno"),
            ("Aquidauana", 125, "Morno"),
            ("Nova Andradina", 132, "Morno"),
            ("Mundo Novo", 138, "Morno"),
            ("Anast?cio", 84, "Morno"),
            ("Ponta Por?", 112, "Morno"),
        ],
        "election": {
            "total": 56552,
            "municipalities": 79,
            "source": "TSE - vota??o por se??o 2022 MS",
            "cities": [
                ("Campo Grande", 37737, "Muito quente", 66.73),
                ("Dourados", 2497, "Quente", 4.42),
                ("Corumb?", 1384, "Quente", 2.45),
                ("Tr?s Lagoas", 1224, "Quente", 2.16),
                ("Nova Andradina", 1085, "Quente", 1.92),
                ("Coxim", 857, "Morno", 1.52),
                ("Ponta Por?", 737, "Morno", 1.30),
                ("Aquidauana", 710, "Morno", 1.26),
                ("Chapad?o do Sul", 662, "Morno", 1.17),
                ("Rio Brilhante", 638, "Morno", 1.13),
                ("Sidrol?ndia", 529, "Morno", 0.94),
                ("Parana?ba", 521, "Morno", 0.92),
            ],
        },
        "emendas": {
            "total_projects": 263,
            "total_value": 217065354.71,
            "paid_value": 135236888.91,
            "to_pay_value": 82253307.45,
            "municipalities": 58,
            "cities": [
                ("Campo Grande", 24932594.00, "Muito quente", 23, 18007594.00),
                ("Aquidauana", 5699396.00, "Quente", 7, 4605186.00),
                ("Corumb?", 5444812.00, "Quente", 8, 3194812.00),
                ("Coxim", 4154969.21, "Quente", 4, 1230000.00),
                ("Nova Andradina", 3967452.00, "Quente", 7, 2219900.00),
                ("Bodoquena", 3599433.00, "Morno", 5, 1936470.00),
                ("Ponta Por?", 3380000.00, "Morno", 3, 2000000.00),
                ("Amambai", 3230000.00, "Morno", 6, 1880000.00),
                ("Bonito", 3132009.58, "Morno", 4, 1909781.58),
                ("Aral Moreira", 2967176.00, "Morno", 3, 1000000.00),
                ("Navira?", 2943920.00, "Morno", 4, 993920.00),
                ("Nioaque", 2811031.00, "Morno", 9, 280000.00),
            ],
            "themes": [
                ("Sa?de", 133, "green"),
                ("MIDR", 38, "blue"),
                ("Educa??o", 16, "purple"),
                ("Cidades", 14, "amber"),
                ("MDS", 13, "red"),
                ("Economia", 11, "blue"),
            ],
            "situations": [
                ("Pago", 140, "green"),
                ("Indicado", 76, "amber"),
                ("Empenhado", 24, "blue"),
                ("Publicado", 14, "purple"),
                ("Entregue", 2, "green"),
                ("Pago parcial", 1, "amber"),
            ],
        },
        "crm_status": [
            ("Coletando dados", 2829, "blue"),
            ("1 contato", 352, "green"),
            ("Lixo", 109, "red"),
            ("Mapeamento 3.0", 86, "purple"),
            ("Lideran?as PT", 27, "green"),
            ("Apresentando redes", 18, "blue"),
        ],
        "leader_categories": [
            ("Lideran?a de Base", 237, "green"),
            ("Lideran?a Geral", 123, "blue"),
            ("Lideran?a Partid?ria PT", 107, "purple"),
            ("Lideran?a de Entidades", 86, "amber"),
            ("Lideran?a de Bairro", 3, "blue"),
        ],
        "emendas_summary": [
            ("Maior execu??o territorial", "Use o mapa para ver onde o valor destinado se concentra."),
            ("Situa??o", "Cruze pago, empenhado e indicado para acompanhar pend?ncias."),
            ("Minist?rios", "Sa?de, MIDR, Educa??o e Cidades ajudam a separar pauta por ?rea."),
            ("Confer?ncia", "Clique em cada munic?pio para ver objetos, situa??o e valores pagos."),
        ],
    }

    total_general = data["total_map"] + data["total_crm"]
    max_source = max(value for _, value, _ in data["sources"])
    max_profile = max(value for _, value, _ in data["profiles"])
    max_city = max(value for _, value, _ in data["cities"])
    max_status = max(value for _, value, _ in data["crm_status"])
    max_heat_city = max(value for _, value, _ in data["cities"])
    max_election = max(value for _, value, _, _ in data["election"]["cities"])
    max_emendas = max(value for _, value, _, _, _ in data["emendas"]["cities"])
    max_theme = max(value for _, value, _ in data["emendas"]["themes"])
    max_situation = max(value for _, value, _ in data["emendas"]["situations"])

    def map_points(rows, max_value, value_index=1, zone_index=2):
        points = []
        for row in rows:
            label = row[0]
            value = row[value_index]
            zone = row[zone_index]
            x, y = city_positions.get(label, (240, 260))
            radius = heat_radius(value, max_value)
            points.append({
                "city": label,
                "value": value,
                "zone": zone,
                "color": zone_colors.get(zone, "#94a3b8"),
                "x": x,
                "y": y,
                "halo": radius,
                "core": max(5, round(radius * 0.34, 1)),
                "label_x": min(x + radius + 8, 560),
            })
        return points

    context = {
        **data,
        "total_general": total_general,
        "phone_pct": pct(data["with_phone"], data["total_map"]),
        "city_pct": pct(data["total_map"] - data["without_city"], data["total_map"]),
        "map_share": pct(data["total_map"], total_general),
        "crm_share": pct(data["total_crm"], total_general),
        "sources_rows": [(label, value, color, width(value, max_source)) for label, value, color in data["sources"]],
        "profile_rows": [(label, value, color, width(value, max_profile)) for label, value, color in data["profiles"]],
        "city_rows": [(label, value, zone, width(value, max_city)) for label, value, zone in data["cities"]],
        "heat_points": map_points(data["cities"], max_heat_city),
        "election_rows": [(label, value, zone, percent, width(value, max_election)) for label, value, zone, percent in data["election"]["cities"]],
        "election_points": map_points(data["election"]["cities"], max_election),
        "emendas_rows": [(label, value, zone, quantity, paid, width(value, max_emendas)) for label, value, zone, quantity, paid in data["emendas"]["cities"]],
        "emendas_points": map_points(data["emendas"]["cities"], max_emendas),
        "theme_rows": [(label, value, color, width(value, max_theme)) for label, value, color in data["emendas"]["themes"]],
        "situation_rows": [(label, value, color, width(value, max_situation)) for label, value, color in data["emendas"]["situations"]],
        "emendas_paid_pct": pct(data["emendas"]["paid_value"], data["emendas"]["total_value"]),
        "status_rows": [(label, value, color, width(value, max_status)) for label, value, color in data["crm_status"]],
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
