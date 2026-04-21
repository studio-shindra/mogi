from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0004_alter_seattier_price_card_alter_seattier_price_cash"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="public_entry_enabled",
            field=models.BooleanField(default=True, verbose_name="本URL公開"),
        ),
    ]
