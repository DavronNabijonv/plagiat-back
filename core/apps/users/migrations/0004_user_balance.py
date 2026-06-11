from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_user_tg_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='balance',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=15,
            ),
        ),
    ]
