from django.db import migrations, models
import django.db.models.deletion

PROVIDER_CHOICES = [
    ('payme', 'Payme'),
    ('click', 'Click'),
    ('uzum', 'Uzum'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('shared', '0015_alter_order_ai_document_alter_order_document'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_provider',
            field=models.CharField(
                blank=True,
                choices=PROVIDER_CHOICES,
                max_length=20,
                null=True,
            ),
        ),
        migrations.CreateModel(
            name='ClickTransaction',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'click_trans_id',
                    models.CharField(max_length=100, unique=True),
                ),
                ('service_id', models.CharField(max_length=100)),
                (
                    'amount',
                    models.DecimalField(decimal_places=2, max_digits=15),
                ),
                ('state', models.IntegerField(default=0)),
                ('error', models.IntegerField(default=0)),
                ('error_note', models.CharField(blank=True, max_length=255)),
                ('sign_time', models.CharField(blank=True, max_length=50)),
                (
                    'order',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='click_transactions',
                        to='shared.order',
                    ),
                ),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='UzumTransaction',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'transaction_id',
                    models.CharField(max_length=100, unique=True),
                ),
                (
                    'amount',
                    models.DecimalField(decimal_places=2, max_digits=15),
                ),
                ('state', models.IntegerField(default=1)),
                ('error', models.IntegerField(default=0)),
                ('error_note', models.CharField(blank=True, max_length=255)),
                (
                    'order',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='uzum_transactions',
                        to='shared.order',
                    ),
                ),
            ],
            options={'abstract': False},
        ),
    ]
