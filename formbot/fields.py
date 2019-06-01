import re


class Field:
    def __init__(self, type, name, display=None, required=False, default=None, validator=None, extra=None):
        self.type = type
        self.name = name
        self.display = display

        self.required = required

        self.validator = validator
        self.extra = extra or {}

        self.data = None
        if default:
            self.fill(default)

    @property
    def hidden(self):
        return self.type == 'hidden'

    def fill(self, data):
        if self.validator:
            self.data = self.validator(data, self)
        else:
            self.data = data

    def __str__(self):
        if self.display:
            result = f'{self.display} [{self.name}] : {self.type}'
        else:
            result = f'{self.name} : {self.type}'

        if self.data is not None:
            result += f' = {self.data}'
        if self.required:
            result = f'* {result}'
        if self.hidden:
            result = f'({result})'

        return result


def email(data, field):
    # init static variables
    if not hasattr(email, 'EMAIL_REGEX'):
        email.REGEX = re.compile(
            r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

    if email.REGEX.match(data):
        return data
    else:
        raise ValueError('invalid email address')


def checkbox(data, field):
    # init static variables
    if not hasattr(checkbox, 'TRUE_VALUES'):
        checkbox.TRUE_VALUES = ['true', 'y', 'yes', 'yup']
    if not hasattr(checkbox, 'FALSE_VALUES'):
        checkbox.FALSE_VALUES = ['false', 'n', 'no', 'nope']

    if not isinstance(data, bool):
        data = data.lower()
        if data.lower() in checkbox.TRUE_VALUES:
            data = True
        elif data.lower() in checkbox.FALSE_VALUES:
            data = False
        else:
            raise ValueError('invalid boolean value')

    if data:
        return field.extra['value']
    else:
        return None


def radio(data, field):
    data = data.lower()

    for value in field.extra['values']:
        if data == value:
            return value

    for i, label in enumerate(field.extra['labels']):
        if data == label:
            return field.extra['values'][i]

    raise ValueError('invalid input choice')
