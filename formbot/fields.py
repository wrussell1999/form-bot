import re


def load_field(element, label=None):
    if element.name == 'textarea':
        return Field('textarea',
                     element.get('name'),
                     label,
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
            return EmailField(name, label, required, default)
        elif fieldtype == 'checkbox':
            return CheckboxField(name, label, required, element.get('checked', False), element.get('value', 'on'))
        elif fieldtype == 'radio':
            return RadioField(name, label, required, None, element.get('value'))
        else:
            return Field(fieldtype, name, label, required, default)

    raise ValueError('invalid form input element')


class Field:
    def __init__(self, fieldtype, name, display=None, required=False, default=None):
        self.fieldtype = fieldtype
        self.name = name
        self.display = display

        self.required = required

        self.value = default

    @property
    def hidden(self):
        return self.fieldtype == 'hidden'

    def fill(self, data):
        self.value = data

    def merge(self, other):
        raise NotImplementedError()

    def __str__(self):
        if self.display:
            result = f'{self.display} [{self.name}] : {self.fieldtype}'
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

    def __init__(self, name, display=None, required=False, default=None):
        super().__init__('email', name, display, required, default)

    def fill(self, data):
        if EmailField.EMAIL_REGEX.match(data):
            super().fill(data)
        else:
            raise ValueError('invalid email address')


class CheckboxField(Field):
    TRUE = ['true', 'y', 'yes', 'yup']
    FALSE = ['false', 'n', 'no', 'nope']

    def __init__(self, name, display=None, required=False, default=False, retvalue='on'):
        super().__init__('checkbox', name, display, required, None)

        self.retvalue = retvalue
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


class RadioField(Field):
    def __init__(self, name, display=None, required=False, default=False, retvalue=''):
        super().__init__('radio', name, display, required, None)

        self.choices = [retvalue]
        if default:
            self.value = retvalue

    def fill(self, data):
        if data in self.choices:
            self.value = data
        else:
            raise ValueError('invalid input choice')

    def merge(self, other):
        assert self.fieldtype == other.fieldtype == 'radio'
        assert self.name == other.name
        self.display += ', ' + other.display

        self.required = self.required or other.required

        self.choices.extend(other.choices)
        if other.value is not None:
            self.value = other.value
