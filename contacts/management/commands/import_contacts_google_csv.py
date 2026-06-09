import csv
import io
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from contacts.importing import (
    build_external_id,
    bulk_save_contacts,
    clean_phone,
    clean_value,
    contact_from_indexes,
    infer_state,
    load_contact_indexes,
    pick_value,
    sync_contact_fields,
)
from contacts.models import Contact


def fetch_csv_rows(csv_source):
    local_path = Path(csv_source).expanduser()
    if local_path.exists():
        content = local_path.read_text(encoding="utf-8-sig")
    else:
        try:
            with urlopen(csv_source, timeout=30) as response:
                content = response.read().decode("utf-8-sig")
        except (UnicodeDecodeError, URLError) as exc:
            raise CommandError(
                "Nao consegui ler o CSV do Google. Confira se a aba foi publicada como CSV."
            ) from exc

    rows = csv.DictReader(io.StringIO(content))
    if not rows.fieldnames:
        raise CommandError("O CSV nao trouxe cabecalhos.")
    return rows


class Command(BaseCommand):
    help = "Importa contatos de um link CSV publicado no Google Planilhas."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_url",
            help="Link CSV publicado da aba Base Completa ou caminho de um CSV baixado.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula a importacao e desfaz as alteracoes no final.",
        )

    def handle(self, *args, **options):
        rows = fetch_csv_rows(options["csv_url"])
        totals = {"created": 0, "updated": 0, "skipped": 0}

        with transaction.atomic():
            contacts_by_external, contacts_by_phone = load_contact_indexes()
            created_contacts = []
            updated_contacts = {}
            for row_number, row in enumerate(rows, start=2):
                payload = {
                    clean_value(header): clean_value(value)
                    for header, value in row.items()
                    if clean_value(header)
                }
                if not any(payload.values()):
                    continue

                full_name = pick_value(payload, "full_name")
                phone = clean_phone(pick_value(payload, "phone"))
                if not full_name:
                    totals["skipped"] += 1
                    continue

                external_id = build_external_id(payload, row_number)
                fields = {
                    "external_id": external_id,
                    "full_name": full_name,
                    "phone": phone,
                    "city": pick_value(payload, "city"),
                    "state": infer_state(payload),
                    "neighborhood": pick_value(payload, "neighborhood"),
                    "profile": pick_value(payload, "profile"),
                    "source": pick_value(payload, "source"),
                    "notes_summary": pick_value(payload, "notes_summary"),
                    "source_payload": {
                        "workbook": "Google Planilhas",
                        "sheet": "Base Completa",
                        "row_number": row_number,
                        "responsavel": payload.get("RESPONSAVEL", "")
                        or payload.get("RESPONSÁVEL", ""),
                        "row": payload,
                    },
                }

                contact = contact_from_indexes(
                    external_id,
                    phone,
                    contacts_by_external,
                    contacts_by_phone,
                )
                if contact is None:
                    contact = Contact(**fields)
                    created_contacts.append(contact)
                    contacts_by_external[external_id] = contact
                    if phone:
                        contacts_by_phone[phone] = contact
                    totals["created"] += 1
                    continue

                if sync_contact_fields(contact, fields):
                    if contact.pk:
                        updated_contacts[contact.pk] = contact
                    totals["updated"] += 1

            bulk_save_contacts(created_contacts, updated_contacts)
            if options["dry_run"]:
                transaction.set_rollback(True)

        mode = "Simulacao" if options["dry_run"] else "Importacao"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode} concluida: {totals['created']} criados, "
                f"{totals['updated']} atualizados, {totals['skipped']} ignorados."
            )
        )
        self.stdout.write("Origem usada: CSV publicado do Google Planilhas.")
