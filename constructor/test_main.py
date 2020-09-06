import os
import sys
import json
import subprocess
from importlib.util import spec_from_loader, module_from_spec
from unittest import TestCase

from constructor.main import MetaClass
from constructor.utils import cleanup

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
        self.meta_class = MetaClass.from_json(self.class_name, self.test_json)

    def tearDown(self):
        cleanup()  # TODO: This should NOT be necessary...

    def test_python_compiles(self):
        source = self.meta_class.generate_python()
        compile(source, "simple.py", 'exec')

    def test_python_has_expected_classes(self):
        source = self.meta_class.generate_python()
        compiled = compile(source, "simple.py", 'exec')
        for expected_class in SIMPLE_TEST_JSON_EXPECTED_CLASSES:
            self.assertIn(expected_class, compiled.co_names,
                          f"Output ({compiled.co_names}) is missing the {expected_class} class")

    def test_python_main_method_runs(self):
        # Setup. TODO: Abstract this
        module_name = 'test_module'
        try:
            source = self.meta_class.generate_python()
            spec = spec_from_loader(module_name, loader=None)
            module = module_from_spec(spec)
            exec(source, module.__dict__)
            sys.modules[module_name] = module

            # Actual test
            module.main()
        finally:
            # Teardown. TODO: Abstract this
            del sys.modules[module_name]

    def test_python_to_json_output_matches_original_structure(self):
        # Setup. TODO: Abstract this
        module_name = 'test_module'
        try:
            source = self.meta_class.generate_python()
            spec = spec_from_loader(module_name, loader=None)
            module = module_from_spec(spec)
            exec(source, module.__dict__)
            sys.modules[module_name] = module

            # Actual test
            simple = module.Simple.from_json(self.test_json)
            test_json = simple.to_json()
            self.assertEqual(json.loads(test_json), json.loads(self.test_json))
        finally:
            # Teardown. TODO: Abstract this
            del sys.modules[module_name]

    def test_java_compiles(self):
        # Setup. TODO: Abstract this
        javaname = f"{self.class_name}.java"
        javacname = f"{self.class_name}.javac"
        try:
            source = self.meta_class.generate_java()
            with open(javaname, "w") as f:
                f.write(source)

            # Actual test
            subprocess.check_output(['javac', javaname])
        finally:
            # Teardown. TODO: Abstract this
            for fp in (javaname, javacname):
                if os.path.exists(fp):
                    os.remove(fp)
