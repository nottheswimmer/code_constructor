import json
from typing import Dict, List, Union, Set

from constructor.field_types import Type, String, Integer, Boolean, Array
from constructor.utils import any_to_upper_camel, any_to_lower_camel, camel_to_lower_snake, indent, primitive_to_type


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

PRINTED_SIGNATURES: Dict[str, Set[str]] = {}

class MetaClass:
    def __init__(self, name: str, fields: Dict[str, Type]):
        # Normalize class name as UpperCamel
        self.name = any_to_upper_camel(name)

        # Normalize field name as lowerCamel
        self.fields = {any_to_lower_camel(field): t for field, t in fields.items()}

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Union[str, bool, int, list]]):
        # TODO: Support for None
        # TODO: Support for Dict (nested structures)
        fields = {}
        for key, value in data.items():
            fields[key] = primitive_to_type(value, field_name=key)

        return cls(name=name, fields=fields)

    @classmethod
    def from_json(cls, name: str, data: str):
        data = json.loads(data)
        if isinstance(data, list):
            raise NotImplementedError("The top-level object cannot be an array")
        return cls.from_dict(name, data)

    @property
    def python_name(self) -> str:
        import keyword
        if self.name in PYTHON_BUILTIN_NAMES or keyword.iskeyword(self.name):
            return self.name + "Object"
        return self.name

    @property
    def java_name(self) -> str:
        return self.name

    @property
    def go_name(self) -> str:
        return self.name

    @property
    def c_name(self) -> str:
        return self.name

    @property
    def python_fields(self) -> Dict[str, Type]:
        import keyword

        def add_field_to_reserved_words(field_name: str) -> str:
            if field_name in PYTHON_BUILTIN_NAMES:
                return field_name + "_field"
            if keyword.iskeyword(field_name):
                return field_name + "_field"
            return field_name

        return {add_field_to_reserved_words(camel_to_lower_snake(field)): t for field, t in self.fields.items()}

    @property
    def java_fields(self) -> Dict[str, Type]:
        return {field: t for field, t in self.fields.items()}

    @property
    def go_fields(self) -> Dict[str, Type]:
        return {any_to_upper_camel(field): t for field, t in self.fields.items()}

    @property
    def c_fields(self) -> Dict[str, Type]:
        return {camel_to_lower_snake(field): t for field, t in self.fields.items()}

    @property
    def c_includes(self) -> List[str]:
        includes = set()
        for field_type in self.fields.values():
            includes.update(field_type.c_includes)
        return sorted(includes)

    @property
    def name_and_field_signature(self) -> str:
        """
        Return an arbitrary string unique to the name and fields of this class
        """
        return self.name + '@@@' + str(sorted(self.java_fields))

    def to_python(self) -> str:
        top_level = 'python' not in PRINTED_SIGNATURES
        if top_level:
            PRINTED_SIGNATURES['python'] = {self.name_and_field_signature}
        elif self.name_and_field_signature in PRINTED_SIGNATURES['python']:
            return ''
        else:
            PRINTED_SIGNATURES['python'].add(self.name_and_field_signature)

        lines = []

        for field, t in self.c_fields.items():
            for field_type in t.embedded_objects:
                object_string = field_type.object_class.to_python()
                if object_string:
                    lines.append(object_string)
                    lines.append('')

        lines.append(f"class {self.python_name}:")

        # Constructor
        constructor = indent(1) + "def __init__(self, "
        constructor_body_lines = []
        for field, t in self.python_fields.items():
            constructor += f"{field}: {t.to_python}, "
            constructor_body_lines.append(indent(2) + f"self.{field} = {field}")
        # Remove trailing ", " and close signature / open body
        constructor = constructor[:-2] + "):"
        lines.append(constructor)
        lines += constructor_body_lines

        # Repr method
        lines.append('')
        lines.append(indent(1) + "def __repr__(self):")
        string_body = indent(2) + f"return f\"{self.python_name}("
        for field, t in self.python_fields.items():
            string_body += f"{field}={{self.{field}!r}}, "
        string_body = string_body[:-2] + ")\""
        lines.append(string_body)

        if top_level:
            del PRINTED_SIGNATURES['python']
        return '\n'.join(lines)

    def to_python_construction(self) -> str:
        line = f"{self.python_name}("
        for field, t in self.python_fields.items():
            line += f"{field}={t.to_python_value}, "
        line = line.rstrip(", ") + ")"
        return line

    def to_python_example(self) -> str:
        import keyword

        test_var_name = camel_to_lower_snake(self.name)
        if test_var_name in PYTHON_BUILTIN_NAMES or keyword.iskeyword(test_var_name):
            test_var_name += "_object"
        lines = [f"{test_var_name} = {self.to_python_construction()}", f"print({test_var_name})"]
        return '\n'.join(lines)


    def to_java(self) -> str:
        top_level = 'java' not in PRINTED_SIGNATURES
        if top_level:
            PRINTED_SIGNATURES['java'] = {self.name_and_field_signature}
        elif self.name_and_field_signature in PRINTED_SIGNATURES['java']:
            return ''
        else:
            PRINTED_SIGNATURES['java'].add(self.name_and_field_signature)

        lines = []

        lines.append(f"class {self.java_name} {{")  # TODO: Scope
        field_lines = []
        for field, t in self.java_fields.items():
            # TODO: We probably don't actually want public fields. Java prefers getters and setters.
            field_lines.append(indent(1) + f"public {t.to_java} {field};")  # TODO: Scope
        lines += field_lines
        lines.append('')

        # No constructor is needed if we have no fields
        if self.java_fields:
            constructor = indent(1) + f"public {self.java_name}("  # TODO: Scope
            constructor_lines = []
            for field, t in self.java_fields.items():
                constructor += f"{t.to_java} {field}, "
                constructor_lines.append(indent(2) + f"this.{field} = {field};")
            # Remove trailing ", " and close signature / open body
            constructor = constructor[:-2] + ") {"
            lines.append(constructor)
            lines += constructor_lines

            # Add closing curly
            lines.append(indent(1) + "}")

        # Add final closing curly
        lines.append("}")

        for field, t in self.c_fields.items():
            for field_type in t.embedded_objects:
                string = field_type.object_class.to_java()
                if string:
                    lines.append('')
                    lines.append(string)

        if top_level:
            del PRINTED_SIGNATURES['java']
        return '\n'.join(lines)

    def to_go(self) -> str:
        top_level = 'go' not in PRINTED_SIGNATURES
        if top_level:
            PRINTED_SIGNATURES['go'] = {self.name_and_field_signature}
        elif self.name_and_field_signature in PRINTED_SIGNATURES['go']:
            return ''
        else:
            PRINTED_SIGNATURES['go'].add(self.name_and_field_signature)

        lines = []

        for field, t in self.c_fields.items():
            for field_type in t.embedded_objects:
                string = field_type.object_class.to_go()
                if string:
                    lines.append(string)
                    lines.append('')

        lines.append(f"type {self.go_name} struct {{")
        constructor_lines = []
        for field, t in self.go_fields.items():
            constructor_lines.append(indent(1) + f"{field} {t.to_go}")  # TODO: Scope
        lines += constructor_lines
        lines.append("}")

        if top_level:
            del PRINTED_SIGNATURES['go']
        return '\n'.join(lines)

    def to_c(self, imports=True) -> str:
        top_level = 'c' not in PRINTED_SIGNATURES
        if top_level:
            PRINTED_SIGNATURES['c'] = {self.name_and_field_signature}
        elif self.name_and_field_signature in PRINTED_SIGNATURES['c']:
            return ''
        else:
            PRINTED_SIGNATURES['c'].add(self.name_and_field_signature)

        lines = []
        if imports:
            for include in self.c_includes:
                lines.append(f"#include <{include}>")
            # Add another line if there were includes needed
            if lines:
                lines.append('')

        for field, t in self.c_fields.items():
            for field_type in t.embedded_objects:
                string = field_type.object_class.to_c(imports=False)
                if string:
                    lines.append(string)
                    lines.append('')

        lines.append(f"struct {self.c_name} {{")
        for field, t in self.c_fields.items():
            lines.append(indent(1) + f"{t.to_c} {field + t.c_field_suffix};")
        lines.append("};")

        if top_level:
            del PRINTED_SIGNATURES['c']
        return '\n'.join(lines)

    def _dump(self):
        print("[To Python]")
        print('```python')
        print(self.to_python())
        print()
        print(self.to_python_example())
        print('```')
        print()

        print("[To Java]")
        print('```java')
        print(self.to_java())
        print('```')
        print()

        print("[To Go]")
        print('```go')
        print(self.to_go())
        print('```')
        print()

        print("[To C]")
        print('```c')
        print(self.to_c())
        print('```')
        print()


def main():
    person = MetaClass("person",
                       {"name": String("Hello"),
                        "age": Integer(14),
                        "happy": Boolean(True),
                        "favorite_colors": Array(value=["Blue"], item_type=String(""))})
    # person._dump()

    car_owner = MetaClass.from_json("CarOwner", """\
{
    "name":"John",
    "age":30,
    "cars": [
        "Ford",
        "BMW",
        "Fiat"
    ]
}
""")
    # car_owner._dump()

    squad = MetaClass.from_json("Squad", """\
{
  "squadName": "Super hero squad",
  "homeTown": "Metro City",
  "formed": 2016,
  "secretBase": "Super tower",
  "active": true,
  "members": [
    {
      "name": "Molecule Man",
      "age": 29,
      "secretIdentity": "Dan Jukes",
      "powers": [
        "Radiation resistance",
        "Turning tiny",
        "Radiation blast"
      ]
    },
    {
      "name": "Madame Uppercut",
      "age": 39,
      "secretIdentity": "Jane Wilson",
      "powers": [
        "Million tonne punch",
        "Damage resistance",
        "Superhuman reflexes"
      ]
    },
    {
      "name": "Eternal Flame",
      "age": 1000000,
      "secretIdentity": "Unknown",
      "powers": [
        "Immortality",
        "Heat Immunity",
        "Inferno",
        "Teleportation",
        "Interdimensional travel"
      ]
    }
  ]
}
""")
    squad._dump()

    course = MetaClass.from_json("course", """\
{
  "id": "string",
  "uuid": "string",
  "externalId": "string",
  "dataSourceId": "string",
  "courseId": "string",
  "name": "string",
  "description": "string",
  "created": "2020-08-30T23:47:15.769Z",
  "modified": "2020-08-30T23:47:15.769Z",
  "organization": true,
  "ultraStatus": "Undecided",
  "allowGuests": true,
  "closedComplete": true,
  "termId": "string",
  "availability": {
    "available": "Yes",
    "duration": {
      "type": "Continuous",
      "start": "2020-08-30T23:47:15.769Z",
      "end": "2020-08-30T23:47:15.769Z",
      "daysOfUse": 0
    }
  },
  "enrollment": {
    "type": "InstructorLed",
    "start": "2020-08-30T23:47:15.769Z",
    "end": "2020-08-30T23:47:15.769Z",
    "accessCode": "string"
  },
  "locale": {
    "id": "string",
    "force": true
  },
  "hasChildren": true,
  "parentId": "string",
  "externalAccessUrl": "string",
  "guestAccessUrl": "string"
}
""")
    # course._dump()

if __name__ == '__main__':
    main()
