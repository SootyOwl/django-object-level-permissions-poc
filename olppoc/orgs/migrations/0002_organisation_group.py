# Generated by Django 4.2.3 on 2023-07-21 09:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('orgs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisation',
            name='group',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='organisation', to='auth.group'),
        ),
    ]
