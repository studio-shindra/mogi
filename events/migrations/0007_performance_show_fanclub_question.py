from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0006_rename_seat_tier_codes"),
    ]

    operations = [
        migrations.AddField(
            model_name="performance",
            name="show_fanclub_question",
            field=models.BooleanField(default=True, verbose_name="FC会員欄を表示"),
        ),
    ]
