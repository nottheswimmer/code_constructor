import keyword
from typing import Union

from inflection import singularize

from constructor import field_types

UNIQUE_CLASSNAMES = set()
CLASS_SIGNATURES_TO_NAME = dict()


def cleanup():
    from constructor.main import PRINTED_SIGNATURES

    UNIQUE_CLASSNAMES.clear()
    CLASS_SIGNATURES_TO_NAME.clear()
    PRINTED_SIGNATURES.clear()


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


def primitive_to_type(primitive: Union[str, bool, int, list, dict], field_name: str) -> field_types.Type:
    # Strings
    if isinstance(primitive, str):
        return field_types.String(value=primitive, original_name=field_name, length=len(primitive))

    # Booleans
    if isinstance(primitive, bool):
        return field_types.Boolean(value=primitive, original_name=field_name)

    # Integers
    if isinstance(primitive, int):
        return field_types.Integer(value=primitive, original_name=field_name)

    # Floating-point types
    if isinstance(primitive, float):
        return field_types.Double(value=primitive, original_name=field_name)

    # Arrays
    if isinstance(primitive, list):
        if len(primitive) == 0:
            raise NotImplementedError("Empty lists are not supported.")
        primitive_type = None
        for subprimative in primitive:
            subprimative_type = primitive_to_type(subprimative, field_name=field_name)
            new_primitive_type = field_types.Array(value=primitive, original_name=field_name,
                                                   item_type=subprimative_type, length=len(primitive))
            if primitive_type is None:
                primitive_type = new_primitive_type
            else:
                # TODO: Something less arbitrary than using Java to check
                if new_primitive_type.to_java != primitive_type.to_java:
                    raise NotImplementedError(f"Arrays cannot contain different types ("
                                              f"{primitive_type.to_java} vs {new_primitive_type.to_java})")
                # We want the maximum length seen for the array size
                primitive_type.length = max(primitive_type.length, len(primitive))
        return primitive_type

    # Objects
    if isinstance(primitive, dict):
        from constructor.main import MetaClass

        field_name = singularize(field_name)
        primitive_class = MetaClass.from_dict(field_name, primitive)
        signature = primitive_class.get_name_and_field_signature()
        if signature in CLASS_SIGNATURES_TO_NAME:
            primitive_class.name = CLASS_SIGNATURES_TO_NAME[signature]
        else:
            print(signature, "not in", CLASS_SIGNATURES_TO_NAME)
            # print("brand new:", signature)
            if field_name not in UNIQUE_CLASSNAMES:
                UNIQUE_CLASSNAMES.add(field_name)
            else:
                i = 1
                while f"{field_name}{i}" in UNIQUE_CLASSNAMES:
                    i += 1
                primitive_class.name = f"{field_name}{i}"
                UNIQUE_CLASSNAMES.add(f"{field_name}{i}")
            CLASS_SIGNATURES_TO_NAME[signature] = primitive_class.name
        return field_types.Object(value=primitive, original_name=field_name, object_class=primitive_class)

    # Other (None/null not yet supported)
    raise NotImplementedError(f"{primitive!r} (type={type(primitive)}) is not supported!")

# TODO: Find a workaround that will let me use dir(__builtin__) or similar
#  __builtin__ does not work for recursively defined classes at the moment
PYTHON_BUILTIN_NAMES = ['ArithmeticError', 'AssertionError', 'AttributeError', 'BaseException', 'BlockingIOError',
                        'BrokenPipeError', 'BufferError', 'BytesWarning', 'ChildProcessError', 'ConnectionAbortedError',
                        'ConnectionError', 'ConnectionRefusedError', 'ConnectionResetError', 'DeprecationWarning',
                        'EOFError', 'Ellipsis', 'EnvironmentError', 'Exception', 'False', 'FileExistsError',
                        'FileNotFoundError', 'FloatingPointError', 'FutureWarning', 'GeneratorExit', 'IOError',
                        'ImportError', 'ImportWarning', 'IndentationError', 'IndexError', 'InterruptedError',
                        'IsADirectoryError', 'KeyError', 'KeyboardInterrupt', 'LookupError', 'MemoryError',
                        'ModuleNotFoundError', 'NameError', 'None', 'NotADirectoryError', 'NotImplemented',
                        'NotImplementedError', 'OSError', 'OverflowError', 'PendingDeprecationWarning',
                        'PermissionError', 'ProcessLookupError', 'RecursionError', 'ReferenceError', 'ResourceWarning',
                        'RuntimeError', 'RuntimeWarning', 'StopAsyncIteration', 'StopIteration', 'SyntaxError',
                        'SyntaxWarning', 'SystemError', 'SystemExit', 'TabError', 'TimeoutError', 'True', 'TypeError',
                        'UnboundLocalError', 'UnicodeDecodeError', 'UnicodeEncodeError', 'UnicodeError',
                        'UnicodeTranslateError', 'UnicodeWarning', 'UserWarning', 'ValueError', 'Warning',
                        'WindowsError', 'ZeroDivisionError', '__build_class__', '__debug__', '__doc__', '__import__',
                        '__loader__', '__name__', '__package__', '__spec__', 'abs', 'all', 'any', 'ascii', 'bin',
                        'bool', 'breakpoint', 'bytearray', 'bytes', 'callable', 'chr', 'classmethod', 'compile',
                        'complex', 'copyright', 'credits', 'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval',
                        'exec', 'exit', 'filter', 'float', 'format', 'frozenset', 'getattr', 'globals', 'hasattr',
                        'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len',
                        'license', 'list', 'locals', 'map', 'max', 'memoryview', 'min', 'next', 'object', 'oct', 'open',
                        'ord', 'pow', 'print', 'property', 'quit', 'range', 'repr', 'reversed', 'round', 'set',
                        'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars',
                        'zip']


def add_suffix_to_reserved_python_words(field_name: str, suffix: str) -> str:
    if field_name in PYTHON_BUILTIN_NAMES:
        return field_name + suffix
    if keyword.iskeyword(field_name):
        return field_name + suffix
    return field_name
