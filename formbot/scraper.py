import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .fields import Field
from .form import Form
from . import fields

class FormScraper:
    def __init__(self, url):
        self.url = url
        self.doc = None

    def extract(self):
        session = requests.session()

        response = session.get(self.url)
        self.doc = BeautifulSoup(response.content, features='html.parser')
        for tag in self.doc.find_all(['header', 'footer']):
            tag.extract()

        form = Form(session,
                    self.doc.form.get('method', 'GET'),
                    urljoin(self.url, self.doc.form.get('action')))

        names = set()

        for element in self.doc.form.find_all(['input', 'textarea']):
            # create field
            field = self._load_field(element)
            if field is None:
                continue

            # ensure field is not duplicated
            if field.name in names:
                continue
            else:
                names.add(field.name)

            form.add_field(field, element.get('id'))

        return form

    def _load_field(self, element):
        display = self._load_label(element)

        if element.name == 'textarea':
            return Field(type='textarea',
                         name=element['name'],
                         display=display,
                         required=element.get('required', False),
                         default=element.text)

        if element.name == 'input':
            ftype = element['type']
            name = element['name']
            required = element.get('required', False)
            default = element.get('default', None)
            validator = None
            extra = {}

            if ftype in ('color', 'file'):
                raise NotImplementedError(f'unsupported field type "{ftype}"')
            elif ftype in ('submit', 'image', 'button'):
                return None
            elif ftype == 'hidden':
                default = element['value']
            elif ftype == 'email':
                default = element.text
                validator = fields.email
            elif ftype == 'checkbox':
                default = element.get('checked', False)
                validator = fields.checkbox
                extra = {
                    'value': element.get('value', 'on')
                }
            elif ftype == 'radio':
                radios = self.doc.find_all(
                    'input', attrs={'type': 'radio', 'name': name})

                labels = [self._load_label(radio) for radio in radios]

                display = ','.join(labels)
                required = any(radio.get('required', False)
                               for radio in radios)
                default = None
                validator = fields.radio
                extra = {
                    'labels': [label.lower() for label in labels],
                    'values': [radio['value'] for radio in radios]
                }

            return Field(type=ftype,
                         name=name,
                         display=display,
                         required=required,
                         default=default,
                         validator=validator,
                         extra=extra)

        raise NotImplementedError('form element not supported')

    def _load_label(self, element):
        # label in tag
        if 'id' in element.attrs:
            label = self.doc.find('label', attrs={'for': element['id']})
            if label:
                return label.text

        # label in attribute
        for attr in element.attrs:
            if 'label' in attr:
                return element.attrs[attr]

        return ''
