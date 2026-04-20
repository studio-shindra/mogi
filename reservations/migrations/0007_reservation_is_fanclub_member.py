from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reservations", "0006_accesslink"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="is_fanclub_member",
            field=models.BooleanField(default=False, verbose_name="FC会員"),
        ),
    ]
