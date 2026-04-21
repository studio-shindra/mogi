import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0004_alter_seattier_price_card_alter_seattier_price_cash"),
        ("reservations", "0007_reservation_is_fanclub_member"),
    ]

    operations = [
        migrations.AddField(
            model_name="accesslink",
            name="event",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="access_links_new",
                to="events.event",
                verbose_name="作品",
            ),
        ),
    ]
