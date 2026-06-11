from django.db import migrations

DOCUMENT_TYPES = [
    "Mashqlar to'plami",
    "asarlar to'plami",
    "Ta'lim vizua nashri",
    "Bitiruvchi ish",
    "Diplom loyihasi",
    "maqola",
    "Falsafa doktorligi dissertatsiyasi",
    "Qo'llanma",
    "Darslik",
    "Kitob",
    "Nomzodlik dissertatsiyasi",
    "Doktorlik dissertatsiyasi",
    "Yakuniy saralash ishi",
    "Ko'rsatmalar",
    "Doktorlik dissertatsiyasi referati fan nomzodi",
    "O'quv qo'llanma",
    "Referat",
    "Kurs ishi",
    "Doktorlik dissertatsiya referati",
]


def seed_document_types(apps, schema_editor):
    DocumentType = apps.get_model('shared', 'DocumentType')
    for name in DOCUMENT_TYPES:
        DocumentType.objects.get_or_create(name=name)


def unseed_document_types(apps, schema_editor):
    DocumentType = apps.get_model('shared', 'DocumentType')
    DocumentType.objects.filter(name__in=DOCUMENT_TYPES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('shared', '0019_alter_balancetopup_id_alter_multicardtransaction_id'),
    ]

    operations = [
        migrations.RunPython(seed_document_types, unseed_document_types),
    ]
