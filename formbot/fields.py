import re


def load_field(element, label=None):
    if label is not None:
        label = label.strip()

    if element.name == 'textarea':
        return Field(type='textarea',
                     name=element.get('name'),
                     display=label,
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
        elif ftype == 'email':
            default = element.text
            validator = email
        elif ftype == 'checkbox':
            default = element.get('checked', False)
            validator = checkbox
            extra = {
                'value': element.get('value', 'on')
            }
        # elif ftype == 'radio':
        #    return RadioField(name, label, required, None, element.get('value'))

        return Field(type=ftype,
                     name=name,
                     display=label,
                     required=required,
                     default=default,
                     validator=validator,
                     extra=extra)

    raise NotImplementedError('form element not supported')


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

    def merge(self, other):
        raise NotImplementedError()

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


EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
def email(data, field):
    if EMAIL_REGEX.match(data):
        return data
    else:
        raise ValueError('invalid email address')


TRUE_VALUES = ['true', 'y', 'yes', 'yup']
FALSE_VALUES = ['false', 'n', 'no', 'nope']
def checkbox(data, field):
    if not isinstance(data, bool):
        data = data.lower()
        if data.lower() in TRUE_VALUES:
            data = True
        elif data.lower() in FALSE_VALUES:
            data = False
        else:
            raise ValueError('invalid boolean value')

    if data:
        return field.extra['value']
    else:
        return None


# class RadioField(Field):
#     def __init__(self, name, display=None, required=False, default=False, retvalue=''):
#         super().__init__('radio', name, display, required, None)

#         self.choices = [retvalue]
#         if default:
#             self.value = retvalue

#     def fill(self, data):
#         if data in self.choices:
#             self.value = data
#         else:
#             raise ValueError('invalid input choice')

#     def merge(self, other):
#         assert self.fieldtype == other.fieldtype == 'radio'
#         assert self.name == other.name
#         self.display += ', ' + other.display

#         self.required = self.required or other.required

#         self.choices.extend(other.choices)
#         if other.value is not None:
#             self.value = other.value
