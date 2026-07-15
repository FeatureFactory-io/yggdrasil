"""
AutoFixture helpers — lazy test data creation (TFK-04).

Wraps FactoryBoy factories for one-call user creation by RBAC role.
"""

from tests.fixtures.autofixture.fixture_creator import (
    make_admin,
    make_architect,
    make_user,
    make_viewer,
)

__all__ = ["make_admin", "make_architect", "make_user", "make_viewer"]
