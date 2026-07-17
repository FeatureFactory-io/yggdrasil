"""Drop Stereotype/Package.model; finalize Model.metamodel FK."""

from __future__ import annotations

from typing import ClassVar

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies: ClassVar[list] = [
        ("graph", "0002_metamodel_first_class"),
    ]

    operations: ClassVar[list] = [
        migrations.AlterUniqueTogether(
            name="stereotype",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="package",
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name="stereotype",
            name="model",
        ),
        migrations.RemoveField(
            model_name="package",
            name="model",
        ),
        migrations.AlterField(
            model_name="stereotype",
            name="metamodel",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="stereotypes",
                to="graph.metamodel",
            ),
        ),
        migrations.AlterField(
            model_name="package",
            name="metamodel",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="packages",
                to="graph.metamodel",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="stereotype",
            unique_together={("metamodel", "slug")},
        ),
        migrations.AlterUniqueTogether(
            name="package",
            unique_together={("metamodel", "slug")},
        ),
        migrations.RemoveField(
            model_name="yggdrasilmodel",
            name="metamodel",
        ),
        migrations.RenameField(
            model_name="yggdrasilmodel",
            old_name="metamodel_fk",
            new_name="metamodel",
        ),
        migrations.AlterField(
            model_name="yggdrasilmodel",
            name="metamodel",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="models",
                to="graph.metamodel",
            ),
        ),
    ]
