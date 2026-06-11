from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

PROVIDER_CHOICES = [
    ('multicard', 'Multicard'),
    ('balance',   'Balans'),
    ('payme',     'Payme'),
    ('click',     'Click'),
    ('uzum',      'Uzum'),
]


class Migration(migrations.Migration):

    dependencies = [
        (
            'shared',
            '0016_order_payment_provider_clicktransaction'
            '_uzumtransaction',
        ),
        ('users', '0004_user_balance'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Order.payment_provider choices ni yangilash
        migrations.AlterField(
            model_name='order',
            name='payment_provider',
            field=models.CharField(
                blank=True,
                choices=PROVIDER_CHOICES,
                max_length=20,
                null=True,
            ),
        ),

        # BalanceTopup modeli
        migrations.CreateModel(
            name='BalanceTopup',
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
                    'amount',
                    models.DecimalField(decimal_places=2, max_digits=15),
                ),
                ('is_applied', models.BooleanField(default=False)),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='topups',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={'abstract': False},
        ),

        # MulticardTransaction modeli
        migrations.CreateModel(
            name='MulticardTransaction',
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
                    models.CharField(
                        blank=True, max_length=255, null=True, unique=True
                    ),
                ),
                (
                    'amount',
                    models.DecimalField(decimal_places=2, max_digits=15),
                ),
                (
                    'state',
                    models.IntegerField(
                        choices=[(1, "Yaratildi"), (2, "To'landi"),
                                 (-1, 'Bekor qilindi')],
                        default=1,
                    ),
                ),
                (
                    'order',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='multicard_transactions',
                        to='shared.order',
                    ),
                ),
                (
                    'topup',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='multicard_transactions',
                        to='shared.balancetopup',
                    ),
                ),
            ],
            options={'abstract': False},
        ),
    ]
