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
    from constructor.main import MetaClass


class Type(ABC):
    def __init__(self, value, original_name: str):
        self.value = value
        self.original_name = original_name

    @property
    @abstractmethod
    def to_python(self) -> str:
        pass

    @property
    @abstractmethod
    def to_python_value(self) -> str:
        pass

    @property
    @abstractmethod
    def to_java_value(self) -> str:
        pass

    @property
    @abstractmethod
    def to_java(self) -> str:
        pass

    @property
    @abstractmethod
    def to_go(self) -> str:
        pass

    @property
    @abstractmethod
    def to_c(self) -> str:
        pass

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


class Integer(Type):
    to_python = 'int'
    to_java = 'int'
    to_go = 'int'
    to_c = 'int'

    @property
    def to_python_value(self) -> str:
        return repr(self.value)

    @property
    def to_java_value(self) -> str:
        return repr(self.value)


class Double(Type):
    to_python = 'float'
    to_java = 'double'
    to_go = 'float64'
    to_c = 'double'

    @property
    def to_python_value(self) -> str:
        return repr(self.value)

    @property
    def to_java_value(self) -> str:
        return repr(self.value)


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


class Array(Type):
    c_is_variable_length_array = True

    def __init__(self, value: List, original_name: str, item_type: Type, length: int = 255):
        super().__init__(value=value, original_name=original_name)
        self.item_type = item_type
        self.length = length

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


class Object(Type):
    def __init__(self, value: dict, original_name: str, object_class: 'MetaClass'):
        super().__init__(value=value, original_name=original_name)
        self.object_class = object_class

    @property
    def embedded_objects(self) -> List['Object']:
        return [self]

    @property
    def to_python_value(self) -> str:
        from constructor.main import MetaClass

        # Not using self.object_class so that overriding the value is supported...
        object_class = MetaClass.from_dict(name=self.object_class.name, data=self.value)
        return object_class.to_python_construction()

    @property
    def to_java_value(self) -> str:
        from constructor.main import MetaClass

        # Not using self.object_class so that overriding the value is supported...
        object_class = MetaClass.from_dict(name=self.object_class.name, data=self.value)
        return object_class.to_java_construction()

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
        return set(self.object_class.c_includes)

    @property
    def python_imports(self) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, Set[str]]]:
        return self.object_class.python_imports

    @property
    def java_imports(self) -> Set[str]:
        return set(self.object_class.java_imports)