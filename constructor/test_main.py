import os
import sys
import json
import subprocess
from abc import ABC, abstractmethod
from importlib.util import spec_from_loader, module_from_spec
from typing import Tuple
from unittest import TestCase

from constructor.main import MetaClass
from constructor.utils import cleanup

# TEST ENVIRONMENT CONFIGURATION
JAVAC_BINARY_PATH = 'javac'
GO_BINARY_PATH = 'go'
GCC_BINARY_PATH = 'gcc'

# AUTO TEST ENVIRONMENT CONFIGURATION
IS_WINDOWS = os.name == 'nt'


class AbstractTestClass(ABC):
    @property
    @abstractmethod
    def class_name(self) -> str:
        pass

    @property
    @abstractmethod
    def test_json(self) -> str:
        pass

    @property
    @abstractmethod
    def expected_classes(self) -> Tuple[str]:
        pass

    def setUp(self):
        self.meta_class = MetaClass.from_json(self.class_name, self.test_json)
        self.testlang = None
        if hasattr(self, '_testMethodName'):
            self.testlang = self._testMethodName.split('_')[1]

        # Python
        if not self.testlang or self.testlang == 'python':
            self.python_source = self.meta_class.generate_python()
            self.python_module_name = 'test_module'
            self.python_file_name = f"test_module.py"
            source = self.meta_class.generate_python()
            spec = spec_from_loader(self.python_module_name, loader=None)
            self.python_module = module_from_spec(spec)
            exec(source, self.python_module.__dict__)
            sys.modules[self.python_module_name] = self.python_module_name

        # Java
        if not self.testlang or self.testlang == 'java':
            self.java_source = self.meta_class.generate_java()
            self.java_file_name = f"{self.class_name}.java"
            self.java_class_file_names = []
            for classname in self.expected_classes:
                self.java_class_file_names.append(f"{classname}.class")
            with open(self.java_file_name, "w") as f:
                f.write(self.java_source)

        # Go
        if not self.testlang or self.testlang == 'go':
            self.go_source = self.meta_class.generate_go()
            self.go_file_name = f"{self.class_name}.go"
            self.go_object_file_name = f"{self.class_name}.o"
            with open(self.go_file_name, "w") as f:
                f.write(self.go_source)

        # C
        if not self.testlang or self.testlang == 'c':
            self.c_source = self.meta_class.generate_c()
            self.c_file_name = f"{self.class_name}.c"
            self.c_executable_file_name = f"{self.class_name}"
            if IS_WINDOWS:
                self.c_executable_file_name += '.exe'
            with open(self.c_file_name, "w") as f:
                f.write(self.c_source)

    def tearDown(self):
        cleanup()  # TODO: This should NOT be necessary...

        # Python
        if not self.testlang or self.testlang == 'python':
            del sys.modules[self.python_module_name]

        # Java
        if not self.testlang or self.testlang == 'java':
            # TODO: Remove .class files unintentionally created as well?
            for fp in (self.java_file_name, *self.java_class_file_names):
                if os.path.exists(fp):
                    os.remove(fp)

        # Go
        if not self.testlang or self.testlang == 'go':
            for fp in (self.go_file_name, self.go_object_file_name):
                if os.path.exists(fp):
                    os.remove(fp)

        # C
        if not self.testlang or self.testlang == 'c':
            for fp in (self.c_file_name, self.c_executable_file_name):
                if os.path.exists(fp):
                    os.remove(fp)

    def test_python_compiles(self):
        print(self.python_source)
        return compile(self.python_source, self.python_file_name, 'exec')

    def test_python_has_expected_classes(self):
        compiled = self.test_python_compiles()
        for expected_class in self.expected_classes:
            self.assertIn(expected_class, compiled.co_names,
                          f"Output ({compiled.co_names}) is missing the {expected_class} class")

    def test_python_main_runs(self):
        self.python_module.main()

    def test_python_to_json_output_matches_original_structure(self):
        base_class = getattr(self.python_module, self.class_name)
        base_object = base_class.from_json(self.test_json)
        test_json = base_object.to_json()
        self.assertEqual(json.loads(test_json), json.loads(self.test_json))

    def test_java_compiles(self):
        print(self.java_source)
        subprocess.check_output([JAVAC_BINARY_PATH, self.java_file_name])

    def test_go_compiles(self):
        print(self.go_source)
        subprocess.check_output([GO_BINARY_PATH, 'tool', 'compile', self.go_file_name])

    def test_go_main_runs(self):
        subprocess.check_output([GO_BINARY_PATH, 'run', self.go_file_name])

    def test_c_compiles(self):
        print(self.c_source)
        subprocess.check_output([GCC_BINARY_PATH, self.c_file_name, '-o', self.c_executable_file_name])

    def test_c_main_runs(self):
        self.test_c_compiles()
        subprocess.check_output([self.c_executable_file_name])


class TestString(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "name": "Michael Phelps"
}
"""
    expected_classes = (class_name,)


class TestEmptyString(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "motto": ""
}
"""
    expected_classes = (class_name,)


class TestSignedPositiveNumber1Byte(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "age": 127
}
"""
    expected_classes = (class_name,)


class TestSignedPositiveNumber2Byte(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "age": 32767
}
"""
    expected_classes = (class_name,)


class TestSignedPositiveNumber4Byte(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "age": 2147483647
}
"""
    expected_classes = (class_name,)


class TestSignedPositiveNumber8Byte(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "age": 9223372036854775807
}
"""
    expected_classes = (class_name,)


class TestSignedNegativeNumber1Byte(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "age": -128
}
"""
    expected_classes = (class_name,)


class TestSignedNegativeNumber2Byte(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "age": -32768
}
"""
    expected_classes = (class_name,)


class TestSignedNegativeNumber4Byte(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "age": -2147483648
}
"""
    expected_classes = (class_name,)


class TestSignedNegativeNumber8Byte(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "age": -9223372036854775808
}
"""
    expected_classes = (class_name,)


class TestLargePositiveFloat(AbstractTestClass, TestCase):
    class_name = "Car"
    test_json = """\
{
    "Miles": 3.4e+38
}
"""
    expected_classes = (class_name,)


class TestLargePositiveDouble(AbstractTestClass, TestCase):
    class_name = "Car"
    test_json = """\
{
    "Miles": 1.7e+308
}
"""
    expected_classes = (class_name,)


# Python is going to treat anything greater than 1.7e+308 as infinity. Good luck.
class TestLargePositiveLongDouble(AbstractTestClass, TestCase):
    class_name = "Car"
    test_json = """\
{
    "Miles": 1.1e+4932
}
"""
    expected_classes = (class_name,)

class TestSmallPositiveFloat(AbstractTestClass, TestCase):
    class_name = "Car"
    test_json = """\
{
    "Miles": 1.2e-38
}
"""
    expected_classes = (class_name,)


class TestSmallPositiveDouble(AbstractTestClass, TestCase):
    class_name = "Car"
    test_json = """\
{
    "Miles": 2.3e-308
}
"""
    expected_classes = (class_name,)


class TestSmallPositiveLongDouble(AbstractTestClass, TestCase):
    class_name = "Car"
    test_json = """\
{
    "Miles": 3.4e-4932
}
"""
    expected_classes = (class_name,)


class TestLargeNegativeFloat(AbstractTestClass, TestCase):
    class_name = "Car"
    test_json = """\
{
    "Miles": -3.4e+38
}
"""
    expected_classes = (class_name,)


class TestLargeNegativeDouble(AbstractTestClass, TestCase):
    class_name = "Car"
    test_json = """\
{
    "Miles": -1.7e+308
}
"""
    expected_classes = (class_name,)


# Python is going to treat anything greater than 1.7e+308 as infinity. Good luck.
class TestLargeNegativeLongDouble(AbstractTestClass, TestCase):
    class_name = "Car"
    test_json = """\
{
    "Miles": -1.1e+4932
}
"""
    expected_classes = (class_name,)

class TestSmallNegativeFloat(AbstractTestClass, TestCase):
    class_name = "Car"
    test_json = """\
{
    "Miles": -1.2e-38
}
"""
    expected_classes = (class_name,)


class TestSmallNegativeDouble(AbstractTestClass, TestCase):
    class_name = "Car"
    test_json = """\
{
    "Miles": -2.3e-308
}
"""
    expected_classes = (class_name,)


class TestSmallNegativeLongDouble(AbstractTestClass, TestCase):
    class_name = "Car"
    test_json = """\
{
    "Miles": -3.4e-4932
}
"""
    expected_classes = (class_name,)



class TestUnsignedNumber1Byte(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "age": 255
}
"""
    expected_classes = (class_name,)


class TestUnsignedNumber2Byte(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "age": 65535
}
"""
    expected_classes = (class_name,)


class TestUnsignedNumber4Byte(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "age": 4294967295
}
"""
    expected_classes = (class_name,)


class TestUnsignedNumber8Byte(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "age": 18446744073709551615
}
"""
    expected_classes = (class_name,)


class TestZeroInteger(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "unique_thoughts": 0
}
"""
    expected_classes = (class_name,)


class TestZeroFloat(AbstractTestClass, TestCase):
    class_name = "Account"
    test_json = """\
{
    "balance": 0.0
}
"""
    expected_classes = (class_name,)


class TestBooleanTrue(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "happy": true
}
"""
    expected_classes = (class_name,)


class TestBooleanFalse(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "happy": false
}
"""
    expected_classes = (class_name,)


class TestNull(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "happy": null
}
"""
    expected_classes = (class_name,)


class TestStruct(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "programming_language": {"language": "python", "years_experience": 7}
}
"""
    expected_classes = (class_name, "ProgrammingLanguage")


class TestSignedPositiveInteger1ByteArrays(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "favorte_numbers": [1, 2, 3]
}
"""
    expected_classes = (class_name,)


class TestBooleanArrays(AbstractTestClass, TestCase):
    class_name = "UnitTest"
    test_json = """\
{
    "results": [false, true, true, true, false, true, true, false, false]
}
"""
    expected_classes = (class_name,)


class TestStringArrays(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "programming_languages": ["python", "rust"]
}
"""
    expected_classes = (class_name,)


class TestStructArrays(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "programming_languages": [
        {"language": "python", "years_experience": 7},
        {"language": "rust", "years_experience": 2}
    ]
}
"""
    expected_classes = (class_name, 'ProgrammingLanguage')


class Test2dSignedPositiveInteger1ByteArrays(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "favorte_number_lists": [[1, 2, 3], [9, 22]]
}
"""
    expected_classes = (class_name,)


class Test3dSignedPositiveInteger1ByteArrays(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
{
    "favorte_number_lists_lists": [[[1, 2, 3], [9, 22]], [[1, 7], [22]]]
}
"""
    expected_classes = (class_name,)


class TestMultiTypeArray(AbstractTestClass, TestCase):
    class_name = "Person"
    test_json = """\
    {
        "favorite_words_and_numbers": ["cake", 17, "hotdogs", "42"]
    }
    """
    expected_classes = (class_name,)


class TestEmpty(AbstractTestClass, TestCase):
    class_name = "Empty"
    test_json = "{}"
    expected_classes = (class_name,)


class TestEmptyArray(AbstractTestClass, TestCase):
    class_name = "EmptyList"
    test_json = """\
    {
        "stuff": []
    }
    """
    expected_classes = (class_name,)

class TestTopLevelPositiveInteger1ByteArray(AbstractTestClass, TestCase):
    class_name = "EmptyList"
    test_json = """\
    { 1, 2, 3, 4, 5 }
    """
    expected_classes = (class_name,)
