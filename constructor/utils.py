import random
from typing import Union

from inflection import singularize

from constructor import field_types
from constructor.words import ADJECTIVES, NOUNS


def any_to_upper_camel(name: str) -> str:
    if not name:
        return 'Name'
    name = name.replace(' ', '_')
    if '_' in name:
        return snake_to_upper_camel(name)
    if name[0].islower():
        name = name[0].upper() + name[1:]
    return name


def any_to_lower_camel(name: str) -> str:
    if not name:
        return 'Name'
    name = name.replace(' ', '_')
    if '_' in name:
        name = snake_to_upper_camel(name)
    if name[0].isupper():
        name = name[0].lower() + name[1:]
    return name


def snake_to_upper_camel(word: str) -> str:
    return ''.join(x.capitalize() or '_' for x in word.split('_'))


def camel_to_lower_snake(word: str) -> str:
    return ''.join(['_' + i.lower() if i.isupper()
                    else i for i in word]).lstrip('_')


def indent(i: int) -> str:
    return ' ' * i * 4


unique_classnames = set()


def create_unique_classname():
    random_adjective = random.choice(ADJECTIVES)
    random_noun = random.choice(NOUNS)
    name = any_to_upper_camel(random_adjective + "_" + random_noun).strip()
    if name not in unique_classnames:
        unique_classnames.add(name)
        return name
    # If the name came up with has been used, try again.
    return create_unique_classname()


class_signatures_to_name = dict()

def primitive_to_type(primitive: Union[str, bool, int, list, dict], field_name: str) -> field_types.Type:
    if isinstance(primitive, str):
        return field_types.String(value=primitive, length=len(primitive))
    if isinstance(primitive, bool):
        return field_types.Boolean(value=primitive)
    if isinstance(primitive, int):
        return field_types.Integer(value=primitive)
    if isinstance(primitive, list):
        if len(primitive) == 0:
            raise NotImplementedError("Empty lists are not supported.")
        primitive_type = None
        for subprimative in primitive:
            subprimative_type = primitive_to_type(subprimative, field_name=field_name)
            new_primitive_type = field_types.Array(value=primitive, item_type=subprimative_type, length=len(primitive))
            if primitive_type is None:
                primitive_type = new_primitive_type
            else:
                # TODO: Something less arbitrary than using Java to check
                if new_primitive_type.to_java != primitive_type.to_java:
                    raise NotImplementedError(f"Arrays cannot contain different types ({new_primitive_type.to_java} vs "
                                     f"{primitive_type.to_java})")
                # We want the maximum length seen for the array size
                primitive_type.length = max(primitive_type.length, len(primitive))
        return primitive_type
    if isinstance(primitive, dict):
        from constructor.main import MetaClass

        field_name = singularize(field_name)
        primitive_class = MetaClass.from_dict(field_name, primitive)
        # TODO: Something less arbitrary than using Java to check
        java_code = primitive_class.to_java()
        if java_code in class_signatures_to_name:
            primitive_class.name = class_signatures_to_name[java_code]
        else:
            if field_name not in unique_classnames:
                unique_classnames.add(field_name)
            else:
                primitive_class.name = create_unique_classname()
            class_signatures_to_name[java_code] = primitive_class.name
        return field_types.Object(value=primitive, object_class=primitive_class)

    raise NotImplementedError(f"{primitive!r} (type={type(primitive)}) is not supported!")
