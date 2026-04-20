import django.db.models.deletion
from django.db import migrations, models

import reservations.models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0003_event_flyer_image_url"),
        ("reservations", "0005_alter_reservation_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessLink",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "token",
                    models.CharField(
                        default=reservations.models._generate_link_token,
                        max_length=32,
                        unique=True,
                        verbose_name="トークン",
                    ),
                ),
                (
                    "mode",
                    models.CharField(
                        choices=[
                            ("reservation", "予約"),
                            ("application", "応募"),
                        ],
                        max_length=12,
                        verbose_name="モード",
                    ),
                ),
                (
                    "sales_channel",
                    models.CharField(
                        choices=[
                            ("advance", "先行"),
                            ("general", "一般"),
                            ("staff", "関係者"),
                            ("invite", "招待"),
                            ("hold", "取り置き"),
                            ("walk_in", "当日券"),
                        ],
                        default="advance",
                        max_length=10,
                        verbose_name="販売区分",
                    ),
                ),
                ("label", models.CharField(max_length=100, verbose_name="ラベル")),
                ("is_active", models.BooleanField(default=True, verbose_name="有効")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "performance",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_links",
                        to="events.performance",
                        verbose_name="公演",
                    ),
                ),
            ],
            options={
                "verbose_name": "限定URL",
                "verbose_name_plural": "限定URL",
                "ordering": ["-created_at"],
            },
        ),
    ]
