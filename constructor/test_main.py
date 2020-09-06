import sys
import json
from importlib.util import spec_from_loader, module_from_spec
from unittest import TestCase

from constructor.main import MetaClass

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
        self.simple_meta_class = MetaClass.from_json("Simple", self.test_json)

    def test_python_compiles(self):
        source = self.simple_meta_class.generate_python()
        compile(source, "simple.py", 'exec')

    def test_python_has_expected_classes(self):
        source = self.simple_meta_class.generate_python()
        compiled = compile(source, "simple.py", 'exec')
        for expected_class in SIMPLE_TEST_JSON_EXPECTED_CLASSES:
            assert expected_class in compiled.co_names, f"Output is missing the {expected_class} class"

    def test_python_to_json_output_matches_original_structure(self):
        # Setup. TODO: Abstract this
        source = self.simple_meta_class.generate_python()
        module_name = 'test_module'
        spec = spec_from_loader(module_name, loader=None)
        module = module_from_spec(spec)
        exec(source, module.__dict__)
        sys.modules[module_name] = module

        # Actual test
        print(source)
        simple = module.Simple.from_json(self.test_json)
        test_json = simple.to_json()
        assert json.loads(test_json) == json.loads(self.test_json)

        # Teardown. TODO: Abstract this
        del sys.modules[module_name]
