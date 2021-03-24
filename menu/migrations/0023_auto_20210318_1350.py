# Generated by Django 3.1.7 on 2021-03-18 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0022_autofillmenuitem_include_linked_page'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='autofillmenuitem',
            name='link_url',
        ),
        migrations.AlterField(
            model_name='autofillmenuitem',
            name='description',
            field=models.CharField(blank=True, help_text='Optional field to describe what this item will load. Titles will come from the pages.', max_length=50, null=True),
        ),
    ]