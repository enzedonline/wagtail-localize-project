# Generated by Django 3.1.7 on 2021-03-08 14:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0059_apply_collection_ordering'),
        ('menu', '0008_auto_20210306_1721'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='menuitem',
            name='is_submenu',
        ),
        migrations.RemoveField(
            model_name='menuitem',
            name='show_linked_page',
        ),
        migrations.RemoveField(
            model_name='menuitem',
            name='title_of_submenu',
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='link_page',
            field=models.ForeignKey(blank=True, help_text='Use this to link to an internal page. Link to the page in the language of this menu.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.page'),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='link_url',
            field=models.CharField(blank=True, help_text='If using link page, any text here will be appended to the page url. For an internal url without page link, leave off the language specific part of the url (ie /accounts/ not /en/accounts/).', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='title',
            field=models.CharField(blank=True, help_text='Title to display in menu', max_length=50, null=True),
        ),
    ]