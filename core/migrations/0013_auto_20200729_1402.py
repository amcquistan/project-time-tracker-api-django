# Generated by Django 3.0.8 on 2020-07-29 14:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_projectcontributor_project_admin'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='members',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='organization',
            name='contact',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='organization_contacts', to=settings.AUTH_USER_MODEL),
        ),
    ]
