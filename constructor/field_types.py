"""
For reference, here are the builtin Python types left that we may want to cover:
  bytearray
  bytes
  classmethod
  complex
  dict
  enumerate
  filter
  float
  frozenset
  list
  map
  memoryview
  property
  range
  reversed
  set
  slice
  staticmethod
  super
  tuple
  type
  zip
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Tuple, Dict, Set

if TYPE_CHECKING:
    from constructor.main import MetaClass # pragma: no cover


class Type(ABC):
    def __init__(self, value, original_name: str):
        self.value = value
        self.original_name = original_name

    def to_python_to_dict_pair(self, name) -> Tuple[str, str]:
        return self.original_name, f"self.{name}"

    def to_python_from_dict_value(self) -> str:
        return f"d[{self.original_name!r}]"

    @property
    def c_includes(self) -> Set[str]:
        return set()

    @property
    def c_is_variable_length_array(self) -> bool:
        return False

    @property
    def python_imports(self) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, Set[str]]]:
        """
        :return: Standard library, third party, and local imports
        """
        return ({}, {}, {})

    @property
    def java_imports(self) -> Set[str]:
        return set()

    @property
    def embedded_objects(self) -> List['Object']:
        return []

    @property
    @abstractmethod
    def to_python(self) -> str:
        pass  # pragma: no cover

    @property
    @abstractmethod
    def to_python_value(self) -> str:
        pass  # pragma: no cover

    @property
    @abstractmethod
    def to_java_value(self) -> str:
        pass  # pragma: no cover

    @property
    @abstractmethod
    def to_c_value(self) -> str:
        pass  # pragma: no cover

    @property
    @abstractmethod
    def to_java(self) -> str:
        pass  # pragma: no cover

    @property
    @abstractmethod
    def to_go(self) -> str:
        pass  # pragma: no cover

    @property
    @abstractmethod
    def to_c(self) -> str:
        pass  # pragma: no cover

    @abstractmethod
    def to_c_printf(self, name: str) -> str:
        pass  # pragma: no cover


class String(Type):
    def __init__(self, value: str, original_name: str, length: int = 255):
        super().__init__(value=value, original_name=original_name)
        self.length = length

    to_python = 'str'
    to_java = 'String'
    to_go = 'string'
    to_c = 'char'
    c_is_variable_length_array = True

    @property
    def to_python_value(self) -> str:
        return repr(self.value)

    @property
    def to_java_value(self) -> str:
        import json

        # In Java, strings cannot be double quoted
        return json.dumps(self.value).lstrip('[').rstrip(']')

    @property
    def to_c_value(self) -> str:
        import json

        # In c, strings cannot be double quoted
        return json.dumps(self.value).lstrip('[').rstrip(']')

    def to_c_printf(self, name: str) -> str:
        return f'printf_s("{name}=\\"%s\\"", p->{name});'


class Integer(Type):
    to_python = 'int'

    @property
    def to_java(self) -> str:
        if self.max_value >= 2**31 or self.min_value < -2**31:
            return 'long'
        return 'int'

    @property
    def to_go(self) -> str:
        if self.max_value >= 2**31 or self.min_value < -2**31:
                return 'int64'
        return 'int'

    @property
    def to_c(self) -> str:
        if self.max_value >= 2**61 or self.min_value < -2**61:
            return 'long long'
        if self.max_value >= 2**31 or self.min_value < -2**31:
            return 'long'
        return 'int'

    def __init__(self, value: int, original_name: str):
        super().__init__(value, original_name)
        self.max_value = value
        self.min_value = value

    @property
    def to_python_value(self) -> str:
        return repr(self.value)

    @property
    def to_java_value(self) -> str:
        if self.to_java == 'long':
            return repr(self.value) + 'L'
        return repr(self.value)

    @property
    def to_c_value(self) -> str:
        return repr(self.value)

    def to_c_printf(self, name: str) -> str:
        return f'printf_s("{name}=%d", p->{name});'


class Double(Type):
    to_python = 'float'
    to_java = 'double'
    to_go = 'float64'

    def __init__(self, value: int, original_name: str):
        super().__init__(value, original_name)
        self.max_value = value
        self.min_value = value

    @property
    def to_c(self) -> str:
        if self.max_value >= 1.7E+308 or self.min_value < -2.3E-308:
            return 'long double'
        return 'double'

    @property
    def to_python_value(self) -> str:
        if self.max_value == float('inf'):
            return 'float("inf")'
        if self.min_value == float('-inf'):
            return 'float("-inf")'
        if self.min_value == float('nan'):
            return 'float("nan")'
        return repr(self.value)

    @property
    def to_java_value(self) -> str:
        if self.max_value == float('inf'):
            return "Float.POSITIVE_INFINITY"
        if self.min_value == float('-inf'):
            return "Float.NEGATIVE_INFINITY"
        if self.min_value == float('nan'):
            return "Float.NaN"
        return repr(self.value)

    @property
    def to_go_value(self) -> str:
        # TODO: Go imports for math will be needed once there's
        #  an actual usage example for Go
        if self.max_value == float('inf'):
            return repr("math.Inf(1)")
        if self.min_value == float('-inf'):
            return repr("math.Inf(-1)")
        if self.min_value == float('nan'):
            return repr("math.NaN()")
        return repr(self.value)

    @property
    def to_c_value(self) -> str:
        return repr(self.value)

    def to_c_printf(self, name: str) -> str:
        return f'printf_s("{name}=%f", p->{name});'


class Boolean(Type):
    to_python = 'bool'
    to_java = 'boolean'
    to_go = 'bool'
    to_c = 'bool'
    c_includes = {'stdbool.h'}

    @property
    def to_python_value(self) -> str:
        return repr(self.value)

    @property
    def to_java_value(self) -> str:
        # In Java, booleans are false rather than False, or true rather than True
        return repr(self.value).lower()

    @property
    def to_c_value(self) -> str:
        # In c, booleans are false rather than False, or true rather than True
        return repr(self.value).lower()

    def to_c_printf(self, name: str) -> str:
        return f'printf_s("{name}=%s\", p->{name} ? "true" : "false");'


class Array(Type):
    c_is_variable_length_array = True

    def __init__(self, value: List, original_name: str, item_type: Type, length: int = 255):
        super().__init__(value=value, original_name=original_name)
        self.item_type = item_type
        self.length = length

    def to_python_to_dict_pair(self, name) -> Tuple[str, str]:
        if isinstance(self.item_type, Array) or isinstance(self.item_type, Object):
            original_name_copy = self.item_type.original_name
            self.item_type.original_name = 'o'
            string = f"[{self.item_type.to_python_to_dict_pair('o')[1].lstrip('self.')} for o in self.{name}]"
            self.item_type.original_name = original_name_copy
            return self.original_name, string
        return self.original_name, f"self.{name}"

    def to_python_from_dict_value(self) -> str:
        if isinstance(self.item_type, Array) or isinstance(self.item_type, Object):
            original_name_copy = self.item_type.original_name
            looped_to_dict_value = self.item_type.to_python_from_dict_value()\
                .replace(f'd[{self.item_type.original_name!r}]', 'o', 1)
            string = f"[{looped_to_dict_value} for o in d[{self.original_name!r}]]"
            self.item_type.original_name = original_name_copy
            return string
        return f"d[{self.original_name!r}]"

    @property
    def to_python_value(self) -> str:
        original_value = self.item_type.value
        value = "["
        for item in self.value:
            self.item_type.value = item
            value += self.item_type.to_python_value + ", "
        value = value.rstrip(", ")
        value += "]"
        self.item_type.value = original_value
        return value

    @property
    def to_java_value(self) -> str:
        # Array literal
        original_value = self.item_type.value
        value = f"new {self.item_type.to_java}[]{{"
        for item in self.value:
            self.item_type.value = item
            value += self.item_type.to_java_value + ", "
        value = value.rstrip(", ")
        value += "}"
        self.item_type.value = original_value
        return value

    @property
    def to_c_value(self) -> str:
        # Array literal
        original_value = self.item_type.value
        value = f"({self.item_type.to_c}[]) {{"
        for item in self.value:
            self.item_type.value = item
            value += "*" if isinstance(self.item_type, Object) else ""
            value += self.item_type.to_c_value + ", "
        value = value.rstrip(", ")
        value += "}"
        self.item_type.value = original_value
        return value

    @property
    def python_imports(self) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, Set[str]]]:
        return ({"typing": {"List"}}, {}, {})

    @property
    def java_imports(self) -> Set[str]:
        return {"java.util.Arrays"}

    @property
    def embedded_objects(self) -> List['Object']:
        return self.item_type.embedded_objects

    @property
    def to_python(self) -> str:
        return f'List[{self.item_type.to_python}]'

    @property
    def to_java(self) -> str:
        return f'{self.item_type.to_java}[]'

    @property
    def to_go(self) -> str:
        return f'[]{self.item_type.to_go}'

    @property
    def to_c(self) -> str:
        return self.item_type.to_c

    @property
    def c_includes(self) -> Set[str]:
        return self.item_type.c_includes

    def to_c_printf(self, name: str) -> str:
        return f'printf_s("{name}={{...}}");'


class Object(Type):
    def __init__(self, value: dict, original_name: str, object_class: 'MetaClass'):
        super().__init__(value=value, original_name=original_name)
        self.object_class = object_class

    @property
    def embedded_objects(self) -> List['Object']:
        return [self]

    def to_python_to_dict_pair(self, name) -> Tuple[str, str]:
        return self.original_name, f"self.{name}.to_dict()"

    def to_python_from_dict_value(self) -> str:
        return f"""{self.to_python.strip("'")}.from_dict(d[{self.original_name!r}])"""

    @property
    def to_python_value(self) -> str:
        from constructor.main import MetaClass

        # Not using self.object_class so that overriding the value is supported...
        object_class = MetaClass.from_dict(name=self.object_class.name, data=self.value)
        return object_class.generate_python_object()

    @property
    def to_java_value(self) -> str:
        from constructor.main import MetaClass

        # Not using self.object_class so that overriding the value is supported...
        object_class = MetaClass.from_dict(name=self.object_class.name, data=self.value)
        return object_class.generate_java_object()

    @property
    def to_c_value(self) -> str:
        from constructor.main import MetaClass

        # Not using self.object_class so that overriding the value is supported...
        object_class = MetaClass.from_dict(name=self.object_class.name, data=self.value)
        return object_class.generate_c_object()

    @property
    def to_python(self) -> str:
        return f"'{self.object_class.python_name}'"

    @property
    def to_java(self) -> str:
        return self.object_class.java_name

    @property
    def to_go(self) -> str:
        return self.object_class.go_name

    @property
    def to_c(self) -> str:
        return self.object_class.c_name

    @property
    def c_includes(self) -> Set[str]:
        return set(self.object_class.get_c_includes())

    @property
    def python_imports(self) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, Set[str]]]:
        return self.object_class.get_python_imports()

    @property
    def java_imports(self) -> Set[str]:
        return set(self.object_class.get_java_imports())

    def to_c_printf(self, name: str) -> str:
        return f'{self.object_class.c_name}_print(&p->{name});'
