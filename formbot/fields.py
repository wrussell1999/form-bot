import re


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
