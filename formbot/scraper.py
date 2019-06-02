import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .fields import Field
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
            field = self.load_field(element)
            if field is None:
                continue

            # ensure field is not duplicated
            if field.name in names:
                continue
            else:
                names.add(field.name)

            form.add_field(field, element.get('id'))

        return form

    def load_field(self, element):
        display = self.load_label(element)

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

                labels = [self.load_label(radio) for radio in radios]

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

    def load_label(self, element):
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


class Form:
    def __init__(self, session, method, action):
        self.session = session
        self.method = method.upper()
        self.action = action

        self.fields = []
        self.name_lookup = {}
        self.id_lookup = {}

    def add_field(self, field, id=None):
        if field.name in self.name_lookup:
            raise ValueError('cannot have duplicate field names')
        else:
            self.fields.append(field)
            self.name_lookup[field.name] = field
            if id:
                self.id_lookup[id] = field

    def get_field(self, name=None, id=None):
        if name and id:
            raise ValueError('cannot get by both name and id')
        elif name:
            return self.name_lookup[name]
        elif id:
            return self.id_lookup[id]
        else:
            raise ValueError('missing search specifier (should be name or id)')

    def fill_field(self, name, value):
        if name not in self.name_lookup:
            raise KeyError(f'{name} does not appear in form')

        field = self.name_lookup[name]
        field.fill(value)

    def submit(self):
        # populate values
        values = {}
        for field in self.fields:
            if field.required and field.data is None:
                raise KeyError(
                    f'{field.name} is required and has not been provided')

            if field.data is not None:
                values[field.name] = field.data
            elif field.type == 'hidden':
                values[field.name] = field.data or ''

        # send form
        req = requests.Request(self.method, self.action, data=values)
        resp = self.session.send(req.prepare())

        # check for submission errors
        if resp.status_code >= 400 and resp.status_code < 500:
            raise RuntimeError('invalid request during form submission')
        if resp.status_code >= 500 and resp.status_code < 600:
            raise RuntimeError('internal server error during form submission')
