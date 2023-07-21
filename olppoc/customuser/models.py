# Create your models here. CustomUser model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here. CustomUserManager model
from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    """Custom user model manager. Facilitates creation of custom users."""

    def create_user(self, email, password, **extra_fields):
        """Create and save a custom user with the given email and password."""
        if not email:
            raise ValueError(_('The email must be set'))
        if not password:
            raise ValueError(_('The password must be set'))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()

        return user
    
    def create_superuser(self, email, password, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Custom user model. Remove username field and use email to login."""
    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    def __str__(self):
        return self.email
