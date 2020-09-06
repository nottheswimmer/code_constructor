import os
import sys
import json
import subprocess
from importlib.util import spec_from_loader, module_from_spec
from unittest import TestCase

from constructor.main import MetaClass
from constructor.utils import cleanup

# TEST ENVIRONMENT CONFIGURATION
JAVAC_BINARY_PATH = 'javac'
GO_BINARY_PATH = 'go'
GOFMT_BINARY_PATH = 'gofmt'

# TEST VARIABLE CONSTANTS
SIMPLE_TEST_JSON = """\
{
    "researcher": {
        "name": "Ford Prefect",
        "species": "Betelgeusian",
        "relatives": [
            {
                "name": "Zaphod Beeblebrox",
                "species": "Betelgeusian"
            }
        ]
    }
}
"""
SIMPLE_TEST_JSON_EXPECTED_CLASSES = ("Simple", "Researcher", "Relative")


class TestMetaClassSimple(TestCase):
    def setUp(self) -> None:
        self.test_json = SIMPLE_TEST_JSON
        self.class_name = "Simple"
        self.expected_classes = SIMPLE_TEST_JSON_EXPECTED_CLASSES
        self.meta_class = MetaClass.from_json(self.class_name, self.test_json)

        # Python
        self.python_source = self.meta_class.generate_python()
        self.python_module_name = 'test_module'
        source = self.meta_class.generate_python()
        spec = spec_from_loader(self.python_module_name, loader=None)
        self.python_module = module_from_spec(spec)
        exec(source, self.python_module.__dict__)
        sys.modules[self.python_module_name] = self.python_module_name

        # Java
        self.java_source = self.meta_class.generate_java()
        self.java_file_name = f"{self.class_name}.java"
        self.java_class_file_names = []
        for classname in self.expected_classes:
            self.java_class_file_names.append(f"{classname}.class")
        with open(self.java_file_name, "w") as f:
            f.write(self.java_source)

        # Go
        self.go_source = self.meta_class.generate_go()
        self.go_file_name = f"{self.class_name}.go"
        self.go_object_file_name = f"{self.class_name}.o"
        with open(self.go_file_name, "w") as f:
            f.write(self.go_source)

    def tearDown(self):
        cleanup()  # TODO: This should NOT be necessary...

        # Python
        del sys.modules[self.python_module_name]

        # Java
        # TODO: Remove .class files unintentionally created as well?
        for fp in (self.java_file_name, *self.java_class_file_names):
            if os.path.exists(fp):
                os.remove(fp)

        # Go
        for fp in (self.go_file_name, self.go_object_file_name):
            if os.path.exists(fp):
                os.remove(fp)

    def test_python_compiles(self):
        source = self.meta_class.generate_python()
        compile(source, "simple.py", 'exec')

    def test_python_has_expected_classes(self):
        compiled = compile(self.python_source, "simple.py", 'exec')
        for expected_class in SIMPLE_TEST_JSON_EXPECTED_CLASSES:
            self.assertIn(expected_class, compiled.co_names,
                          f"Output ({compiled.co_names}) is missing the {expected_class} class")

    def test_python_main_method_runs(self):
        self.python_module.main()

    def test_python_to_json_output_matches_original_structure(self):
        simple = self.python_module.Simple.from_json(self.test_json)
        test_json = simple.to_json()
        self.assertEqual(json.loads(test_json), json.loads(self.test_json))

    def test_java_compiles(self):
        subprocess.check_output([JAVAC_BINARY_PATH, self.java_file_name])

    def test_go_compiles(self):
        print(self.go_source)
        subprocess.check_output([GO_BINARY_PATH, 'tool', 'compile', self.go_file_name])