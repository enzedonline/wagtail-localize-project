# Generated by Django 3.1.7 on 2021-03-18 11:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0020_auto_20210318_1208'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='menu',
            name='slug',
        ),
    ]
