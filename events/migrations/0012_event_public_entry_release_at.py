from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0011_fix_staff_seat_flag"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="public_entry_release_at",
            field=models.DateTimeField(
                blank=True,
                help_text="指定するとこの日時以降に公開されます。空なら即時公開。",
                null=True,
                verbose_name="本URL公開予定日時",
            ),
        ),
    ]
