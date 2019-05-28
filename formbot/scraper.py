import requests
from bs4 import BeautifulSoup


class FormScraper:
    def __init__(self, url):
        self.url = url

    def extract(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, features='html.parser')

        form = Form(soup.form['method'], soup.form['action'])

        inputs = soup.form.find_all(['input', 'textarea'])
        for element in inputs:
            if element.name == 'input':
                field = Field(element.get('type'),
                              element.get('name'),
                              element.get('required', False),
                              element.get('value', None))
            elif element.name == 'textarea':
                field = Field('textarea',
                              element.get('name'),
                              element.get('required', False),
                              element.text)
            else:
                raise RuntimeError('invalid form input element')

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

        self.values = {}

    def add_field(self, field, id=None):
        self.fields.append(field)

        self.name_lookup[field.name] = field
        if id:
            self.id_lookup[id] = field

    def get_field(self, name=None, id=None):
        if name and id:
            raise RuntimeError('cannot get by both name and id')
        elif name:
            return self.name_lookup[name]
        elif id:
            return self.id_lookup[id]
        else:
            RuntimeError('missing search specifier (should be name or id)')

    def fill_field(self, name, value):
        self.values[name] = value

    def submit(self):
        # ensure all required fields are provided
        for field in self.fields:
            if field.required and field.name not in self.values:
                raise KeyError(f'{field.name} is required and has not been provided')

        # send form
        if self.method == 'GET':
            resp = requests.get(self.action, data=self.values)
        elif self.method == 'POST':
            resp = requests.post(self.action, data=self.values)
        else:
            raise RuntimeError(f'{self.method} is not a valid form submission method')

        # check for submission errors
        if resp.status_code >= 400 and resp.status_code < 500:
            raise RuntimeError('invalid request during form submission')
        if resp.status_code >= 500 and resp.status_code < 600:
            raise RuntimeError('internal server error during form submission')


class Field:
    def __init__(self, fieldtype, name, required=False, default=None):
        self.fieldtype = fieldtype
        self.name = name
        self.display_name = None
        self.default = default
        self.required = required

    @property
    def hidden(self):
        return self.fieldtype == 'hidden'

    def __str__(self):
        if self.display_name:
            result = f'{self.display_name} [{self.name}] : {self.fieldtype}'
        else:
            result = f'{self.name} : {self.fieldtype}'

        if self.default:
            result += f' = {self.default}'
        if self.required:
            result = f'* {result}'
        if self.hidden:
            result = f'({result})'

        return result
