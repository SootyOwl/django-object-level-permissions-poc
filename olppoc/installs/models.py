from django.db import models
# Create your models here.
from perms.querysets import RestrictedQuerySet

class Location(models.Model):
    """A location model."""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RestrictedQuerySet.as_manager()
    
    def __str__(self):
        return self.name

class Install(models.Model):
    """An install model. Represents a single install of a product at a location."""
    
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='installs')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    assigned_to = models.ForeignKey('customuser.CustomUser', on_delete=models.CASCADE, related_name='installs', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    

class Product(models.Model):
    """A product model."""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name