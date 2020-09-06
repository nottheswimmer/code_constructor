import os
import sys
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

class TestMetaClass(TestCase):
    def test_generate_python_simple(self):
        simple_meta_class = MetaClass.from_json("Simple", SIMPLE_TEST_JSON)
        source = simple_meta_class.generate_python()
        simple = compile(source, "simple.py", 'exec')
        for expected_class in SIMPLE_TEST_JSON_EXPECTED_CLASSES:
            assert expected_class in simple.co_names, f"Output is missing the {expected_class} class"
