from menu.models import Menu, CompanyLogo
from django import template
from django.utils import translation
from django.conf import settings
from wagtail_localize.synctree import Locale
from wagtail.images.models import Image

def default_language():
    return Locale.objects.get(language_code=settings.LANGUAGES[0][0])

def get_locale(language_code, request):
    # if language code supplied, try to return locale
    if language_code:
        try:
            return Locale.objects.get(language_code=language_code)
        except Locale.DoesNotExist:                     
            pass
    # no language code supplied or invalid language code
    try:
        # try to take the locale code from the request
        return Locale.objects.get(language_code=translation.get_language_from_request(request))
    except Locale.DoesNotExist:                     
        try:
            # try to get the locale of the LANGUAGE_CODE setting
            return Locale.objects.get(language_code=translation.get_language())
        except Locale.DoesNotExist:  
            try:
                # LANGUAGE_CODE locale is not one of the languages, try language component of locale (en-gb -> en) 
                return Locale.objects.get(language_code=translation.get_language()[:2])
            except Locale.DoesNotExist:                     
                # still no match, use the default language code
                return Locale.objects.get(language_code=settings.LANGUAGES[0][0])    

def sub_menu_items(menu, logged_in):
    # return any submenus for the menu instance
    sub_menu_items = []
    for item in menu.sub_menu_items.all():
        if item.show(logged_in):
            sub_menu_items.append({
                'order': item.menu_display_order,
                'submenu_id': item.submenu_id, 
                'is_submenu': True,
                'divider': item.show_divider_after_this_item,
                'display_option': item.display_option,
            })
    return sub_menu_items

def link_menu_items(menu, logged_in, locale):
    #return any links for the menu instance
    link_menu_items = []
    for item in menu.link_menu_items.all():
        if item.show(logged_in): # authentication status of user matches item 'show_when' property
            trans_page = item.trans_page(locale) # get translated page if any
            if trans_page: # link is to internal page (not url)
                if not item.title: # no title set in menu item, use page title
                    item.title = trans_page.title
                url = str(item.trans_page(locale).url)
                if item.link_url: # anything in url field to be treated as suffix (eg /?cat=news)
                    url = url + str(item.link_url)
            else: # not a page link, test if internal or external url, translate if internal
                if item.link_url.startswith('/'): # presumes internal link starts with '/' and no lang code
                    url = '/' + locale.language_code + item.link_url
                else: # external link, do nothing
                    url = item.link_url                
            link_menu_items.append({
                'order': item.menu_display_order,
                'title': item.title, 
                'url': url,
                'icon': item.icon,
                'is_submenu': False,
                'divider': item.show_divider_after_this_item,
            })
    return link_menu_items

def autofill_menu_items(menu, logged_in, locale):
    autofill_menu_items = []
    for item in menu.autofill_menu_items.all():
        if item.show(logged_in): # authentication status of user matches item 'show_when' property
            trans_page = item.trans_page(locale) # get translated page if any
            if trans_page:
                if item.include_linked_page: # show linked page as well as any results
                    autofill_menu_items.append({
                        'order': item.menu_display_order,
                        'title': trans_page.title, 
                        'url': trans_page.url,
                        'is_submenu': False,
                        'divider': True,
                    })
                # return only public pages if user not logged in
                if logged_in:
                    list = trans_page.get_children().live().order_by(item.order_by)
                else:
                    list = trans_page.get_children().live().public().order_by(item.order_by)
                # filter by 'Show In Menu' if selected
                if item.only_show_in_menus:
                    list = list.filter(show_in_menus=True)
                # limit list to maximum set in menu item
                list = list[:item.max_items]
                # add results (if any) to menu items
                if list:
                    i = 0
                    for result in list:
                        autofill_menu_items.append({
                            'order': item.menu_display_order + i/(item.max_items + 1),
                            'title': result.title, 
                            'url': result.url,
                            'is_submenu': False,                            
                        })
                        i+=1
                    # if add divider selected, add to last item only
                    autofill_menu_items[-1]['divider'] = item.show_divider_after_this_item
    return autofill_menu_items

register = template.Library()

@register.simple_tag()
def get_menu_items(menu, request):
    # returns a list of dictionaries with title, url, page and icon of all items in the menu
    # use get_menu first to load the menu object then pass that instance to this function

    authenticated = request.user.is_authenticated
    language_code = request.LANGUAGE_CODE

    if not isinstance(menu, Menu):
        if isinstance(menu, int):
            # menu id supplied instead of menu instance
            menu = get_menu(menu)
        if menu == None:
            # couldn't load menu, return nothing
            return None
    
    # determine locale, get translated menu (if any)
    locale=get_locale(language_code, request)

    # gather all menu item types, sort by menu_display_order at the end
    # create a list of all items that should be shown in the menu depending on logged_in
    menu_items = [] + \
                 sub_menu_items(menu, authenticated) + \
                 link_menu_items(menu, authenticated, locale) + \
                 autofill_menu_items(menu, authenticated, locale)

    # if no menu items to show, return None
    if menu_items.__len__() == 0:
        return None

    # sort menu items by common 'order' field
    menu_items = sorted(menu_items, key=lambda k: k['order'])

    return menu_items

@register.simple_tag()
def get_menu(menu_id, language_code):
    # return the menu instance for a given id, or none if no match
    try:
        menu = Menu.objects.get(id=menu_id)
    except (AttributeError, Menu.DoesNotExist):
        return None
        # determine locale, get translated menu (if any)
    
    if language_code:
        try:
            locale=Locale.objects.get(language_code=language_code)
            if menu.has_translation(locale):
                menu = menu.get_translation(locale=locale)
        except Locale.DoesNotExist:                     
            pass

    return menu

@register.simple_tag()
def language_switcher(page, current_language):
    default_lang = default_language()
    # build the language switcher menu
    switch_pages = []
    for locale in Locale.objects.all():
        if not locale.language_code == current_language:
            trans_page = page.get_translation(locale=locale)
            alternate_link = f'<link rel="alternate" hreflang="{locale.language_code}" href="{trans_page.url}" />'
            if locale == default_lang:
                alternate_link += f'<link rel="alternate" hreflang="x-default" href="{trans_page.url}" />'
            switch_pages.append(
                {
                    'language': locale, 
                    'url': '/lang/' + locale.language_code + '/?next=' + trans_page.url,
                    'flag': get_lang_flag(locale.language_code),
                    'alternate': alternate_link
                }
            )
    return switch_pages

@register.simple_tag()
def get_lang_flag(language_code):
    # returns the flag icon for the menu 
    # upload flag image to wagtail, set title to flag-lang (eg flag-fr, flag-en)
    return Image.objects.all().filter(title='flag-' + language_code).first()

@register.simple_tag()
def company_logo():
    return CompanyLogo.objects.first()
