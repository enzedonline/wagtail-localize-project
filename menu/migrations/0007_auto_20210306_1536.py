# Generated by Django 3.1.7 on 2021-03-06 14:36

from django.db import migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0006_auto_20210306_1528'),
    ]

    operations = [
        migrations.AlterField(
            model_name='menu',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(blank=True, editable=False, help_text='Unique identifier of menu. Will be populated automatically from title of menu. Change only if needed.', populate_from='title'),
        ),
    ]
