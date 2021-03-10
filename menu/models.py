from django.conf import settings
from django.db import models
from django.forms.widgets import Select
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.edit_handlers import (FieldPanel, HelpPanel, InlinePanel,
                                         MultiFieldPanel, PageChooserPanel)
from wagtail.core.models import Orderable
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.models import register_snippet
from wagtail_localize.synctree import Page as LocalizePage, Locale
from wagtail.core.models import TranslatableMixin
from wagtail.admin.forms import WagtailAdminPageForm

from wagtaillocalize.read_only_edit_handler import ReadOnlyPanel

class MenuForm(WagtailAdminPageForm):
    """ MenuForm - provides validation for Menu & Menu Item orderables"""

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        for form in self.formsets['sub_menu_items'].forms:
            if form.is_valid():
                cleaned_form_data = form.clean()
                if cleaned_form_data.get('title_of_submenu') == None:
                    form.add_error('title_of_submenu', "Sub Menu ID cannot be left blank")
                elif cleaned_form_data.get('title_of_submenu') == self.data['slug']:
                    form.add_error('title_of_submenu', "Parent Menu cannot be a Sub Menu of itself")
        for form in self.formsets['link_menu_items'].forms:
            if form.is_valid():
                cleaned_form_data = form.clean()
                cleaned_title = cleaned_form_data.get('title')
                cleaned_image = cleaned_form_data.get('icon')
                cleaned_url = cleaned_form_data.get('link_url')
                cleaned_page = cleaned_form_data.get('link_page')
                if (cleaned_title == None) and (cleaned_image == None) and (cleaned_page == None):
                    msg = _("Title, icon and linked page cannot all be left empty. ")
                    form.add_error('title', msg)
                    form.add_error('icon', msg)
                    form.add_error('link_page', msg)
                if (cleaned_url == None) and (cleaned_page == None):
                    msg = _("Linked URL and Linked Page cannot both be left empty. ")
                    form.add_error('link_url', msg)
                    form.add_error('link_page', msg)

        return cleaned_data

@register_snippet
class Menu(TranslatableMixin, ClusterableModel):
    """ Menu Class creates menus to display - validation in MenuForm
        Holds a collection of Menu Item orderables """

    base_form_class = MenuForm

    title = models.CharField(
        max_length=50,
        help_text=_("Title will be used if this is a submenu")
    )
    slug = AutoSlugField(
        populate_from="title",
#        editable=False,
    )
    # Optional image to display if submenu
    icon = models.ForeignKey(
        "wagtailimages.Image",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Optional image to display if submenu")
    )

    panels = [
        MultiFieldPanel(
            [
                ReadOnlyPanel("slug", heading="Menu ID",),
                FieldPanel("title"),
                ImageChooserPanel("icon"),
            ],
            heading=_("Menu Heading"),
        ),
        MultiFieldPanel(
            [
                HelpPanel(_("Items in the menu will be arranged by 'Menu Display Order' over the order in which they appear below.")),
                InlinePanel("sub_menu_items", label=_("Sub-menu")),
                InlinePanel("link_menu_items", label=_("Link")),
            ],
            heading=_("Menu Items - Add items to show in the menu below"),
        ),
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
    """ MenuItem Class - orderables to display in Menu class
        Parent class to SubMenuItem and AutoMenuItem classes """

    # hidden field, links item to menu        
    menu = ParentalKey(
        "Menu",
        related_name="menu_items",
        help_text=_("Menu to which this item belongs"),
    )

    # show if user logged in, logged out or always
    show_when = models.CharField(
        max_length=15,
        choices=[
            ("always", _("Always")),
            ("logged_in", _("When logged in")),
            ("not_logged_in", _("When not logged in")),
        ],
        default="always",
        help_text=_("Determines if menu item is only shown if user logged in, logged out or always")
    )
    # adds a dividing line after the item if it's on a dropdown menu
    show_divider_after_this_item = models.BooleanField(
        default=False,
        help_text=_("Add a dividing line after this menu item if on a dropdown menu.")
    )
    # allow menu items to be sorted regardless of type
    menu_display_order = models.IntegerField(
        default=0,
        help_text=_("Enter digit to determine order in menu. Menu items of all types will be sorted by this number")
    )

    class Meta:
        abstract = True

    def trans_page(self, language_code):
        """ returns the translated page for a given language if it exists """
        # if no link_page, return none
        if not self.link_page:
            return None

        # default language, just return link_page
        # if language_code == settings.LANGUAGES[0][0]:
        #     return self.link_page

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
        try:   
            if self.title_of_submenu:
                return slugify(self.title_of_submenu)
        except AttributeError:
            pass
        return None

    def show(self, authenticated):
        return (
            (self.show_when == "always")
            or (self.show_when == "logged_in" and authenticated)
            or (self.show_when == "not_logged_in" and not authenticated)
        )

    def __str__(self):
        return self.title

class LinkMenuItem(MenuItem):

    # hidden field, links item to menu        
    menu = ParentalKey(
        "Menu",
        related_name="link_menu_items",
        help_text=_("Menu to which this item belongs"),
    )

    # the text to show in the menu - can only be blank if image is not also blank
    # or blank if link page (link page title will be used)
    title = models.CharField(
        max_length=50, 
        blank=True,
        null=True,
        help_text=_("Title to display in menu"),
    )
    # Optional image to display on menu - if title is blank, only image will show
    icon = models.ForeignKey(
        "wagtailimages.Image",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Optional image to display on menu - if title is blank, only image will show")
    )

    # this field can be used to provide an external url or internal url 
    # for internal url's, must omit the language code from the url (ie /accounts/ not /en/accounts/)
    # if used with a link page, provides a suffix to the url of that page
    link_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text=_(
            "If using link page, any text here will be appended to the page url. " +
            "For an internal url without page link, leave off the language specific part of the url " +
            "(ie /accounts/ not /en/accounts/)."
        ),
    )
    # wagtail page to link to
    # if value entered in link_url, it will be appended to the url of this page
    # eg link page = /blog/categories/, link_url = news -> menu item url = /blog/categories/news/
    # useful for routable pages
    # could also to POST arguments to a page (eg link_url = ?cat=news -> /blog/categories/?cat=news)
    link_page = models.ForeignKey(
        LocalizePage,
        blank=True,
        null=True,
        related_name="+",
        on_delete=models.CASCADE,
        help_text=_(
            "Use this to link to an internal page. Link to the page in the language of this menu."
        ),
    )

    panels = [
        FieldPanel("title"),
        ImageChooserPanel("icon"),
        PageChooserPanel("link_page"),
        FieldPanel("link_url"),
        FieldPanel("show_when"),
        FieldPanel("menu_display_order"),
        FieldPanel("show_divider_after_this_item"),
    ]

    class Meta:
        unique_together = ('translation_key', 'locale')

class SubMenuListIterator(object):

    locale = None

    def __init__(self, locale) -> None:
        super().__init__()
        self.locale = locale

    def __iter__(self):
        menu_list = list(Menu.objects.values_list('slug','title').filter(locale=self.locale))
    #     parent_menu = Menu.objects.get(id=menu)
    #     menu_list = Menu.objects.values_list('slug','title').filter(locale=parent_menu.locale).exclude(id=menu)
        return menu_list.__iter__()
        
class SubMenuItem(MenuItem):
    """ Class SubMenuItem - child of MenuItem
        Used to add a sub menu to a parent menu - submenu must exist first """

    # hidden field, links item to menu        
    menu = ParentalKey(
        "Menu",
        related_name="sub_menu_items",
        help_text=_("Menu to which this item belongs"),
    )

    lang=Locale.objects.get(language_code=settings.LANGUAGES[0][0])
    choice_list=SubMenuListIterator(lang)
    submenu_selector=Select()
    submenu_selector.choices = choice_list

    title_of_submenu = models.CharField(
        blank=False,
        null=True,
        max_length=50,
        help_text=_("Enter the menu-ID that this sub-menu will load"),
        choices=choice_list
    )
    # show if user logged in, logged out or always
    display_option = models.CharField(
        max_length=4,
        choices=[
            ("both", _("Icon & Title")),
            ("text", _("Title Only")),
            ("icon", _("Icon Only")),
        ],
        default="text",
        help_text=_("Display the sub-menu as icon, text or both.")
    )
    panels = [
        HelpPanel(_("Select the menu that this sub-menu will load")),
        FieldPanel("title_of_submenu"),
        FieldPanel("display_option"),
        FieldPanel("menu_display_order"),
        FieldPanel("show_divider_after_this_item"),
    ]

    class Meta:
        unique_together = ('translation_key', 'locale')

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

