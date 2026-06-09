import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal

from contacts.models import Contact


HEADER_ALIASES = {
    "external_id": ("id", "codigo", "código"),
    "full_name": ("nome completo", "nome", "lead"),
    "phone": ("telefone", "tel", "whatsapp", "numero", "número"),
    "city": ("cidade", "municipio", "município"),
    "state": ("estado", "uf"),
    "neighborhood": ("bairro",),
    "profile": ("perfil", "tipo de apoio"),
    "source": ("fonte", "origem"),
    "notes_summary": ("observacao", "observação", "observacoes", "observações", "obs"),
    "locality_type": ("tipo localidade", "tipo de localidade"),
}


def clean_value(value):
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        value = str(value)
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0", text):
        return text[:-2]
    return text


def normalize_label(value):
    value = clean_value(value).lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def clean_phone(value):
    digits = re.sub(r"\D", "", clean_value(value))
    return digits if len(digits) >= 8 else ""


def pick_value(payload, field):
    aliases = {normalize_label(alias) for alias in HEADER_ALIASES[field]}
    for header, value in payload.items():
        if normalize_label(header) in aliases and clean_value(value):
            return clean_value(value)
    return ""


def build_external_id(payload, row_number):
    spreadsheet_id = pick_value(payload, "external_id")
    phone = clean_phone(pick_value(payload, "phone"))
    if spreadsheet_id:
        return f"base-completa:{spreadsheet_id}"
    if phone:
        return f"base-completa:telefone:{phone}"
    return f"base-completa:linha:{row_number}"


def infer_state(payload):
    state = pick_value(payload, "state").upper()[:2]
    if state:
        return state
    locality_type = normalize_label(pick_value(payload, "locality_type"))
    return "" if "fora do ms" in locality_type else "MS"


def find_existing_contact(external_id, phone):
    contact = Contact.objects.filter(external_id=external_id).first()
    if contact or not external_id.endswith(f"telefone:{phone}"):
        return contact
    return Contact.objects.filter(phone=phone).first()


def contact_from_indexes(external_id, phone, contacts_by_external, contacts_by_phone):
    contact = contacts_by_external.get(external_id)
    if contact is not None:
        return contact
    if external_id.endswith(f"telefone:{phone}") and phone:
        return contacts_by_phone.get(phone)
    return None


CONTACT_SYNC_FIELDS = (
    "external_id",
    "full_name",
    "phone",
    "city",
    "state",
    "neighborhood",
    "profile",
    "source",
    "notes_summary",
    "source_payload",
)


def load_contact_indexes():
    contacts = Contact.objects.all()
    return (
        {contact.external_id: contact for contact in contacts if contact.external_id},
        {contact.phone: contact for contact in contacts if contact.phone},
    )


def sync_contact_fields(contact, fields):
    changed = False
    for field, value in fields.items():
        if getattr(contact, field) != value:
            setattr(contact, field, value)
            changed = True
    return changed


def bulk_save_contacts(created_contacts, updated_contacts):
    Contact.objects.bulk_create(created_contacts, batch_size=1000)
    Contact.objects.bulk_update(
        list(updated_contacts.values()),
        fields=CONTACT_SYNC_FIELDS,
        batch_size=1000,
    )
