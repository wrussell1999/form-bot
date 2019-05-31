import requests
from bs4 import BeautifulSoup

from . import fields


class FormScraper:
    def __init__(self, url):
        self.url = url

    def extract(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, features='html.parser')

        form = Form(soup.form.get('method', 'GET'), soup.form.get('action'))

        inputs = soup.form.find_all(['input', 'textarea'])
        for element in inputs:
            field = fields.load_field(element)
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
