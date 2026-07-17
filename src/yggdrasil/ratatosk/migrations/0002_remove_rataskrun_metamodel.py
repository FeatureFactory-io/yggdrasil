"""Drop denormalized RataskRun.metamodel — use run.model.metamodel.slug."""

from __future__ import annotations

from typing import ClassVar

from django.db import migrations


class Migration(migrations.Migration):
    dependencies: ClassVar[list] = [
        ("ratatosk", "0001_initial"),
        ("graph", "0003_metamodel_finalize_schema"),
    ]

    operations: ClassVar[list] = [
        migrations.RemoveField(
            model_name="rataskrun",
            name="metamodel",
        ),
    ]
