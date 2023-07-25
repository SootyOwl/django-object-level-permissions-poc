from django.db import models

from perms.utils import get_filter_from_constraints, get_perm_name


class RestrictedQuerySet(models.QuerySet):
    """A queryset that restricts the objects returned to only include objects that the specified user has the specified action for.
    
    Example:
        >>> from perms.models import ObjectPermission
        >>> from perms.querysets import RestrictedQuerySet
        >>> from customuser.models import CustomUser
        >>> from install.models import Install
        >>> user = CustomUser.objects.get(username="admin")
        >>> install = Install.objects.get(pk=1)
        >>> install
        <Install: Install object (1)>
        >>> install.objectpermissions.all()
        <QuerySet [<ObjectPermission: Install view>]>
        >>> install.objectpermissions.restrict(user)
        <QuerySet [<ObjectPermission: Install view>]>
    """

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
