# Generated by Django 4.2.3 on 2023-07-21 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('orgs', '0003_remove_organisation_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisationmember',
            name='permissions',
            field=models.ManyToManyField(related_name='orgs', to='auth.group', verbose_name='permissions'),
        ),
    ]
