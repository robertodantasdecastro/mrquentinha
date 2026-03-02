from django.db import migrations


def _normalize_digits(value: str) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _hash_value(value: str, salt: str) -> str:
    import hashlib

    normalized = str(value or "").strip()
    if not normalized:
        return ""
    payload = f"{salt}:{normalized}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def encrypt_profile_fields(apps, schema_editor):
    UserProfile = apps.get_model("accounts", "UserProfile")
    from django.conf import settings

    salt = str(getattr(settings, "FIELD_HASH_SALT", "") or "").strip()
    for profile in UserProfile.objects.all().iterator():
        # Reatribui valores para acionar criptografia nos campos alterados
        profile.phone = profile.phone or ""
        profile.secondary_phone = profile.secondary_phone or ""
        profile.cpf = profile.cpf or ""
        profile.cnpj = profile.cnpj or ""
        profile.rg = profile.rg or ""
        profile.postal_code = profile.postal_code or ""
        profile.street = profile.street or ""
        profile.street_number = profile.street_number or ""
        profile.address_complement = profile.address_complement or ""
        profile.neighborhood = profile.neighborhood or ""
        profile.city = profile.city or ""
        profile.state = profile.state or ""
        profile.document_number = profile.document_number or ""
        profile.document_issuer = profile.document_issuer or ""

        profile.cpf_hash = _hash_value(_normalize_digits(profile.cpf), salt)
        profile.cnpj_hash = _hash_value(_normalize_digits(profile.cnpj), salt)
        profile.rg_hash = _hash_value(_normalize_digits(profile.rg), salt)
        profile.document_number_hash = _hash_value(
            _normalize_digits(profile.document_number), salt
        )
        profile.phone_hash = _hash_value(_normalize_digits(profile.phone), salt)

        profile.save(
            update_fields=[
                "phone",
                "secondary_phone",
                "cpf",
                "cnpj",
                "rg",
                "postal_code",
                "street",
                "street_number",
                "address_complement",
                "neighborhood",
                "city",
                "state",
                "document_number",
                "document_issuer",
                "cpf_hash",
                "cnpj_hash",
                "rg_hash",
                "document_number_hash",
                "phone_hash",
                "updated_at",
            ]
        )


def decrypt_profile_fields(apps, schema_editor):
    # Sem reversao: manter valores criptografados.
    return


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_customergovernanceprofile_email_login_allowed_dev_and_more"),
    ]

    operations = [
        migrations.RunPython(encrypt_profile_fields, decrypt_profile_fields),
    ]
