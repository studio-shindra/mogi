from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reservations", "0010_accesslink_drop_performance"),
    ]

    operations = [
        migrations.AddField(
            model_name="accesslink",
            name="header_image_url",
            field=models.URLField(
                blank=True,
                max_length=500,
                verbose_name="ヘッダー画像URL",
            ),
        ),
    ]
