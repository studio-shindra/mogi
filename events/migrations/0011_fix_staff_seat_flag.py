from django.db import migrations


def set_staff_seat_flag(apps, schema_editor):
    """code='staff_seat' のレコードを is_staff_only=True に揃える。
    0010 で invite→staff_seat にリネームした既存データが is_staff_only=False のまま
    残っており、公開APIに漏れていた問題を修正する。
    """
    SeatTier = apps.get_model("events", "SeatTier")
    SeatTier.objects.filter(code="staff_seat").update(is_staff_only=True)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0010_rename_invite_to_staff_seat"),
    ]

    operations = [
        migrations.RunPython(set_staff_seat_flag, noop),
    ]
