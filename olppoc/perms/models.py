"""Models for the perms app. Based on https://www.youtube.com/watch?v=svTt9F7MnDk"""
from django.contrib.auth.models import Group
from django.db import models

from customuser.models import CustomUser
from perms.utils import get_filter_from_constraints, get_perm_name


class RestrictedQuerySet(models.QuerySet):
    """Usage: Model.objects.restrict(user=user, actions=['view'])"""

    def restrict(self, user, action="view") -> models.QuerySet:
        """Filter the queryset to only include objects that the specified user has the specified action for.

        Args:
            user (CustomUser): The user to restrict the queryset for.
            actions (list[str], optional): The actions to filter the ObjectPermissions by. Defaults to None.
        """
        perm_name = get_perm_name(self.model, action)
        if user.is_superuser:
            return self
        elif not user.is_authenticated or perm_name not in user.get_all_permissions():
            return self.none()
        else:
            qfilter = get_filter_from_constraints(user._object_perm_cache[perm_name])
            allowed_objects = self.model.objects.filter(qfilter)
            return self.filter(pk__in=allowed_objects)


class ObjectPermission(models.Model):
    """An object permission model.

    Correlates content types, users/groups, and action(s)
        - View, add, change, delete, and/or custom actions
        - Actions are stored as an array of strings

    Optionally, constraints can be added to the permission to filter the objects by (expressed as JSON)
        - With no constraints, this replicate Django's default permissions system
        - Logical AND when combining constraints within an instance of this model
        - Logical OR when combining constraints across instances of this model

    Essentially supplants Django's default permissions system.
    """

    name = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)

    object_types = models.ManyToManyField(
        "contenttypes.ContentType", related_name="objectpermissions"
    )
    groups = models.ManyToManyField(Group, related_name="objectpermissions")
    users = models.ManyToManyField(CustomUser, related_name="objectpermissions")

    actions = models.JSONField(
        default=list,
        help_text="The list of actions granted by this permission.",
    )
    """Example: ["view", "edit"]"""
    constraints = models.JSONField(
        blank=True,
        null=True,
        help_text="Queryset filter matching the applicable objects of the selected type(s).)",
    )
    """Optional constraints to filter the objects by."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        verbose_name = "permission"

    def __str__(self):
        return self.name

    def list_constraints(self):
        """Return the constraints as a list."""
        if type(self.constraints) is not list:
            return [self.constraints]
        return self.constraints
