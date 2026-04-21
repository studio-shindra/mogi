from django.db import migrations


def backfill_event(apps, schema_editor):
    AccessLink = apps.get_model("reservations", "AccessLink")
    Performance = apps.get_model("events", "Performance")
    for link in AccessLink.objects.all():
        if link.performance_id and not link.event_id:
            perf = Performance.objects.get(pk=link.performance_id)
            link.event_id = perf.event_id
            link.save(update_fields=["event_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("reservations", "0008_accesslink_add_event"),
    ]

    operations = [
        migrations.RunPython(backfill_event, migrations.RunPython.noop),
    ]
