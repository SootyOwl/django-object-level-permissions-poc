import pytest
from django.contrib.auth import get_user_model
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
    user = user_factory()
    location = location_factory()
    location2 = location_factory()
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


@pytest.mark.django_db
def test_assign_permission_with_multiple_actions(user_factory, location_factory):
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

    # check that the user has the permission now
    user = User.objects.get(pk=user.pk)
    # check the user has permission for any location
    assert user.has_perm(
        "installs.view_location"
    ), "The user does not have the permission."
    assert user.has_perm(
        "installs.add_location"
    ), "The user does not have the permission."


@pytest.mark.django_db
def test_assign_permission_with_complex_constraints_AND(user_factory, location_factory):
    user = user_factory()
    location = location_factory()
    location2 = location_factory(name="Another Location")
    # assert that the user does not have any permission yet
    assert not user.has_perm("installs.view_location")

    obj_perm = ObjectPermission(
        name="Test permission",
        enabled=True,
        actions=["view"],
        constraints=[
            {
                "id__in": [location.id, location2.id],
                # AND
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
    # check the user does not have permission for the wrong location (name doesn't contain "Test")
    assert not user.has_perm(
        "installs.view_location", obj=location2
    ), "The user has the permission for the wrong location."


@pytest.mark.django_db
def test_assign_permission_with_complex_constraints_OR(
    user_factory, location_factory
):
    user = user_factory()
    location = location_factory()
    location2 = location_factory(name="Another Location")
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
            # OR
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
    # check the user has permission for the correct location
    assert user.has_perm(
        "installs.view_location", obj=location
    ), "The user does not have the permission for the location."
    # check the user has permission for the correct location
    assert user.has_perm(
        "installs.view_location", obj=location2
    ), "The user does not have the permission for the location."


@pytest.mark.django_db
def test_assign_permission_with_multiple_object_types(user_factory, install_factory):
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


