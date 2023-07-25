import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from installs.models import Install, Location
from perms.models import ObjectPermission

User = get_user_model()


@pytest.fixture
def user_factory(db):
    def create_user(email=None, password=None):
        if not email:
            email = "default@example.com"
        if not password:
            password = "password"
        return User.objects.create_user(email=email, password=password)

    return create_user


@pytest.fixture
def location_factory(db):
    def create_location(name=None):
        if not name:
            name = "Test Location"
        return Location.objects.create(name=name)

    return create_location


@pytest.fixture
def install_factory(db, location_factory):
    def create_install(name=None):
        if not name:
            name = "Test Install"
        location = location_factory()
        return Install.objects.create(name=name, location=location)

    return create_install


@pytest.mark.django_db
def test_assign_model_level_permission(user_factory):
    """Test assigning a permission to a user for a model.

    GIVEN a user
    WHEN a permission is assigned to the user for a model
    THEN the user has the permission for the model
    """
    user = user_factory()
    # assert that the user does not have the permission yet
    assert not user.has_perm("installs.view_location")

    obj_perm = ObjectPermission(
        name="Test permission",
        enabled=True,
        actions=["view"],
    )
    obj_perm.save()
    obj_perm.users.add(user)
    obj_perm.object_types.add(ContentType.objects.get_for_model(Location))

    # assert that the permission exists in the database
    assert ObjectPermission.objects.filter(
        name="Test permission",
        enabled=True,
        actions=["view"],
    ).exists(), "The permission was not created."

    # check that the user has the permission now
    user = User.objects.get(
        pk=user.pk
    )  # refresh the user object entirely to get the new permissions cache
    assert user.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."

    # check that the user does not have the permission for a different model
    assert not user.has_perm(
        "installs.view_install"
    ), "The user has the permission for a different model."


@pytest.mark.django_db
def test_assign_permission_with_constraint(user_factory, location_factory):
    """Test assigning a permission to a user for a model with a constraint.

    GIVEN a user
    WHEN a permission is assigned to the user for a model with a constraint
    THEN the user has the permission for instances of the model that meet the constraint
    AND the user does not have the permission for instances of the model that do not meet the constraint
    """
    user = user_factory()
    location = location_factory()
    location2 = location_factory()
    # assert that the user does not have any permission yet
    assert not user.has_perm("installs.view_location")

    obj_perm = ObjectPermission(
        name="Test permission",
        enabled=True,
        actions=["view"],
        constraints=[{"id": location.id}],
    )
    obj_perm.save()
    obj_perm.users.add(user)
    obj_perm.object_types.add(ContentType.objects.get_for_model(Location))

    # check that the user has the permission now
    user = User.objects.get(pk=user.pk)
    # check the user has permission for any location
    assert user.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."
    # check the user has permission for the correct location
    assert user.has_perm(
        "installs.view_location", obj=location
    ), "The user does not have the permission for the location."
    # check the user does not have permission for the wrong location
    assert not user.has_perm(
        "installs.view_location", obj=location2
    ), "The user has the permission for the wrong location."


@pytest.mark.django_db
def test_assign_permission_with_multiple_constraints(user_factory, location_factory):
    """Test assigning a permission to a user for a model with multiple constraints.

    GIVEN a user and three instances of a model (e.g. Location)
    WHEN a permission is assigned to the user for a model with multiple constraints (e.g. two locations out of three)
    THEN the user has the permission for instances of the model that meet the constraints
    AND the user does not have the permission for instances of the model that do not meet the constraints
    """
    user = user_factory()
    location = location_factory()
    location2 = location_factory()
    location3 = location_factory()
    # assert that the user does not have any permission yet
    assert not user.has_perm("installs.view_location")

    obj_perm = ObjectPermission(
        name="Test permission",
        enabled=True,
        actions=["view"],
        constraints=[{"id": location.id}, {"id": location2.id}],
    )
    obj_perm.save()
    obj_perm.users.add(user)
    obj_perm.object_types.add(ContentType.objects.get_for_model(Location))

    # check that the user has the permission now
    user = User.objects.get(pk=user.pk)
    # check the user has permission for any location
    assert user.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."
    # check the user has permission for the correct location
    assert user.has_perm(
        "installs.view_location", obj=location
    ), "The user does not have the permission for the location."
    # check the user has permission for the correct location
    assert user.has_perm(
        "installs.view_location", obj=location2
    ), "The user does not have the permission for the location."
    # check the user does not have permission for the wrong location
    assert not user.has_perm(
        "installs.view_location", obj=location3
    ), "The user has the permission for the wrong location."


@pytest.mark.django_db
def test_assign_permission_with_multiple_actions(user_factory, location_factory):
    """Test assigning a permission to a user for a model with multiple actions.

    GIVEN a user and an instance of a model (e.g. Location)
    WHEN a permission is assigned to the user for a model with multiple actions (e.g. view and add)
    THEN the user has the permission for the model for each action
    AND the user does not have the permission for the model for any other actions"""
    user = user_factory()
    location = location_factory()
    # assert that the user does not have any permission yet
    assert not user.has_perm("installs.view_location")
    assert not user.has_perm("installs.add_location")

    obj_perm = ObjectPermission(
        name="Test permission",
        enabled=True,
        actions=["view", "add"],
    )
    obj_perm.save()
    obj_perm.users.add(user)
    obj_perm.object_types.add(ContentType.objects.get_for_model(Location))

    user = User.objects.get(pk=user.pk)
    # check the user has permission for any location
    assert user.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."
    assert user.has_perm(
        "installs.add_location"
    ), "The user does not have the permission."
    # check the user does not have permission for the wrong action
    assert not user.has_perm(
        "installs.change_location"
    ), "The user has the permission for the wrong action."


@pytest.mark.django_db
def test_assign_permission_with_complex_constraints_AND(user_factory, location_factory):
    """Test assigning a permission to a user for a model with complex constraints.

    GIVEN a user and three instances of a model (e.g. Location)
    WHEN a permission is assigned to the user for a model with complex constraints (e.g. two locations out of three, AND the name contains "Test")
    THEN the user has the permission for instances of the model that meet ALL the constraints
    AND the user does not have the permission for instances of the model that do not meet ALL the constraints
    """
    user = user_factory()
    location = location_factory()  # name = "Test Location"
    location2 = location_factory(
        name="Another Location"
    )  # name does not contain "Test", but id is in the constraint
    location3 = location_factory(
        name="Test Location 3"
    )  # name contains "Test", but id is not in the constraint
    # assert that the user does not have any permission yet
    assert not user.has_perm("installs.view_location")

    obj_perm = ObjectPermission(
        name="Test permission",
        enabled=True,
        actions=["view"],
        constraints=[
            {
                "id__in": [location.id, location2.id],
                # AND (implicit due to being in the same constraint object)
                "name__contains": "Test",
            }
        ],
    )
    obj_perm.save()
    obj_perm.users.add(user)
    obj_perm.object_types.add(ContentType.objects.get_for_model(Location))

    # check that the user has the permission now
    user = User.objects.get(pk=user.pk)
    # check the user has permission for any location
    assert user.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."
    # check the user has permission for the correct location
    assert user.has_perm(
        "installs.view_location", obj=location
    ), "The user does not have the permission for the location."
    # check the user does not have permission for the wrong location (name doesn't contain "Test" or id is not in the constraint)
    assert not user.has_perm(
        "installs.view_location", obj=location2
    ), "The user has the permission for the wrong location."
    assert not user.has_perm(
        "installs.view_location", obj=location3
    ), "The user has the permission for the wrong location."


@pytest.mark.django_db
def test_assign_permission_with_complex_constraints_OR(user_factory, location_factory):
    """Test assigning a permission to a user for a model with complex constraints.

    GIVEN a user and three instances of a model (e.g. Location)
    WHEN a permission is assigned to the user for a model with complex constraints (e.g. two locations out of three, OR the name contains "Test")
    THEN the user has the permission for instances of the model that meet ANY of the constraints
    AND the user does not have the permission for instances of the model that do not meet ANY of the constraints
    """
    user = user_factory()
    location = location_factory()
    location2 = location_factory(name="Another Location")
    location3 = location_factory(name="Location 3")
    # assert that the user does not have any permission yet
    assert not user.has_perm("installs.view_location")

    obj_perm = ObjectPermission(
        name="Test permission",
        enabled=True,
        actions=["view"],
        constraints=[
            {
                "id": location2.id,
            },
            # OR (implicit due to being in separate constraint objects)
            {
                "name__contains": "Test",
            },
        ],
    )
    obj_perm.save()
    obj_perm.users.add(user)
    obj_perm.object_types.add(ContentType.objects.get_for_model(Location))

    # check that the user has the permission now
    user = User.objects.get(pk=user.pk)
    # check the user has permission for any location
    assert user.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."
    # check the user has permission for the correct locations (ones that meet ANY of the constraints)
    assert user.has_perm(
        "installs.view_location", obj=location
    ), "The user does not have the permission for the location despite meeting the 'name contains Test' constraint."
    assert user.has_perm(
        "installs.view_location", obj=location2
    ), "The user does not have the permission for the location despite meeting the 'id is in the constraint' constraint."

    # check the user does not have permission for the wrong location (doesn't meet ANY of the constraints)
    assert not user.has_perm(
        "installs.view_location", obj=location3
    ), "The user has the permission for the wrong location."


@pytest.mark.django_db
def test_assign_permission_with_multiple_object_types(user_factory, install_factory):
    """Test assigning a permission to a user for multiple models."""
    user = user_factory()
    install = install_factory()
    location = install.location
    # assert that the user does not have any permission yet
    assert not user.has_perm("installs.view_location")
    assert not user.has_perm("installs.view_install")

    obj_perm = ObjectPermission(
        name="Test permission",
        enabled=True,
        actions=["view"],
    )
    obj_perm.save()
    obj_perm.users.add(user)
    obj_perm.object_types.add(ContentType.objects.get_for_model(Location))
    obj_perm.object_types.add(ContentType.objects.get_for_model(Install))

    # check that the user has the permission now
    user = User.objects.get(pk=user.pk)
    # check the user has permission for any location
    assert user.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."
    assert user.has_perm(
        "installs.view_install"
    ), "The user does not have the permission."
    # check the user has permission for the correct location
    assert user.has_perm(
        "installs.view_location", obj=location
    ), "The user does not have the permission for the location."
    # check the user has permission for the correct install
    assert user.has_perm(
        "installs.view_install", obj=install
    ), "The user does not have the permission for the install."


@pytest.mark.django_db
def test_assign_permission_with_multiple_users(user_factory):
    user = user_factory()
    user2 = user_factory(email="test2@example.com")
    # assert that the user does not have any permission yet
    assert not user.has_perm("installs.view_location")
    assert not user2.has_perm("installs.view_location")

    obj_perm = ObjectPermission(
        name="Test permission",
        enabled=True,
        actions=["view"],
    )
    obj_perm.save()
    obj_perm.users.add(user)
    obj_perm.users.add(user2)
    obj_perm.object_types.add(ContentType.objects.get_for_model(Location))

    # check that the user has the permission now
    user = User.objects.get(pk=user.pk)
    user2 = User.objects.get(pk=user2.pk)
    # check the user has permission for any location
    assert user.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."
    assert user2.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."


@pytest.mark.django_db
def test_assign_permission_with_multiple_groups(user_factory):
    user = user_factory()
    user2 = user_factory(email="user2@example.com")

    group = Group.objects.create(name="Test Group")
    group2 = Group.objects.create(name="Test Group 2")

    user.groups.add(group)
    user2.groups.add(group2)

    # assert that the user does not have any permission yet
    assert not user.has_perm("installs.view_location")
    assert not user2.has_perm("installs.view_location")

    obj_perm = ObjectPermission(
        name="Test permission",
        enabled=True,
        actions=["view"],
    )
    obj_perm.save()
    obj_perm.groups.add(group)
    obj_perm.groups.add(group2)
    obj_perm.object_types.add(ContentType.objects.get_for_model(Location))

    # check that the user has the permission now
    user = User.objects.get(pk=user.pk)
    user2 = User.objects.get(pk=user2.pk)
    # check the user has permission for any location
    assert user.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."
    assert user2.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."


@pytest.mark.django_db
def test_assign_permission_with_multiple_groups_and_users(user_factory):
    user = user_factory()
    user2 = user_factory(email="user2@example.com")

    group = Group.objects.create(name="Test Group")
    group2 = Group.objects.create(name="Test Group 2")

    user.groups.add(group)
    user2.groups.add(group2)

    # assert that the user does not have any permission yet
    assert not user.has_perm("installs.view_location")
    assert not user2.has_perm("installs.view_location")

    obj_perm = ObjectPermission(
        name="Test permission",
        enabled=True,
        actions=["view"],
    )
    obj_perm.save()
    obj_perm.groups.add(group)
    obj_perm.users.add(user2)
    obj_perm.object_types.add(ContentType.objects.get_for_model(Location))

    # check that the user has the permission now
    user = User.objects.get(pk=user.pk)
    user2 = User.objects.get(pk=user2.pk)
    # check the user has permission for any location
    assert user.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."
    assert user2.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."


@pytest.mark.django_db
def test_assign_permission_with_multiple_groups_and_users_and_object_types(
    user_factory, install_factory
):
    user = user_factory()
    user2 = user_factory(email="test2@example.com")

    group = Group.objects.create(name="Test Group")
    group2 = Group.objects.create(name="Test Group 2")

    user.groups.add(group)
    user2.groups.add(group2)

    install = install_factory()
    location = install.location

    # assert that the user does not have any permission yet
    assert not user.has_perm("installs.view_location")
    assert not user2.has_perm("installs.view_location")

    obj_perm = ObjectPermission(
        name="Test permission",
        enabled=True,
        actions=["view"],
    )
    obj_perm.save()
    obj_perm.groups.add(group)
    obj_perm.users.add(user2)
    obj_perm.object_types.add(ContentType.objects.get_for_model(Location))
    obj_perm.object_types.add(ContentType.objects.get_for_model(Install))

    # check that the user has the permission now
    user = User.objects.get(pk=user.pk)
    user2 = User.objects.get(pk=user2.pk)
    # check the user has permission for any location
    assert user.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."
    assert user2.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."
    # check the user has permission for the correct location
    assert user.has_perm(
        "installs.view_location", obj=location
    ), "The user does not have the permission for the location."
    # check the user has permission for the correct install
    assert user.has_perm(
        "installs.view_install", obj=install
    ), "The user does not have the permission for the install."


@pytest.mark.django_db
def test_assign_permission_with_multiple_groups_and_users_and_object_types_and_actions(
    user_factory, install_factory
):
    user = user_factory()
    user2 = user_factory(email="user2@example.com")

    group = Group.objects.create(name="Test Group")
    group2 = Group.objects.create(name="Test Group 2")

    user.groups.add(group)
    user2.groups.add(group2)

    install = install_factory()
    location = install.location

    # assert that the user does not have any permission yet
    assert not user.has_perm("installs.view_location")
    assert not user2.has_perm("installs.add_location")

    obj_perm = ObjectPermission(
        name="Test permission",
        enabled=True,
        actions=["view", "add"],
    )
    obj_perm.save()
    obj_perm.groups.add(group)
    obj_perm.users.add(user2)
    obj_perm.object_types.add(ContentType.objects.get_for_model(Location))
    obj_perm.object_types.add(ContentType.objects.get_for_model(Install))

    # check that the user has the permission now
    user = User.objects.get(pk=user.pk)
    user2 = User.objects.get(pk=user2.pk)
    # check the user has permission for any location
    assert user.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."
    assert user2.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."
    assert user.has_perm(
        "installs.add_location"
    ), "The user does not have the permission."
    assert user2.has_perm(
        "installs.add_location"
    ), "The user does not have the permission."
    # check the user has permission for the correct location
    assert user.has_perm(
        "installs.view_location", obj=location
    ), "The user does not have the permission for the location."
    assert user.has_perm(
        "installs.add_location", obj=location
    ), "The user does not have the permission for the location."
    # check the user has permission for the correct install
    assert user.has_perm(
        "installs.view_install", obj=install
    ), "The user does not have the permission for the install."
    assert user.has_perm(
        "installs.add_install", obj=install
    ), "The user does not have the permission for the install."
    assert user2.has_perm(
        "installs.view_install", obj=install
    ), "The user does not have the permission for the install."
    assert user2.has_perm(
        "installs.add_install", obj=install
    ), "The user does not have the permission for the install."


@pytest.mark.django_db
def test_assign_permission_with_multiple_groups_and_users_and_object_types_and_actions_and_constraints(
    user_factory, install_factory
):
    user = user_factory()
    user2 = user_factory(email="user2@example.com")

    group = Group.objects.create(name="Test Group")
    group2 = Group.objects.create(name="Test Group 2")

    user.groups.add(group)
    user2.groups.add(group2)

    install = install_factory()
    location = install.location
    location2 = install_factory(name="Another Location").location
    location3 = install_factory(name="Location 3").location

    # assert that the user does not have any permission yet
    assert not user.has_perm("installs.view_location")
    assert not user2.has_perm("installs.add_location")

    obj_perm = ObjectPermission(
        name="Test permission",
        enabled=True,
        actions=["view", "add"],
        constraints=[
            {
                "id": location.id,
                "name__contains": "Test",
            },
            # OR
            {
                "id": location2.id,
            },
        ],
    )
    obj_perm.save()
    obj_perm.groups.add(group)
    obj_perm.users.add(user2)
    obj_perm.object_types.add(ContentType.objects.get_for_model(Location))
    obj_perm.object_types.add(ContentType.objects.get_for_model(Install))

    # check that the user has the permission now
    user = User.objects.get(pk=user.pk)
    user2 = User.objects.get(pk=user2.pk)

    # check the user has permission for any location
    assert user.has_perm("installs.view_location") and user.has_perm(
        "installs.add_location"
    ), "The user does not have the permission."
    assert user2.has_perm("installs.view_location") and user2.has_perm(
        "installs.add_location"
    ), "The user does not have the permission."

    # check the user has permission for the correct location
    assert user.has_perm(
        "installs.view_location", obj=location
    ), "The user does not have the permission for the location."
    assert user.has_perm(
        "installs.add_location", obj=location
    ), "The user does not have the permission for the location."
    assert user2.has_perm(
        "installs.view_location", obj=location
    ), "The user does not have the permission for the location."
    assert user2.has_perm(
        "installs.add_location", obj=location
    ), "The user does not have the permission for the location."

    # check the user does not have permission for the wrong location
    assert not user.has_perm(
        "installs.view_location", obj=location3
    ), "The user has the permission for the wrong location."
    assert not user.has_perm(
        "installs.add_location", obj=location3
    ), "The user has the permission for the wrong location."
    assert not user2.has_perm(
        "installs.view_location", obj=location3
    ), "The user has the permission for the wrong location."
    assert not user2.has_perm(
        "installs.add_location", obj=location3
    ), "The user has the permission for the wrong location."
