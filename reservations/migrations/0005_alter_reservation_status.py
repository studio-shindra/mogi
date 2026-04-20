from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reservations", "0004_reservation_sales_channel"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reservation",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "仮受付"),
                    ("pending", "仮予約"),
                    ("applied", "応募"),
                    ("confirmed", "確定"),
                    ("cancelled", "キャンセル"),
                ],
                default="pending",
                max_length=10,
                verbose_name="ステータス",
            ),
        ),
    ]
