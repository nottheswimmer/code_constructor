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
    from main import MetaClass


class Type(ABC):
    @property
    @abstractmethod
    def to_python(self) -> str:
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
    def __init__(self, length: int = 255):
        self.length = length

    to_python = 'str'
    to_java = 'String'
    to_go = 'string'
    to_c = 'char'

    @property
    def c_field_suffix(self) -> str:
        return f"[{self.length}]"


class Integer(Type):
    to_python = 'int'
    to_java = 'int'
    to_go = 'int'
    to_c = 'int'


class Boolean(Type):
    to_python = 'bool'
    to_java = 'boolean'
    to_go = 'bool'
    to_c = 'bool'
    c_includes = {'stdbool.h'}


class Array(Type):
    def __init__(self, item_type: Type, length: int = 255):
        self.item_type = item_type
        self.length = length

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
    def __init__(self, object_class: 'MetaClass'):
        self.object_class = object_class

    @property
    def embedded_objects(self) -> List['Object']:
        return [self]

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
