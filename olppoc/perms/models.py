"""Models for the perms app. Based on https://www.youtube.com/watch?v=svTt9F7MnDk"""
from django.contrib.auth.models import Group
from django.db import models

from customuser.models import CustomUser
from perms.querysets import RestrictedQuerySet
from perms.utils import get_filter_from_constraints, get_perm_name


class ObjectPermissionManager(models.Manager):
    """Manager for the ObjectPermission model, for future use."""
    def get_queryset(self):
        return RestrictedQuerySet(self.model, using=self._db)
    
    def restrict(self, user, action="view") -> models.QuerySet:
        return self.get_queryset().restrict(user, action)


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

    objects = ObjectPermissionManager()

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

    def as_filter(self):
        """Return the constraints as a Q object."""
        return get_filter_from_constraints(self.list_constraints())