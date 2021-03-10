from menu.models import Menu, CompanyLogo
from django import template
from django.utils import translation
from django.conf import settings
from wagtail_localize.synctree import Locale

register = template.Library()

@register.simple_tag()
def get_menu_items(menu, logged_in, language_code=None):
    # returns a list of dicts with title, url, slug, page and icon of all items in the menu
    # use the slug of the default language
    if menu == None:
        return None
    
    try:
        # get menu in default language
        # menu = get_menu(slug)

        # if language code supplied, get translated menu if it exists
        if language_code:
            locale = Locale.objects.get(language_code=language_code)
            locale_menu = menu.get_translation_or_none(locale=locale)
            if locale_menu:
                menu = locale_menu
        else:
            language_code = translation.get_language()

        # gather all menu item type, sort by menu_display_order at the end
        sub_menu_items = menu.sub_menu_items.all()
        link_menu_items = menu.link_menu_items.all()
                    
        # create a list of all items that should be shown in the menu depending on logged_in
        menu_items = []
        for item in sub_menu_items:
            if item.show(logged_in):
                menu_items.append({
                    'order': item.menu_display_order,
                    'slug': item.title_of_submenu, 
                    'is_submenu': True,
                    'divider': item.show_divider_after_this_item,
                    'display_option': item.display_option,
                })
        for item in link_menu_items:
            trans_page = item.trans_page(language_code)
            link_page_title = trans_page.title if trans_page else None
            if item.show(logged_in):
                menu_items.append({
                    'order': item.menu_display_order,
                    'title': item.title, 
                    'url': item.trans_url(language_code),
                    #'page': item.trans_page(language_code), 
                    'icon': item.icon,
                    'link_page_title': link_page_title,
                    'is_submenu': False,
                    'divider': item.show_divider_after_this_item,
                })
        menu_items = sorted(menu_items, key=lambda k: k['order'])
        return menu_items
    except Menu.DoesNotExist:
        return None

    # try:
    #     # if there is no custom menu, then there should be a valid page argument; see if it has children
    #     items = page.get_children()
    #     # if so, create a list of all items that have show_in_menus == True
    #     menu_items = []
    #     for item in items:
    #         if item.show_in_menus:
    #             menu_items.append({
    #                 'title': item.title, 
    #                 'url': item.url,
    #                 'slug': None, 
    #                 'page': item, 
    #                 'icon': None,
    #                 'show_linked_page': False,
    #                 'is_submenu': True,
    #             })
    #     return menu_items

    # except AttributeError:
    #     # neither custom menu nor valid page argument; return None
    #     print('error')
    #     return None

@register.simple_tag()
def get_menu(menu_slug):
    try:
        menu = Menu.objects.get(slug=menu_slug)
        print(menu)
    except AttributeError:
        return None
    return menu


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
