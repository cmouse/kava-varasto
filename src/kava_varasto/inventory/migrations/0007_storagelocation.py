import django.db.models.deletion
from django.db import migrations, models


def seed_and_backfill_kolo(apps, schema_editor):
    StorageLocation = apps.get_model("inventory", "StorageLocation")
    Equipment = apps.get_model("inventory", "Equipment")
    # Literal "Kolo", not inventory.models.DEFAULT_LOCATION_NAME -- migrations
    # must not import from the live models module.
    kolo, _created = StorageLocation.objects.get_or_create(name="Kolo")
    Equipment.objects.filter(location__isnull=True).update(location=kolo)


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0006_equipmentimage"),
    ]

    operations = [
        migrations.CreateModel(
            name="StorageLocation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="name")),
            ],
            options={
                "verbose_name": "storage location",
                "verbose_name_plural": "storage locations",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="equipment",
            name="location",
            field=models.ForeignKey(
                null=True,
                help_text="Where this equipment is physically kept.",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="equipment",
                to="inventory.storagelocation",
                verbose_name="storage location",
            ),
        ),
        migrations.RunPython(seed_and_backfill_kolo, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="equipment",
            name="location",
            field=models.ForeignKey(
                help_text="Where this equipment is physically kept.",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="equipment",
                to="inventory.storagelocation",
                verbose_name="storage location",
            ),
        ),
    ]
