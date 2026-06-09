import csv
import io
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from contacts.importing import clean_phone, clean_value
from contacts.models import Contact


LUVA_FIELDS = (
    "id",
    "nome",
    "descricao",
    "responsavel",
    "data_de_criacao",
    "fonte",
    "status",
    "ultimo_contato",
    "telefone",
    "genero",
    "cidade",
    "estado",
    "tags",
    "empresa",
    "funil_etapa",
)


def read_csv_rows(path):
    try:
        content = Path(path).expanduser().read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise CommandError(f"Nao consegui abrir o CSV do Luva: {path}") from exc

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise CommandError("O CSV do Luva nao trouxe cabecalhos.")
    return list(reader)


def phone_variants(phone):
    digits = clean_phone(phone)
    variants = {digits} if digits else set()
    if digits.startswith("55") and len(digits) > 11:
        variants.add(digits[2:])
    if digits and not digits.startswith("55") and len(digits) in (10, 11):
        variants.add(f"55{digits}")
    return {value for value in variants if value}


def has_real_name(value):
    text = clean_value(value)
    letters = re.findall(r"[A-Za-zÀ-ÿ]", text)
    return len(letters) >= 2


def build_phone_index():
    index = {}
    duplicates = set()
    for contact in Contact.objects.exclude(phone=""):
        for phone in phone_variants(contact.phone):
            if phone in index and index[phone].pk != contact.pk:
                duplicates.add(phone)
                continue
            index[phone] = contact

    for phone in duplicates:
        index.pop(phone, None)
    return index


def build_luva_id_index():
    index = {}
    for contact in Contact.objects.all().only("external_id", "source_payload"):
        if contact.external_id.startswith("crm-luva:"):
            index[contact.external_id.removeprefix("crm-luva:")] = contact
        luva_id = (contact.source_payload or {}).get("crm_luva", {}).get("id")
        if luva_id:
            index[str(luva_id)] = contact
    return index


def compact_luva_payload(row):
    return {field: clean_value(row.get(field, "")) for field in LUVA_FIELDS}


def build_source_payload(row, name_review_required):
    return {
        "crm_luva": compact_luva_payload(row),
        "name_review_required": name_review_required,
    }


class Command(BaseCommand):
    help = "Vincula contatos ja importados aos dados originais do CRM Luva."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Caminho do CSV exportado do Luva.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula a vinculacao e desfaz as alteracoes no final.",
        )

    def handle(self, *args, **options):
        rows = read_csv_rows(options["csv_path"])
        phone_index = build_phone_index()
        luva_id_index = build_luva_id_index()
        totals = {
            "matched": 0,
            "created": 0,
            "updated": 0,
            "missing_phone": 0,
            "not_found": 0,
            "name_review": 0,
        }

        with transaction.atomic():
            for row in rows:
                luva_phone = row.get("telefone", "")
                if not clean_phone(luva_phone):
                    totals["missing_phone"] += 1
                    continue

                luva_id = clean_value(row.get("id", ""))
                contact = luva_id_index.get(luva_id) if luva_id else None
                for phone in phone_variants(luva_phone):
                    if contact:
                        break
                    contact = phone_index.get(phone)
                    if contact:
                        break

                luva_name = clean_value(row.get("nome", ""))
                luva_name_ok = has_real_name(luva_name)
                name_review_required = not luva_name_ok

                if not contact:
                    contact = Contact(
                        external_id=f"crm-luva:{clean_value(row.get('id', '')) or clean_phone(luva_phone)}",
                        full_name=luva_name if luva_name else "Nome para revisar",
                        phone=clean_phone(luva_phone),
                        city=clean_value(row.get("cidade", "")),
                        state=clean_value(row.get("estado", "MS")).upper()[:2] or "MS",
                        profile=clean_value(row.get("status", "")),
                        source="CRM Luva",
                        notes_summary=clean_value(row.get("descricao", "")),
                        source_payload=build_source_payload(row, name_review_required),
                    )
                    contact.save()
                    if luva_id:
                        luva_id_index[luva_id] = contact
                    for phone in phone_variants(luva_phone):
                        phone_index.setdefault(phone, contact)
                    totals["created"] += 1
                    if name_review_required:
                        totals["name_review"] += 1
                    continue

                totals["matched"] += 1
                payload = dict(contact.source_payload or {})
                current_name_ok = has_real_name(contact.full_name)
                payload["name_review_required"] = not current_name_ok
                payload["crm_luva"] = compact_luva_payload(row)

                changed_fields = []
                if payload != contact.source_payload:
                    contact.source_payload = payload
                    changed_fields.append("source_payload")

                if not current_name_ok and luva_name_ok and contact.full_name != luva_name:
                    contact.full_name = luva_name
                    contact.source_payload["name_review_required"] = False
                    changed_fields.append("full_name")
                    current_name_ok = True

                if not contact.notes_summary and clean_value(row.get("descricao", "")):
                    contact.notes_summary = clean_value(row.get("descricao", ""))
                    changed_fields.append("notes_summary")

                if not current_name_ok:
                    totals["name_review"] += 1

                if changed_fields:
                    contact.save(update_fields=sorted(set(changed_fields + ["updated_at"])))
                    totals["updated"] += 1

            if options["dry_run"]:
                transaction.set_rollback(True)

        mode = "Simulacao" if options["dry_run"] else "Vinculacao"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode} concluida: {totals['matched']} encontrados, "
                f"{totals['created']} criados, "
                f"{totals['updated']} atualizados, "
                f"{totals['name_review']} nomes para revisar."
            )
        )
        self.stdout.write(
            f"Sem telefone: {totals['missing_phone']} | "
            f"Nao encontrados no banco: {totals['not_found']}"
        )
