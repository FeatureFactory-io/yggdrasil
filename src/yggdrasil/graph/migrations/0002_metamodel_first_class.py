"""Add Metamodel and re-parent Stereotype/Package data onto it."""

from __future__ import annotations

from typing import ClassVar

import django.db.models.deletion
from django.db import migrations, models
from django.utils.text import slugify

C4_ELEMENT_STEREOTYPES = ("System", "Container", "Component", "Person", "External")
C4_EDGE_STEREOTYPES = ("calls", "depends_on", "uses")
C4_PACKAGES = ("Context", "Technology", "Application", "Code")


def forwards_reparent(apps, schema_editor) -> None:
    """Seed C4 Metamodel, remap stereotypes/packages, bind Models to Metamodel."""
    Metamodel = apps.get_model("graph", "Metamodel")
    YggdrasilModel = apps.get_model("graph", "YggdrasilModel")
    Stereotype = apps.get_model("graph", "Stereotype")
    Package = apps.get_model("graph", "Package")
    Element = apps.get_model("graph", "Element")
    Relationship = apps.get_model("graph", "Relationship")
    Diagram = apps.get_model("graph", "Diagram")

    mm, _ = Metamodel.objects.get_or_create(
        slug="c4",
        defaults={
            "name": "C4",
            "description": "C4 architecture metamodel (Context, Container, Component, Code).",
        },
    )

    shared_stereotypes: dict[str, object] = {}
    for name in C4_ELEMENT_STEREOTYPES:
        st, _ = Stereotype.objects.get_or_create(
            metamodel=mm,
            slug=slugify(name),
            defaults={"name": name, "is_edge": False, "model": None},
        )
        shared_stereotypes[st.slug] = st
    for name in C4_EDGE_STEREOTYPES:
        st, _ = Stereotype.objects.get_or_create(
            metamodel=mm,
            slug=slugify(name),
            defaults={"name": name, "is_edge": True, "model": None},
        )
        shared_stereotypes[st.slug] = st

    shared_packages: dict[str, object] = {}
    for name in C4_PACKAGES:
        pkg, _ = Package.objects.get_or_create(
            metamodel=mm,
            slug=slugify(name),
            defaults={"name": name, "model": None},
        )
        shared_packages[pkg.slug] = pkg

    for model in YggdrasilModel.objects.all():
        old_slug = getattr(model, "metamodel", None) or "c4"
        target = Metamodel.objects.filter(slug=old_slug).first() or mm
        model.metamodel_fk_id = target.pk
        model.save(update_fields=["metamodel_fk"])

    for st in list(Stereotype.objects.filter(model__isnull=False)):
        shared = shared_stereotypes.get(st.slug)
        if shared is None:
            shared, _ = Stereotype.objects.get_or_create(
                metamodel=mm,
                slug=st.slug,
                defaults={
                    "name": st.name,
                    "is_edge": st.is_edge,
                    "property_schema": st.property_schema,
                    "allowed_edge_rules": st.allowed_edge_rules,
                    "color": st.color,
                    "icon": st.icon,
                    "model": None,
                },
            )
            shared_stereotypes[st.slug] = shared
        if st.pk != shared.pk:
            Element.objects.filter(stereotype_id=st.pk).update(stereotype_id=shared.pk)
            Relationship.objects.filter(stereotype_id=st.pk).update(stereotype_id=shared.pk)
            st.delete()
        else:
            st.metamodel = mm
            st.model = None
            st.save(update_fields=["metamodel", "model"])

    for pkg in list(Package.objects.filter(model__isnull=False)):
        shared = shared_packages.get(pkg.slug)
        if shared is None:
            shared, _ = Package.objects.get_or_create(
                metamodel=mm,
                slug=pkg.slug,
                defaults={
                    "name": pkg.name,
                    "description": pkg.description,
                    "parent": None,
                    "model": None,
                },
            )
            shared_packages[pkg.slug] = shared
        if pkg.pk != shared.pk:
            Element.objects.filter(package_id=pkg.pk).update(package_id=shared.pk)
            Diagram.objects.filter(package_id=pkg.pk).update(package_id=shared.pk)
            Package.objects.filter(parent_id=pkg.pk).update(parent_id=shared.pk)
            pkg.delete()
        else:
            pkg.metamodel = mm
            pkg.model = None
            pkg.save(update_fields=["metamodel", "model"])

    YggdrasilModel.objects.filter(metamodel_fk__isnull=True).update(metamodel_fk=mm)
    Stereotype.objects.filter(metamodel__isnull=True).update(metamodel=mm)
    Package.objects.filter(metamodel__isnull=True).update(metamodel=mm)


def backwards_noop(apps, schema_editor) -> None:
    """Irreversible data reshape."""


class Migration(migrations.Migration):
    # PostgreSQL rejects schema changes after DML in the same transaction
    # ("pending trigger events"). Run each op in its own transaction.
    atomic = False

    dependencies: ClassVar[list] = [
        ("graph", "0001_initial_graph_models"),
    ]

    operations: ClassVar[list] = [
        migrations.CreateModel(
            name="Metamodel",
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
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=200, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="stereotype",
            name="metamodel",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="stereotypes",
                to="graph.metamodel",
            ),
        ),
        migrations.AddField(
            model_name="package",
            name="metamodel",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="packages",
                to="graph.metamodel",
            ),
        ),
        migrations.AlterField(
            model_name="stereotype",
            name="model",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="stereotypes",
                to="graph.yggdrasilmodel",
            ),
        ),
        migrations.AlterField(
            model_name="package",
            name="model",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="packages",
                to="graph.yggdrasilmodel",
            ),
        ),
        migrations.AddField(
            model_name="yggdrasilmodel",
            name="metamodel_fk",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="models",
                to="graph.metamodel",
            ),
        ),
        migrations.RunPython(forwards_reparent, backwards_noop),
    ]
