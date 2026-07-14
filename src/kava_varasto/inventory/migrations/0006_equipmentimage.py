from pathlib import PurePosixPath

import django.db.models.deletion
from django.db import migrations, models


def create_images_from_paths(apps, schema_editor):
    Equipment = apps.get_model("inventory", "Equipment")
    EquipmentImage = apps.get_model("inventory", "EquipmentImage")
    for equipment in Equipment.objects.exclude(old_image=""):
        image, _created = EquipmentImage.objects.get_or_create(
            image=equipment.old_image,
            defaults={"name": PurePosixPath(equipment.old_image).stem[:100]},
        )
        equipment.image = image
        equipment.save(update_fields=["image"])


def restore_paths_from_images(apps, schema_editor):
    Equipment = apps.get_model("inventory", "Equipment")
    for equipment in Equipment.objects.filter(image__isnull=False):
        equipment.old_image = equipment.image.image
        equipment.save(update_fields=["old_image"])


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0005_equipment_image"),
    ]

    operations = [
        migrations.CreateModel(
            name="EquipmentImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="name")),
                ("image", models.ImageField(upload_to="equipment/", verbose_name="image")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True, verbose_name="uploaded at")),
            ],
            options={
                "verbose_name": "equipment image",
                "verbose_name_plural": "equipment images",
                "ordering": ["name"],
            },
        ),
        migrations.RenameField(
            model_name="equipment",
            old_name="image",
            new_name="old_image",
        ),
        migrations.AddField(
            model_name="equipment",
            name="image",
            field=models.ForeignKey(
                blank=True,
                help_text="Optional photo shown in the storage detail view.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="equipment",
                to="inventory.equipmentimage",
                verbose_name="image",
            ),
        ),
        migrations.RunPython(create_images_from_paths, restore_paths_from_images),
        migrations.RemoveField(
            model_name="equipment",
            name="old_image",
        ),
    ]
