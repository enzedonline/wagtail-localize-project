from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.edit_handlers import (FieldPanel, InlinePanel,
                                         MultiFieldPanel, PageChooserPanel)
from wagtail.core.models import Orderable
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.models import register_snippet
from wagtail_localize.synctree import Page as LocalizePage, Locale
from wagtail.core.models import TranslatableMixin
from django import forms

from wagtaillocalize.read_only_edit_handler import ReadOnlyPanel

@register_snippet
class Menu(TranslatableMixin, ClusterableModel):

    title = models.CharField(max_length=50)
    slug = AutoSlugField(
        populate_from="title",
        editable=False,
    )

    panels = [
        MultiFieldPanel(
            [
                ReadOnlyPanel("slug"),
            ],
            heading=_("Menu ID"),
        ),
        FieldPanel("title"),
        InlinePanel("menu_items", label=_("Menu Item")),
    ]

    def __str__(self):
        return self.title

    def slugify_function(self, content):
        locale_code = self.locale.language_code
        if locale_code == settings.LANGUAGES[0][0]:
            return slugify(self.title)
        else:
            return slugify(self.title + '-' + locale_code)

class MenuItem(TranslatableMixin, Orderable):

    menu = ParentalKey(
        "Menu",
        related_name="menu_items",
        help_text=_("Menu to which this item belongs"),
    )
    title = models.CharField(
        max_length=50, help_text=_("Title to display in menu")
    )
    link_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text=_(
            "Leave blank if linking to an internal page (see below). " +
            "For an internal url, leave off the language specific part of the url " +
            "(ie /accounts/ not /en/accounts/)."
        ),
    )
    link_page = models.ForeignKey(
        LocalizePage,
        blank=True,
        null=True,
        related_name="+",
        on_delete=models.CASCADE,
        help_text=_(
            "Use this to link to an internal page. Link to the page in the default language."
        ),
    )
    is_submenu = models.BooleanField(
        default=False,
        help_text=_("If checked, this is a drop-down menu. " +
                    "If submenu selected below, this will be use to populate the menu items." + 
                    "If submenu left blank, menu will autopopulate from child pages of linked page above, " + 
                    "showing all child pages that have 'Show In Menus' selected.")
    )
    title_of_submenu = models.CharField(
        blank=True,
        null=True,
        max_length=50,
        help_text=_("If this is a drop-down menu heading, select the menu-ID to use, otherwise leave blank."),
    )
    show_linked_page = models.BooleanField(
        default=False,
        help_text=_("If checked, and this is a drop-down menu, linked page will be first item in sub-menu using that page's title")
    )
    icon = models.ForeignKey(
        "wagtailimages.Image",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    show_when = models.CharField(
        max_length=15,
        choices=[
            ("always", _("Always")),
            ("logged_in", _("When logged in")),
            ("not_logged_in", _("When not logged in")),
        ],
        default="always",
    )

    panels = [
        ImageChooserPanel("icon"),
        FieldPanel("title"),
        FieldPanel("link_url"),
        PageChooserPanel("link_page"),
        FieldPanel("show_when"),
        MultiFieldPanel(
            [
                FieldPanel("is_submenu"),
                FieldPanel("title_of_submenu"),
                FieldPanel("show_linked_page"),
            ],
            heading="Submenu",
            classname="collapsible collapsed",
            ),    
    ]

    def trans_page(self, language_code):
        # if no link_page, return none
        if not self.link_page:
            return None

        # default language, just return link_page
        if language_code == settings.LANGUAGES[0][0]:
            return self.link_page

        # if language_code locale exists, retrun translated page
        # if language_code locale doesn't exists, retrun default language page
        # if language_code locale exists but no translated page, default language page
        try:
            locale = Locale.objects.get(language_code=language_code)
            trans_page = self.link_page.get_translation_or_none(locale=locale)
            if trans_page != None:
                return trans_page
            return self.link_page 
        except Locale.DoesNotExist:
            return self.link_page

    def trans_url(self, language_code):
        # if link_page and link_url set, assume url is suffix to link_page.url (anchor or parameter etc)
        # else if link_url does not begin with '/' then assume external link, just return it
        # if internal url (starts with '/') then insert requested code
        if self.link_page:
            return str(self.trans_page(language_code).url) + (str(self.link_url) if self.link_url != None else '')
        elif self.link_url:
            if self.link_url.startswith('/'):
                return '/' + language_code + self.link_url
            return self.link_url
        return None

    @property
    def slug_of_submenu(self):
        # becomes slug of submenu if there is one, otherwise None
        if self.title_of_submenu:
            return slugify(self.title_of_submenu)
        return None

    def show(self, authenticated):
        return (
            (self.show_when == "always")
            or (self.show_when == "logged_in" and authenticated)
            or (self.show_when == "not_logged_in" and not authenticated)
        )

    def __str__(self):
        return self.title



@register_snippet
class CompanyLogo(models.Model):
    name = models.CharField(max_length=250)
    logo = models.ForeignKey(
        "wagtailimages.Image", on_delete=models.CASCADE, related_name="+"
    )

    panels = [
        FieldPanel("name", classname="full"),
        ImageChooserPanel("logo"),
    ]

    def __str__(self):
        return self.name

