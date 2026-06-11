from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shared', '0017_balance_topup_multicard_transaction'),
    ]

    operations = [
        migrations.DeleteModel(name='ClickTransaction'),
        migrations.DeleteModel(name='UzumTransaction'),
        migrations.AlterField(
            model_name='order',
            name='payment_provider',
            field=models.CharField(
                blank=True,
                choices=[
                    ('multicard', 'Multicard'),
                    ('balance', 'Balans'),
                    ('payme', 'Payme'),
                ],
                max_length=20,
                null=True,
            ),
        ),
    ]
