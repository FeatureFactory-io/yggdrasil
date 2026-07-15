"""
FactoryBoy factory for Django's built-in ``User`` model.

RBAC roles (SAO.md §13: ``admin`` / ``architect`` / ``viewer``) are not yet
modeled as first-class objects — the ``auth`` app has no models yet
(placeholder ``TokenAuthentication`` only, see
``src/yggdrasil/auth/authentication.py``). Until a real role model ships,
roles are approximated with Django's built-in permission flags plus
``Group`` membership, so tests can be written against the *intended* RBAC
shape without blocking on it.

Update this factory (and its traits) once the ``auth`` app ships real
role models — do not let this placeholder silently drift from behavior.
"""

from __future__ import annotations

import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """
    Build a ``User`` with sensible unique defaults.

    :Example:

    >>> viewer = UserFactory()
    >>> admin = UserFactory(is_admin=True)
    >>> architect = UserFactory(is_architect=True)
    """

    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        """Attach the user to a named ``Group`` (e.g. "architect", "viewer").

        :param extracted: group name, or list of group names, passed either
            directly (``UserFactory(groups="architect")``) or via a trait
            (``is_architect=True``).
        """
        if not create or not extracted:
            return
        names = [extracted] if isinstance(extracted, str) else extracted
        for name in names:
            group, _ = Group.objects.get_or_create(name=name)
            self.groups.add(group)

    class Params:
        is_admin = factory.Trait(is_staff=True, is_superuser=True)
        is_architect = factory.Trait(groups="architect")
        is_viewer = factory.Trait(groups="viewer")
