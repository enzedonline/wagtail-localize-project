# Generated by Django 3.1.7 on 2021-03-08 16:20

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0022_uploadedimage'),
        ('wagtailcore', '0059_apply_collection_ordering'),
        ('menu', '0010_menuitem_show_divider_after_this_item'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubMenuItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('title', models.CharField(blank=True, help_text='Title to display in menu', max_length=50, null=True)),
                ('link_url', models.CharField(blank=True, help_text='If using link page, any text here will be appended to the page url. For an internal url without page link, leave off the language specific part of the url (ie /accounts/ not /en/accounts/).', max_length=500, null=True)),
                ('show_when', models.CharField(choices=[('always', 'Always'), ('logged_in', 'When logged in'), ('not_logged_in', 'When not logged in')], default='always', help_text='Determines if menu item is only shown if user logged in, logged out or always', max_length=15)),
                ('show_divider_after_this_item', models.BooleanField(default=False, help_text='Add a dividing line after this menu item if on a dropdown menu.')),
                ('icon', models.ForeignKey(blank=True, help_text='Optional image to display on menu - if title is blank, only image will show', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.image')),
                ('link_page', models.ForeignKey(blank=True, help_text='Use this to link to an internal page. Link to the page in the language of this menu.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.page')),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale')),
                ('menu', modelcluster.fields.ParentalKey(help_text='Menu to which this item belongs', on_delete=django.db.models.deletion.CASCADE, related_name='menu_items', to='menu.menu')),
            ],
            options={
                'unique_together': {('translation_key', 'locale')},
            },
        ),
        migrations.DeleteModel(
            name='MenuItem',
        ),
    ]
