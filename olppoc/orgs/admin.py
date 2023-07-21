from django.contrib import admin

# Register your models here.
from .models import Organisation, OrganisationMember, OrganisationOwner

admin.site.register(Organisation)
admin.site.register(OrganisationMember)
admin.site.register(OrganisationOwner)
