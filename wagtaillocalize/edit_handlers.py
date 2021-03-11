from django.utils.html import format_html
from wagtail.admin.edit_handlers import EditHandler

class ReadOnlyPanel(EditHandler):

    def __init__(self, attr, style=None, add_hidden_input=False, *args, value=None, **kwargs):
        if type(attr)=='str':
            self.attr = attr
        else:
            try:
                self.attr = str(attr)
            except:
                pass
        self.style = style
        self.add_hidden_input = add_hidden_input
        super().__init__(*args, **kwargs)

    def get_value(self):
        try:
            value = getattr(self.instance, self.attr)
            if callable(value):
                value = value()
        except AttributeError:
            value = ''
        return value
        
    def clone(self):
        return self.__class__(
            attr=self.attr,
            heading=self.heading,
            classname=self.classname,
            help_text=self.help_text,
            style=self.style,
            add_hidden_input=self.add_hidden_input,
            value=None,
        )

    def render(self):
        self.value = self.get_value()
        return format_html('<div style="padding-top: 1.2em;">{}</div>', self.value)

    def render_as_object(self):
        return format_html(
            '<fieldset>{}'
            '<ul class="fields"><li><div class="field">{}</div></li></ul>'
            '</fieldset>',
            self.heading('legend'), self.render())

    def hidden_input(self):
        if self.add_hidden_input:
            input = f'<input type="hidden" name="{self.attr}" value="{self.value}" id="id_{self.attr}">'
            return format_html(input)
        return ''

    def heading_tag(self, tag):
        if self.heading:
            if tag == 'legend':
                return format_html('<legend>{}</legend>', self.heading)
            return format_html('<label>{}{}</label>', self.heading, ':')
        return ''

    def get_style(self):
        if self.style:
            return format_html('style="{}"', self.style)
        return ''

    def render_as_field(self):
        return format_html(
            '<div class="field" {}>'
            '{}'
            '<div class="field-content">{}</div>'
            '{}'
            '</div>',
            format_html(self.get_style()), self.heading_tag('label'), self.render(), self.hidden_input())  

class RichHelpPanel(EditHandler):

    def __init__(self, text, value_dict={}, style=None, *args, **kwargs):
        if type(text)=='str':
            self.text = text
        else:
            try:
                self.text = str(text)
            except:
                pass
        self.value_dict = value_dict
        self.text = text
        self.style = style
        super().__init__(*args, **kwargs)

    def clone(self):
        return self.__class__(
            text=self.text,
            heading=self.heading,
            classname=self.classname,
            help_text=self.help_text,
            value_dict = self.value_dict,
            style=self.style,
        )

    def get_value(self, field_name):
        try:
            value = getattr(self.instance, field_name)
            if callable(value):
                value = value()
        except (AttributeError, TypeError) as e:
            value = field_name
        return value

    def parse_text(self):
        try:
            for item in self.value_dict:
                print(item)
                self.text = self.text.replace('{{' + item + '}}', self.get_value(str(self.value_dict[item])))
            return format_html(self.text)
        except TypeError:
            return format_html(self.text)

    def render(self):
        return format_html('<div style="padding-top: 1.2em;">{}</div>', self.parse_text())

    def label(self):
        if self.heading:
            return format_html('<label>{}{}</label>', self.heading, ':')
        return ''

    def get_style(self):
        if self.style:
            return format_html('style="{}"', self.style)
        return ''

    def render_as_field(self):
        return format_html(
            '<div class="field" {}>'
            '{}'
            '<div class="field-content">{}</div>'
            '</div>',
            format_html(self.get_style()), self.label(), self.render())  
