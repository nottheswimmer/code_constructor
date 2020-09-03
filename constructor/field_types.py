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
from typing import Set, TYPE_CHECKING, List

if TYPE_CHECKING:
    from constructor.main import MetaClass


class Type(ABC):
    def __init__(self, value):
        self.value = value

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
    def c_field_suffix(self) -> str:
        return ''

    @property
    def embedded_objects(self) -> List['Object']:
        return []


class String(Type):
    def __init__(self, value: str, length: int = 255):
        super().__init__(value=value)
        self.length = length

    to_python = 'str'
    to_java = 'String'
    to_go = 'string'
    to_c = 'char'

    @property
    def to_python_value(self) -> str:
        return repr(self.value)

    @property
    def c_field_suffix(self) -> str:
        return f"[{self.length}]"


class Integer(Type):
    to_python = 'int'
    to_java = 'int'
    to_go = 'int'
    to_c = 'int'

    @property
    def to_python_value(self) -> str:
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


class Array(Type):
    def __init__(self, value: List, item_type: Type, length: int = 255):
        super().__init__(value=value)
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
    def c_field_suffix(self) -> str:
        return self.item_type.c_field_suffix + f'[{self.length}]'  # TODO: Array size

    @property
    def c_includes(self) -> Set[str]:
        return self.item_type.c_includes


class Object(Type):
    def __init__(self, value: dict, object_class: 'MetaClass'):
        super().__init__(value=value)
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
    def c_field_suffix(self) -> str:
        return ''

    @property
    def c_includes(self) -> Set[str]:
        return set(self.object_class.c_includes)
