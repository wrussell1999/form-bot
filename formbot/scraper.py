import requests
import re
from bs4 import BeautifulSoup


class FormScraper:
    def __init__(self, url):
        self.url = url

    def extract(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, features='html.parser')

        form = Form(soup.form.get('method', 'GET'), soup.form.get('action'))

        inputs = soup.form.find_all(['input', 'textarea'])
        for element in inputs:
            field = load_field(element)
            if field is None:
                continue

            # label in attribute
            for attr in element.attrs:
                if 'label' in attr:
                    field.display_name = element.attrs[attr]
                    break

            form.add_field(field, element.get('id'))

        # label in tag
        labels = soup.form.find_all('label')
        for label in labels:
            field = form.get_field(id=label['for'])
            field.display_name = label.text

        return form


class Form:
    def __init__(self, method, action):
        self.method = method.upper()
        self.action = action

        self.fields = []
        self.name_lookup = {}
        self.id_lookup = {}

    def add_field(self, field, id=None):
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
            if field.required and field.value is None:
                raise KeyError(f'{field.name} is required and has not been provided')

            if field.value is not None:
                values[field.name] = field.value

        # send form
        if self.method == 'GET':
            resp = requests.get(self.action, data=values)
        elif self.method == 'POST':
            resp = requests.post(self.action, data=values)
        else:
            raise ValueError(f'{self.method} is not a valid form submission method')

        # check for submission errors
        if resp.status_code >= 400 and resp.status_code < 500:
            raise RuntimeError('invalid request during form submission')
        if resp.status_code >= 500 and resp.status_code < 600:
            raise RuntimeError('internal server error during form submission')


def load_field(element):
    if element.name == 'textarea':
        return Field('textarea',
                     element.get('name'),
                     element.get('required', False),
                     element.text)

    if element.name == 'input':
        fieldtype = element['type']
        name = element['name']
        required = element.get('required', False)
        default = element.get('default', None)

        if fieldtype in ('color', 'file'):
            raise ValueError(f'unsupported field type "{fieldtype}"')
        elif fieldtype in ('submit', 'image', 'button'):
            return None
        elif fieldtype == 'email':
            return EmailField(name, required, default)
        elif fieldtype == 'checkbox':
            return CheckboxField(name, required, element.get('checked', False), element.get('value', 'on'))
        else:
            return Field(fieldtype, name, required, default)

    raise ValueError('invalid form input element')


class Field:
    def __init__(self, fieldtype, name, required=False, default=None):
        self.fieldtype = fieldtype
        self.name = name
        self.display_name = None

        self.required = required

        self.value = default

    @property
    def hidden(self):
        return self.fieldtype == 'hidden'

    def fill(self, data):
        self.value = data

    def __str__(self):
        if self.display_name:
            result = f'{self.display_name} [{self.name}] : {self.fieldtype}'
        else:
            result = f'{self.name} : {self.fieldtype}'

        if self.value is not None:
            result += f' = {self.value}'
        if self.required:
            result = f'* {result}'
        if self.hidden:
            result = f'({result})'

        return result


class EmailField(Field):
    EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

    def __init__(self, name, required=False, default=None):
        super().__init__('email', name, required, default)

    def fill(self, data):
        if EmailField.EMAIL_REGEX.match(data):
            super().fill(data)
        else:
            raise ValueError('invalid email address')


class CheckboxField(Field):
    TRUE = ['true', 'y', 'yes', 'yup']
    FALSE = ['false', 'n', 'no', 'nope']

    def __init__(self, name, required=False, default=False, retvalue='on'):
        self.retvalue = retvalue

        super().__init__('checkbox', name, None, default)

        self.fill(default)

    def fill(self, data):
        if not isinstance(data, bool):
            data = data.lower()
            if data.lower() in CheckboxField.TRUE:
                data = True
            elif data.lower() in CheckboxField.FALSE:
                data = False
            else:
                raise ValueError('invalid boolean value')

        if data:
            self.value = self.retvalue
        else:
            self.value = None
