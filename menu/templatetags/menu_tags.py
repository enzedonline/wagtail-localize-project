from menu.models import Menu, CompanyLogo
from django import template
from django.utils import translation
from django.conf import settings
from wagtail_localize.synctree import Locale

register = template.Library()

@register.simple_tag()
def get_menu_items(menu, logged_in, language_code=None):
    # returns a list of dicts with title, url, page and icon of all items in the menu
    # use get_menu first to load the menu object then pass that instance to this function

    if menu == None:
        return None

    if not isinstance(menu, Menu):
        if isinstance(menu, int):
            # menu id supplied instead of menu instance
            menu = get_menu(menu)
        if menu == None:
            # couldn't load menu, return nothing
            return None
    
    try:
        # if language code supplied, get translated menu if it exists
        if language_code:
            locale = Locale.objects.get(language_code=language_code)
        else:
            try:
                # takes the locale code from the LANGUAGE_CODE setting
                locale = Locale.objects.get(language_code=translation.get_language())
            except Locale.DoesNotExist:                     
                try:
                    # LANGUAGE_CODE locale is not one of the languages, try language component of locale (en-gb -> en) 
                    locale = Locale.objects.get(language_code=translation.get_language()[:2])
                except Locale.DoesNotExist:                     
                    # still no match, use the default language code
                    locale = Locale.objects.get(language_code=settings.LANGUAGES[0][0])

        locale_menu = menu.get_translation_or_none(locale=locale)
        if locale_menu:
            menu = locale_menu

        # gather all menu item type, sort by menu_display_order at the end
        sub_menu_items = menu.sub_menu_items.all()
        link_menu_items = menu.link_menu_items.all()
        autofill_menu_items = menu.autofill_menu_items.all()
                    
        # create a list of all items that should be shown in the menu depending on logged_in
        menu_items = []
        for item in sub_menu_items:
            if item.show(logged_in):
                menu_items.append({
                    'order': item.menu_display_order,
                    'submenu_id': item.submenu_id, 
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
                    'icon': item.icon,
                    'link_page_title': link_page_title,
                    'is_submenu': False,
                    'divider': item.show_divider_after_this_item,
                })
        for item in autofill_menu_items:
            trans_page = item.trans_page(language_code)
            if trans_page:
                if item.include_linked_page:
                    link_page_title = trans_page.title if trans_page else None
                    if item.show(logged_in):
                        menu_items.append({
                            'order': item.menu_display_order,
                            'title': trans_page.title, 
                            'url': trans_page.url,
                            'link_page_title': link_page_title,
                            'is_submenu': False,
                            'divider': True,
                        })
                if logged_in:
                    list = trans_page.get_children().live().order_by(item.order_by)
                else:
                    list = trans_page.get_children().live().public().order_by(item.order_by)
                if item.only_show_in_menus:
                    list = list.filter(show_in_menus=True)
                list = list[:item.max_items]
                if list:
                    i = 0
                    for result in list:
                        menu_items.append({
                            'order': item.menu_display_order + i/(item.max_items + 1),
                            'title': result.title, 
                            'url': result.url,
                            'is_submenu': False,                            
                        })
                        i+=1
                    menu_items[-1]['divider'] = item.show_divider_after_this_item
        menu_items = sorted(menu_items, key=lambda k: k['order'])
        return menu_items
    except Menu.DoesNotExist:
        return None

@register.simple_tag()
def get_menu(menu_id):
    try:
        menu = Menu.objects.get(id=menu_id)
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
