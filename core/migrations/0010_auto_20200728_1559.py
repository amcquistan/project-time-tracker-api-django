# Generated by Django 3.0.8 on 2020-07-28 15:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_project_organization'),
    ]

    operations = [
        migrations.RenameField(
            model_name='projectcontributor',
            old_name='can_log_activity',
            new_name='activity_editor',
        ),
        migrations.RenameField(
            model_name='projectcontributor',
            old_name='can_view_activity',
            new_name='activity_viewer',
        ),
    ]
