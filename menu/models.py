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

@register_snippet
class Menu(ClusterableModel):

    title = models.CharField(max_length=50)
    slug = AutoSlugField(
        populate_from="title",
        editable=True,
        help_text="Unique identifier of menu. Will be populated automatically from title of menu. Change only if needed.",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("title"),
                FieldPanel("slug"),
            ],
            heading=_("Menu"),
        ),
        InlinePanel("menu_items", label=_("Menu Item")),
    ]

    def __str__(self):
        return self.title

class MenuItem(Orderable):
    menu = ParentalKey(
        "Menu",
        related_name="menu_items",
        help_text=_("Menu to which this item belongs"),
    )
    title = models.CharField(
        max_length=50, help_text=_("Title of menu item that will be displayed")
    )
    link_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text=_(
            "URL to link to, e.g. /accounts/signup (no language prefix, LEAVE BLANK if you want to link to a page instead of a URL)"
        ),
    )
    link_page = models.ForeignKey(
        LocalizePage,
        blank=True,
        null=True,
        related_name="+",
        on_delete=models.CASCADE,
        help_text=_(
            "Page to link to (LEAVE BLANK if you want to link to a URL instead)"
        ),
    )
    title_of_submenu = models.CharField(
        blank=True,
        null=True,
        max_length=50,
        help_text=_("Title of submenu (LEAVE BLANK if there is no custom submenu)"),
    )
    show_linked_page = models.BooleanField(
        default=False,
        help_text=_("If checked, linked page will be first item in sub-menu using that page's title")
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
        FieldPanel("title_of_submenu"),
        FieldPanel("show_linked_page"),
        FieldPanel("show_when"),
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
