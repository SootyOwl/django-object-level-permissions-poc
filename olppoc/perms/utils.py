"""Utility functions for the perms app."""

from django.db.models import Q
from django.contrib.contenttypes.models import ContentType


def get_filter_from_constraints(constraints: list[dict]) -> Q:
    """Get a Q object from a list of constraints.

    Args:
        constraints (list[dict]): The constraints to convert to a Q object.

    Returns:
        Q: The Q object representing the constraints.
    """
    params = Q()
    for constraint in constraints:
        if constraint:
            params |= Q(**constraint)
        else:
            return Q()  # null constraint
    return params


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
