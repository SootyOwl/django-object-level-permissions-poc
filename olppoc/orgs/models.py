from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import models
# Create your models here.
# Create Organisation, OrganisationOwner, OrganisationMember models


User = get_user_model()


class Organisation(models.Model):
    """An organisation model.
    
    An organisation can have one owner and many members.

    Represents a group of users who can share permissions to resources.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    members = models.ManyToManyField(
        User,
        verbose_name='members',
        through='OrganisationMember',
        related_name='orgs',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class OrganisationMember(models.Model):
    """An organisation member through model.
    
    A user can be a member of one organisation.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organisation = models.OneToOneField(Organisation, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)

    permissions = models.ManyToManyField(
        Group,
        verbose_name='permissions',
        related_name='orgs',
    )
    """A user can have many permissions to resources. Permissions are represented by groups of users."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'organisation member'
        verbose_name_plural = 'organisation members'

    def __str__(self):
        return f'{self.user} is a member of {self.organisation}'


class OrganisationOwner(models.Model):
    """An organisation owner model. Designates the owner of an organisation.
    """
    organisation = models.OneToOneField(Organisation, on_delete=models.CASCADE, related_name='owner')
    member = models.OneToOneField(OrganisationMember, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.member.user} owns {self.organisation}'
    
