from menu.models import Menu, CompanyLogo
from django import template
from django.utils import translation
from django.conf import settings
from wagtail_localize.synctree import Locale

register = template.Library()

@register.simple_tag()
def get_menu(slug, page, logged_in):
    # returns a list of dicts with title, url, slug, page and icon of all items in the menu of the given slug or page

    try:
        # see if there is a custom menu defined for the slug of the item
        items = Menu.objects.get(slug=slug).menu_items.all()
        language_code = translation.get_language()
        # create a list of all items that should be shown in the menu depending on logged_in
        menu_items = []
        for item in items:
            trans_page = item.trans_page(language_code)
            link_page_title = trans_page.title if trans_page else None
            if item.show(logged_in):
                menu_items.append({
                    'title': item.title, 
                    'url': item.trans_url(language_code),
                    'slug': item.slug_of_submenu, 
                    'page': item.trans_page(language_code), 
                    'icon': item.icon,
                    'link_page_title': link_page_title,
                    'show_linked_page': item.show_linked_page,
                })
        return menu_items
    except Menu.DoesNotExist:
        pass
    try:
        # if there is no custom menu, then there should be a valid page argument; see if it has children
        items = page.get_children()

        # if so, create a list of all items that have show_in_menus == True
        menu_items = []
        for item in items:
            if item.show_in_menus:
                menu_items.append({'title': item.title, 'url': item.url,
                                   'slug': None, 'page': item, 'icon': None})
        return menu_items
    except AttributeError:
        # neither custom menu nor valid page argument; return None
        return None

@register.simple_tag()
def language_switcher(current_language):
    switch_pages = []
    for locale in Locale.objects.all():
        if not locale.language_code == current_language:
            switch_pages.append(
                {
                    'language': locale, 
                    'url': '/lang/' + locale.language_code + '/',
                    'flag': get_lang_flag(locale.language_code)
                }
            )
    return switch_pages

@register.simple_tag()
def get_lang_flag(language_code):
    path = settings.STATIC_URL + settings.LANGUAGE_FLAG_LOCATION
    return path + '/' + language_code + '.png'


@register.simple_tag()
def company_logo():
    return CompanyLogo.objects.first()
