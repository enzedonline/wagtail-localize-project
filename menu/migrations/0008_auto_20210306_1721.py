# Generated by Django 3.1.7 on 2021-03-06 16:21

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0059_apply_collection_ordering'),
        ('menu', '0007_auto_20210306_1536'),
    ]

    operations = [
        migrations.AddField(
            model_name='menuitem',
            name='is_submenu',
            field=models.BooleanField(default=False, help_text="If checked, this is a drop-down menu. If submenu selected below, this will be use to populate the menu items.If submenu left blank, menu will autopopulate from child pages of linked page above, showing all child pages that have 'Show In Menus' selected."),
        ),
        migrations.AlterField(
            model_name='menu',
            name='slug',
            field=django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='title'),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='link_page',
            field=models.ForeignKey(blank=True, help_text='Use this to link to an internal page. Link to the page in the default language.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.page'),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='link_url',
            field=models.CharField(blank=True, help_text='Leave blank if linking to an internal page (see below). For an internal url, leave off the language specific part of the url (ie /accounts/ not /en/accounts/).', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='show_linked_page',
            field=models.BooleanField(default=False, help_text="If checked, and this is a drop-down menu, linked page will be first item in sub-menu using that page's title"),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='title',
            field=models.CharField(help_text='Title to display in menu', max_length=50),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='title_of_submenu',
            field=models.CharField(blank=True, help_text='If this is a drop-down menu heading, select the menu-ID to use, otherwise leave blank.', max_length=50, null=True),
        ),
    ]