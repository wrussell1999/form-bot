import requests

class Form:
    def __init__(self, session, method, action):
        self.session = session
        self.method = method.upper()
        self.action = action

        print(self.action)

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
