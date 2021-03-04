from django.conf import settings
from django.db import models

from wagtail.core.models import Page


class HomePage(Page):
    pass

    def get_context(self, request, *args, **kwargs):
        """Adds custom fields to the context"""
        context = super().get_context(request, *args, **kwargs)
        context['lang_versions'] = self.get_translations()
        context['default_lang'] = (settings.LANGUAGES[0][0])
        return context