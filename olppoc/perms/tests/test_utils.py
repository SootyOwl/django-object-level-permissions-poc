"""Tests for the utils module in the perms app."""
import pytest
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db.models import Q
from installs.models import Install, Location
from perms.utils import (
    get_filter_from_constraints,
    get_perm_name,
    resolve_contenttype_from_perm,
    resolve_perm,
    modify_object_safely
)

User = get_user_model()


@pytest.mark.parametrize(
    "constraints, expected",
    [
        # empty constraints
        ([], Q()),
        # single constraint
        ([{"a": 1}], Q(a=1)),
        # a complex constraint (AND)
        ([{"a": 1, "b": 2}], Q(a=1) & Q(b=2)),
        # multiple constraints (OR)
        ([{"a": 1}, {"b": 2}], Q(a=1) | Q(b=2)),
        # null constraint
        ([None], Q()),
        # null constraint with other constraints (null constraint should be ignored)
        ([{"a": 1}, None, {"b": 2}], Q(a=1) | Q(b=2)),
    ],
)
def test_get_filter_from_constraints(constraints, expected):
    """Test get_filter_from_constraints."""
    assert get_filter_from_constraints(constraints) == expected


@pytest.mark.parametrize(
    "perm, expected",
    [
        ("installs.add_install", ("installs", "add", "install")),
        ("installs.change_install", ("installs", "change", "install")),
        ("installs.delete_install", ("installs", "delete", "install")),
        ("installs.view_install", ("installs", "view", "install")),
        ("installs.add_location", ("installs", "add", "location")),
        ("installs.change_location", ("installs", "change", "location")),
        ("installs.delete_location", ("installs", "delete", "location")),
        ("installs.view_location", ("installs", "view", "location")),
    ],
)
def test_resolve_perm(perm, expected):
    """Test resolve_perm."""
    assert resolve_perm(perm) == expected


@pytest.mark.parametrize(
    "model, action, expected",
    [
        (Install, "add", "installs.add_install"),
        (Install, "change", "installs.change_install"),
        (Install, "delete", "installs.delete_install"),
        (Install, "view", "installs.view_install"),
        (Location, "add", "installs.add_location"),
        (Location, "change", "installs.change_location"),
        (Location, "delete", "installs.delete_location"),
        (Location, "view", "installs.view_location"),
    ],
)
def test_get_perm_name(model, action, expected):
    """Test get_perm_name."""
    assert get_perm_name(model, action) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "perm, model, expected_action",
    [
        ("installs.add_install", Install, "add"),
        ("installs.change_install", Install, "change"),
        ("installs.delete_install", Install, "delete"),
        ("installs.view_install", Install, "view"),
        ("installs.add_location", Location, "add"),
        ("installs.change_location", Location, "change"),
        ("installs.delete_location", Location, "delete"),
        ("installs.view_location", Location, "view"),
    ],
)
def test_resolve_contenttype_from_perm(perm, model, expected_action):
    """Test resolve_contenttype_from_perm."""
    content_type, action = resolve_contenttype_from_perm(perm)
    assert content_type == ContentType.objects.get_for_model(model)
    assert action == expected_action


def test_resolve_contenttype_from_perm_invalid():
    """Test resolve_contenttype_from_perm with an invalid permission."""
    with pytest.raises(ValueError):
        resolve_contenttype_from_perm("installs.invalid")


@pytest.mark.django_db
def test_resolve_contenttype_from_perm_invalid_format():
    """Test resolve_contenttype_from_perm with an invalid format."""
    with pytest.raises(ValueError):
        resolve_contenttype_from_perm("installs.invalid_format")


from django.core.exceptions import PermissionDenied

@pytest.mark.django_db
def test_modify_object_safely():
    """Test modify_object_safely.
    
    1. Set up a user with objectpermissions to add and change locations with a constraint on the "name" field.
    2. Create a location with a name that matches the constraint.
    3. Attempt to update the location with a name that does not match the constraint by calling modify_object_safely.
    4. The update should fail and the location should not be updated.
    """
    # 1. Set up a user with permissions to add and change installs with a constraint on the "name" field.
    user = User.objects.create_user(email="user@example.com", password="password")
    user.objectpermissions.create(
        name="Add and change installs with 'Test' in the name",
        actions=["add", "change"],
        constraints=[{"name__icontains": "Test"}],
    )
    user.objectpermissions.first().object_types.add(
        ContentType.objects.get_for_model(Location)
    )
    # 2. Create a location with a name that matches the constraint.
    location = Location.objects.create(name="Test Location")
    # 3. Attempt to update the location with a name that does not match the constraint by calling modify_object_safely.
    with pytest.raises(PermissionDenied):
        modify_object_safely(location, user, {"name": "New Location Name"})
    # 4. The update should fail and the location should not be updated.
    assert Location.objects.get(pk=location.pk).name == "Test Location"

    # attempt to update the location with a name that matches the constraint
    obj = modify_object_safely(location, user, {"name": "New Test Location Name"})
    assert Location.objects.get(pk=location.pk).name == "New Test Location Name"
    assert obj.name == "New Test Location Name"
    assert obj == location