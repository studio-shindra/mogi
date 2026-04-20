from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reservations", "0003_alter_reservation_reservation_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="sales_channel",
            field=models.CharField(
                choices=[
                    ("advance", "先行"),
                    ("general", "一般"),
                    ("staff", "関係者"),
                    ("invite", "招待"),
                    ("hold", "取り置き"),
                    ("walk_in", "当日券"),
                ],
                default="general",
                max_length=10,
                verbose_name="販売区分",
            ),
        ),
    ]
