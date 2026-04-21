from django.db import migrations, models


FORWARD_MAP = {
    "front_row": "row_a",
    "front": "row_b",
    "center": "row_c",
    "rear": "row_d_bench",
}

BACKWARD_MAP = {v: k for k, v in FORWARD_MAP.items()}


def forward(apps, schema_editor):
    SeatTier = apps.get_model("events", "SeatTier")
    for old, new in FORWARD_MAP.items():
        SeatTier.objects.filter(code=old).update(code=new)


def backward(apps, schema_editor):
    SeatTier = apps.get_model("events", "SeatTier")
    # row_e_bench は旧 choices に存在しないため、旧コードに戻せるもののみ戻す
    for new, old in BACKWARD_MAP.items():
        SeatTier.objects.filter(code=new).update(code=old)


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0005_event_public_entry_enabled"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
        migrations.AlterField(
            model_name="seattier",
            name="code",
            field=models.CharField(
                choices=[
                    ("row_a", "A列"),
                    ("row_b", "B列"),
                    ("row_c", "C列"),
                    ("row_d_bench", "D列ベンチシート"),
                    ("row_e_bench", "E列ベンチシート"),
                ],
                max_length=20,
                verbose_name="席種コード",
            ),
        ),
    ]
