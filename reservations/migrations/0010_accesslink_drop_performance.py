import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reservations", "0009_accesslink_backfill_event"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="accesslink",
            name="performance",
        ),
        migrations.AlterField(
            model_name="accesslink",
            name="event",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="access_links",
                to="events.event",
                verbose_name="作品",
            ),
        ),
    ]
