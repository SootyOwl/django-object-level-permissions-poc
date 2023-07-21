"""Custom authentication backend for object permissions."""

from collections import defaultdict
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from perms.models import ObjectPermission
from perms.utils import get_filter_from_constraints, resolve_perm

class ObjectPermissionBackend(ModelBackend):
    """Override has_perm and get_all_permissions methods, to check object-level permissions."""

    def get_all_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous:
            return {}
        if not hasattr(user_obj, '_object_perm_cache') or not user_obj._object_perm_cache:
            # if the user doesn't have an object permission cache, or it's empty,
            # populate it now and cache it on the user object for future use
            user_obj._object_perm_cache = self.get_object_permissions(user_obj)
        return user_obj._object_perm_cache
    
    def get_permission_filter(self, user_obj):
        """Get the permission filter for the user."""
        return Q(users=user_obj) | Q(groups__user=user_obj)
    
    def get_object_permissions(self, user_obj):
        """Return permissions granted to the user by an ObjectPermission."""
        objectpermissions = ObjectPermission.objects.filter(
            self.get_permission_filter(user_obj),
            enabled=True,
        ).order_by('id').distinct().prefetch_related('object_types')
        
        perms = defaultdict(list)
        for p in objectpermissions:
            for object_type in p.object_types.all():
                for action in p.actions:
                    perm_name = f"{object_type.app_label}.{action}_{object_type.model}"
                    perms[perm_name].extend(p.list_constraints())

        return perms
    
    def has_perm(self, user_obj, perm, obj=None):
        app_label, action, model_name = resolve_perm(perm)

        if not user_obj.is_active or user_obj.is_anonymous:
            return False

        if user_obj.is_superuser:
            return True

        object_permissions = self.get_all_permissions(user_obj)

        if perm not in object_permissions:
            return False

        if obj is None:
            return True

        model = obj._meta.model
        if model._meta.label_lower != '.'.join((app_label, model_name)):
            raise ValueError(f"Invalid permission: {perm} for model: {model}")

        # compile constraints into a Q object
        q_filter = get_filter_from_constraints(object_permissions[perm])

        return model.objects.filter(q_filter, pk=obj.pk).exists()
