from django.utils.html import format_html
from wagtail.admin.edit_handlers import EditHandler

class ReadOnlyPanel(EditHandler):
    """ ReadOnlyPanel EditHandler Class - built from ideas on https://github.com/wagtail/wagtail/issues/2893
        Most credit to @BertrandBordage for this.
        Usage:
        attr:               name of field to display
        style:              optional, any valid style string
        add_hidden_input:   optional, add a hidden input field to allow retrieving data in form_clean (self.data['field'])
        If the field name is invalid, or an error is received getting the value, empty string is returned.
        """
    def __init__(self, attr, style=None, add_hidden_input=False, *args, value=None, **kwargs):
        # error if attr is not string
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
        # try to get the value of field, return empty string if failed
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
        # return formatted field value
        self.value = self.get_value()
        return format_html('<div style="padding-top: 1.2em;">{}</div>', self.value)

    def render_as_object(self):
        return format_html(
            '<fieldset>{}'
            '<ul class="fields"><li><div class="field">{}</div></li></ul>'
            '</fieldset>',
            self.heading('legend'), self.render())

    def hidden_input(self):
        # add a hidden input field if selected, field value can be retrieved in form_clean with self.data['field']
        if self.add_hidden_input:
            input = f'<input type="hidden" name="{self.attr}" value="{self.value}" id="id_{self.attr}">'
            return format_html(input)
        return ''

    def heading_tag(self, tag):
        # add the label/legen tags only if heading supplied
        if self.heading:
            if tag == 'legend':
                return format_html('<legend>{}</legend>', self.heading)
            return format_html('<label>{}{}</label>', self.heading, ':')
        return ''

    def get_style(self):
        # add style if supplied
        if self.style:
            return format_html('style="{}"', self.style)
        return ''

    def render_as_field(self):
        # render the final output
        return format_html(
            '<div class="field" {}>'
            '{}'
            '<div class="field-content">{}</div>'
            '{}'
            '</div>',
            format_html(self.get_style()), self.heading_tag('label'), self.render(), self.hidden_input())  

class RichHelpPanel(EditHandler):
    """ RichHelpPanel EditHandler Class - built on the ReadOnlyPanel
        Like the HelpPanel but with basic HTML tags and dynamic content
        Supply a Django template like text and a value dictionary
        Template tags ({{tag}}) that match dictionary keys will be replaced with the value from the dictionary.
        If the key/tag matches a field name, the value of that field will be swapped in.
        If the key/tag is not a field, then the value from the dictionary (eg a function result) is swapped in.
        Usage:
        text:       unparsed to display - use template tags {{tag}} as placeholders for data to be swapped in
                    basic html tags are rendered (formatting, links, line breaks etc)
        value_dict: optional dictionary containing tags and corresponding values
                    key name must match a {{tag}} in the text to be swapped in
                    if the value matches a field name, the value from that field is swapped in
                    if the value doesn't match (eg value is the return from a function), the dictionary value is swapped in
        style:      optional, any valid style string

        Example usage:
        msg=_('This snippet\'s slug is <b>{{the_slug}}</b>.<br>Today\'s date is {{today}}<br><a href="/somepage" target="_blank">Read More</a>')
        values={'the_slug': 'slug', 'today': datetime.today().strftime('%d-%B-%Y')}
        style="color:blue;text-align:center"
        panels = [
            RichHelpPanel(
                msg, 
                style=style,
                value_dict=values,
                heading=_("Rich Help Panel Test")
            ), 
        ]       
        """
    def __init__(self, text, value_dict={}, style=None, *args, **kwargs):
        # make sure text is a string
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
        # if field_name is a valid name, return data, otherwise return field name unchanged
        try:
            value = getattr(self.instance, field_name)
            if callable(value):
                value = value()
        except (AttributeError, TypeError) as e:
            value = field_name
        return value

    def parse_text(self):
        # loop through the the value dictionary if present, 
        # swap out {{tag}}'s that match key names with the corresponding values
        # keep looping on error
        # return text unchanged if not a string
        try:
            parsed_text = self.text
            for item in self.value_dict:
                try:
                    parsed_text = parsed_text.replace('{{' + item + '}}', self.get_value(str(self.value_dict[item])))
                except:
                    pass
            return format_html(parsed_text)
        except TypeError:
            return format_html(self.text)

    def render(self):
        # render the parsed text in a div
        return format_html('<div style="padding-top: 1.2em;">{}</div>', self.parse_text())

    def label(self):
        # add label tag if heading supplied
        if self.heading:
            return format_html('<label>{}{}</label>', self.heading, ':')
        return ''

    def get_style(self):
        # add style if supplied
        if self.style:
            return format_html('style="{}"', self.style)
        return ''

    def render_as_field(self):
        # return assembled HTML
        return format_html(
            '<div class="field" {}>'
            '{}'
            '<div class="field-content">{}</div>'
            '</div>',
            format_html(self.get_style()), self.label(), self.render())  
