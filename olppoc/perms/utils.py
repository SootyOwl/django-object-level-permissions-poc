"""Utility functions for the perms app."""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q


def get_filter_from_constraints(constraints: list[dict]) -> Q:
    """Get a Q object from a list of constraints.

    Args:
        constraints (list[dict]): The constraints to convert to a Q object.

    Returns:
        Q: The Q object representing the constraints.
    """
    params = Q()
    has_constraints = False
    for constraint in constraints:
        if constraint:
            params |= Q(**constraint)
            has_constraints = True
    return params if has_constraints else Q()


def resolve_perm(perm: str) -> tuple[str, str, str]:
    """Given a permission name resolves the app_label, action, and model_name."""
    try:
        app_label, action_model = perm.split(".")
        action, model_name = action_model.split("_", 1)
    except ValueError as e:
        raise ValueError(
            f"Invalid permission name: {perm}. Must be in the format: 'app_label.action_model'"
        ) from e
    return app_label, action, model_name


def get_perm_name(model, action):
    """Given a model and action, returns the permission name."""
    return f"{model._meta.app_label}.{action}_{model._meta.model_name}"


def resolve_contenttype_from_perm(perm: str) -> tuple[str, str]:
    """Given a permission name resolves the ContentType and action."""
    app_label, action, model_name = resolve_perm(perm)
    try:
        content_type = ContentType.objects.get(app_label=app_label, model=model_name)
    except ContentType.DoesNotExist as e:
        raise ValueError(f"Cound not find ContentType for: {perm}") from e
    return content_type, action


def modify_object_safely(obj, user, update_dict):
    """
    Modify an object safely by checking if the user has permission to modify it
    before and after the modification. Prevents users from modifying objects
    in ways that would remove their access to the object.

    Args:
        obj: The object to modify.
        user: The user attempting to modify the object.
        update_dict: A dictionary containing the fields to update and their new values.

    Returns:
        The modified object.

    Raises:
        PermissionDenied: If the user does not have permission to modify the object.
    """
    # validate pre-modified object state
    queryset = obj.__class__.objects.restrict(user=user, action="change")
    if not queryset.filter(pk=obj.pk).exists():
        raise PermissionDenied("You do not have permission to modify this object.")
    # modify and save the object inside a transaction
    try:
        with transaction.atomic():
            # update the object fields
            for field, value in update_dict.items():
                setattr(obj, field, value)
            obj.save()
            # check whether the current user can still access the object
            if not queryset.filter(pk=obj.pk).exists():
                # abort the transaction
                raise PermissionDenied("Your changes would have removed your access to this object. Aborting.")
    except PermissionDenied:
        raise
    return obj
