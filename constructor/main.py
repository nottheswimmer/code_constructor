import json
import autopep8
from typing import Dict, List, Union, Set, Tuple

from constructor.field_types import Type, Array, Object
from constructor.utils import any_to_upper_camel, any_to_lower_camel, camel_to_lower_snake, indent, primitive_to_type, \
    add_suffix_to_reserved_python_words

from inflection import pluralize, singularize

PRINTED_SIGNATURES: Dict[str, Set[str]] = {}


class MetaClass:
    def __init__(self, name: str, fields: Dict[str, Type]):
        if not name:
            name += 'ClassName'  # TODO: Raise an error

        # For JSON tags in Go and maybe importing/exporting from/to JSON later
        self.original_name = name

        # Normalize class name as UpperCamel
        self.name = any_to_upper_camel(name)

        # TODO: Maybe change them to English? e.g. "1" -> "One"
        # If it starts with a number, fix that
        if self.name[0].isdigit():
            self.name = 'Item' + self.name

        # Normalize field name as lowerCamel
        self.fields = {any_to_lower_camel(field): t for field, t in fields.items()}

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Union[str, bool, int, list]], skip_fields_with_errors=False):
        # TODO: Support for None
        fields = {}
        for key, value in data.items():

            try:
                fields[key] = primitive_to_type(value, field_name=key)
            except Exception:
                if not skip_fields_with_errors:
                    raise
                # TODO: Warnings instead

        return cls(name=name, fields=fields)

    @classmethod
    def from_json(cls, name: str, data: str, skip_fields_with_errors=False):
        data = json.loads(data)
        # TODO: More useful support for lists
        # TODO: Bubble up a warning that we ignored everything except the first nonlist item
        if isinstance(data, list):
            if len(data) == 0:
                raise NotImplementedError("Top-level array cannot be an empty list")
            items_name = pluralize(name)
            if singularize(items_name) == name:
                items_name = "items"
            return cls.from_dict(name, {items_name: data}, skip_fields_with_errors)
        return cls.from_dict(name, data, skip_fields_with_errors)

    @property
    def python_name(self) -> str:
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

    def get_python_fields(self) -> Dict[str, Type]:
        return {add_suffix_to_reserved_python_words(camel_to_lower_snake(field), "_field"): t for field, t in
                self.fields.items()}

    def get_java_fields(self) -> Dict[str, Type]:
        return {field: t for field, t in self.fields.items()}

    def get_go_fields(self) -> Dict[str, Type]:
        return {any_to_upper_camel(field): t for field, t in self.fields.items()}

    def get_c_fields(self) -> Dict[str, Type]:
        return {camel_to_lower_snake(field): t for field, t in self.fields.items()}

    def get_c_includes(self) -> List[str]:
        includes = set()
        for field_type in self.fields.values():
            includes.update(field_type.c_includes)
        return sorted(includes)

    def get_python_imports(self) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, Set[str]]]:
        i_standard = {}
        i_third_party = {}
        i_local = {}
        for field_type in self.fields.values():
            i_standard.update(field_type.python_imports[0])
            i_third_party.update(field_type.python_imports[1])
            i_local.update(field_type.python_imports[2])
        return i_standard, i_third_party, i_local

    def get_java_imports(self) -> List[str]:
        imports = set()
        for field_type in self.fields.values():
            imports.update(field_type.java_imports)
        return sorted(imports)

    def get_name_and_field_signature(self) -> str:
        """
        Return an arbitrary string unique to the name and fields of this class
        """
        return self.name + '@@@' + str(sorted(self.get_java_fields()))

    def generate_python(self) -> str:
        top_level = 'python' not in PRINTED_SIGNATURES
        if top_level:
            PRINTED_SIGNATURES['python'] = {self.get_name_and_field_signature()}
        elif self.get_name_and_field_signature() in PRINTED_SIGNATURES['python']:
            return ''
        else:
            PRINTED_SIGNATURES['python'].add(self.get_name_and_field_signature())

        lines = []
        if top_level:
            lines += self.generate_python_import_lines()
        lines += self.generate_python_related_classes_lines()
        lines += self.generate_python_class_lines()

        # Code example
        if top_level:
            lines += self.generate_python_main_function_lines()

        if top_level:
            del PRINTED_SIGNATURES['python']
        return '\n'.join(lines)

    def generate_python_class_lines(self):
        class_lines = [f"class {self.python_name}"]
        class_lines += self.generate_python_constructor_lines()
        class_lines += self.generate_python_from_dict_classmethod_lines()
        class_lines += self.generate_python_from_json_classmethod_lines()
        class_lines += self.generate_python_to_dict_method_lines()
        class_lines += self.generate_python_to_json_method_lines()
        class_lines += self.generate_python_repr_method_lines()
        return class_lines

    def generate_python_repr_method_lines(self):
        repr_lines = ['']
        repr_lines.append(indent(1) + "def __repr__(self):")
        fields = self.get_python_fields()
        if fields:
            repr_lines.append(indent(2) + f"return f\"{self.python_name}(\" \\")
            for field, t in fields.items():
                # 7 is the number of spaces in "return "
                repr_lines.append(indent(1) + " " * 7 + f"f\"{field}={{self.{field}!r}}, \" \\")
            repr_lines[-1] = repr_lines[-1].rstrip(", \" \\") + ")\""
        else:
            repr_lines.append(indent(2) + f"return f\"{self.python_name}()\"")
        return repr_lines

    def generate_python_to_json_method_lines(self):
        to_json_lines = ['']
        to_json_lines.append(indent(1) + "def to_json(self) -> str:")
        to_json_lines.append(indent(2) + "return json.dumps(self.to_dict())")
        return to_json_lines

    def generate_python_to_dict_method_lines(self):
        to_dict_lines = ['']
        to_dict_lines.append(indent(1) + "def to_dict(self) -> dict:")
        fields = self.get_python_fields()
        if fields:
            first_item_prefix = indent(2) + "return {"
            other_item_prefix = indent(2) + "        "
            for field, t in fields.items():
                k, v = t.to_python_to_dict_pair(field)
                to_dict_lines.append(f"{first_item_prefix or other_item_prefix}{k!r}: {v}, ")
                first_item_prefix = ""
            to_dict_lines[-1] = to_dict_lines[-1].rstrip(", ") + "}"
        else:
            to_dict_lines.append(indent(2) + "return {}")
        return to_dict_lines

    def generate_python_from_json_classmethod_lines(self):
        from_json_lines = ['']
        from_json_lines.append(indent(1) + '@classmethod')
        from_json_lines.append(indent(1) + "def from_json(cls, data: str):")
        from_json_lines.append(indent(2) + "return cls.from_dict(json.loads(data))")
        return from_json_lines

    def generate_python_from_dict_classmethod_lines(self):
        from_dict_lines = ['']
        from_dict_lines.append(indent(1) + '@classmethod')
        from_dict_lines.append(indent(1) + "def from_dict(cls, d: dict):")
        string_body = indent(2) + f"return cls("
        fields = self.get_python_fields()
        if fields:
            for field, t in fields.items():
                string_body += f"{field}=d[{t.original_name!r}], "
        string_body = string_body.rstrip(", ") + ")"
        from_dict_lines.append(string_body)
        return from_dict_lines

    def generate_python_constructor_lines(self):
        constructor_lines = [indent(1) + "def __init__(self, "]
        fields = self.get_python_fields()
        if fields:
            for field, t in fields.items():
                constructor_lines[0] += f"{field}: {t.to_python}, "
                constructor_lines.append(indent(2) + f"self.{field} = {field}")
        else:
            constructor_lines.append(indent(2) + "pass")
        # Remove trailing ", " and close signature / open body
        constructor_lines[0] = constructor_lines[0].rstrip(', ') + "):"
        return constructor_lines

    def generate_python_main_function_lines(self):
        main_function_lines = []
        main_function_lines.append('')
        main_function_lines.append('def main():')
        for line in self.generate_python_example_lines():
            main_function_lines.append(indent(1) + line)
        main_function_lines.append('')
        main_function_lines.append("""if __name__ == '__main__':""")
        main_function_lines.append(indent(1) + "main()")
        return main_function_lines

    def generate_python_related_classes_lines(self) -> List[str]:
        related_object_definitions = []
        for field, t in self.get_c_fields().items():
            for field_type in t.embedded_objects:
                object_string = field_type.object_class.generate_python()
                if object_string:
                    related_object_definitions.append(object_string)
                    related_object_definitions.append('')
        return related_object_definitions

    def generate_python_import_lines(self) -> List[str]:
        import_lines = ['import json']  # serialization and deserialization to JSON seems really useful
        for import_group in self.get_python_imports():
            if not import_group:
                continue
            for key, values in import_group.items():
                if not values:
                    continue

                line = f'from {key} import '
                for value in values:
                    line += value + ', '
                line = line[:-2]
                import_lines.append(line)
            import_lines.append('')
        return import_lines

    def to_python_construction(self) -> str:
        line = f"{self.python_name}("
        for field, t in self.get_python_fields().items():
            line += f"{field}={t.to_python_value}, "
        line = line.rstrip(", ") + ")"
        return line

    def generate_python_example_lines(self) -> List[str]:
        test_var_name = add_suffix_to_reserved_python_words(camel_to_lower_snake(self.name), "_object")
        lines = [f"{test_var_name} = {self.to_python_construction()}", f"print({test_var_name})"]
        return lines

    def to_java_construction(self) -> str:
        line = f"new {self.java_name}("
        for field, t in self.get_java_fields().items():
            line += f"{t.to_java_value}, "
        line = line.rstrip(", ") + ")"
        return line

    def to_java_example(self) -> str:
        # TODO: Avoid Java keywords and shadowing Java builtins
        test_var_name = any_to_lower_camel(self.name)
        lines = [f"{self.java_name} {test_var_name} = {self.to_java_construction()};",
                 f"System.out.println({test_var_name});"]
        return '\n'.join(lines)

    def to_java(self) -> str:
        top_level = 'java' not in PRINTED_SIGNATURES
        if top_level:
            PRINTED_SIGNATURES['java'] = {self.get_name_and_field_signature()}
        elif self.get_name_and_field_signature() in PRINTED_SIGNATURES['java']:
            return ''
        else:
            PRINTED_SIGNATURES['java'].add(self.get_name_and_field_signature())

        lines = []
        if top_level:
            for java_import in self.get_java_imports():
                lines.append(f"import {java_import};")
            # Add another line if there were imports needed
            if lines:
                lines.append('')

        lines.append(f"{'public ' if top_level else ''}class {self.java_name} {{")  # TODO: Scope
        field_lines = []
        for field, t in self.get_java_fields().items():
            field_lines.append(indent(1) + f"private {t.to_java} {field};")
        lines += field_lines
        lines.append('')

        # No constructor is needed if we have no fields
        # Also no getters or setters would be needed
        field_items = self.get_java_fields().items()
        if field_items:
            # Build constructor
            constructor = indent(1) + f"public {self.java_name}("
            constructor_lines = []
            for field, t in field_items:
                constructor += f"{t.to_java} {field}, "
                constructor_lines.append(indent(2) + f"this.{field} = {field};")
            # Remove trailing ", " and close signature / open body
            constructor = constructor[:-2] + ") {"
            lines.append(constructor)
            lines += constructor_lines

            # Add closing curly
            lines.append(indent(1) + "}")
            lines.append('')

            # Add getters and setters
            for field, t in field_items:
                getter_lines = [
                    indent(1) + f"public {t.to_java} get{field[0].upper()}{field[1:]}() {{",
                    indent(2) + f'return this.{field};',
                    indent(1) + '}',
                    ''
                ]
                lines += getter_lines

                setter_lines = [
                    indent(1) + f"public void set{field[0].upper()}{field[1:]}({t.to_java} {field}) {{",
                    indent(2) + f'this.{field} = {field};',
                    indent(1) + '}',
                    ''
                ]

                lines += setter_lines

        # Add toString method
        lines.append(indent(1) + "public String toString() {")
        string_body = indent(2) + f'return "{self.java_name}('
        if field_items:
            for field, t in field_items:
                if isinstance(t, Array):
                    string_body += f'{field}=" + Arrays.toString(this.{field}) + ", '
                else:
                    string_body += f'{field}=" + this.{field} + ", '
            string_body = string_body.rstrip(', ')
        string_body += ')";'
        lines.append(string_body)
        # Add closing curly
        lines.append(indent(1) + "}")
        lines.append('')

        # For java, let's go ahead and add a main method with an example in the top-level course
        if top_level:
            lines.append(indent(1) + "public static void main(String[] args) {")
            for line in self.to_java_example().splitlines():
                lines.append(indent(2) + line)
            lines.append(indent(1) + "}")
            lines.append('')

        # Add final closing curly
        lines.append("}")

        for field, t in self.get_c_fields().items():
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
            PRINTED_SIGNATURES['go'] = {self.get_name_and_field_signature()}
        elif self.get_name_and_field_signature() in PRINTED_SIGNATURES['go']:
            return ''
        else:
            PRINTED_SIGNATURES['go'].add(self.get_name_and_field_signature())

        lines = []

        for field, t in self.get_go_fields().items():
            for field_type in t.embedded_objects:
                string = field_type.object_class.to_go()
                if string:
                    lines.append(string)
                    lines.append('')

        lines.append(f"type {self.go_name} struct {{")
        struct_lines = []
        for field, t in self.get_go_fields().items():
            struct_lines.append(indent(1) + f"{field} {t.to_go} `json:\"{t.original_name}\"`")  # TODO: Scope
        lines += struct_lines
        lines.append("}")
        lines.append('')

        constructor_signature = f"func New{self.go_name}("
        constructor_return = indent(1) + f"return &{self.go_name}{{"
        for field, t in self.get_go_fields().items():
            lower_field_name = any_to_lower_camel(field)
            constructor_signature += f"{lower_field_name} {t.to_go}, "
            constructor_return += f"{field}: {lower_field_name}, "
        constructor_signature = constructor_signature.rstrip(", ") + f") *{self.go_name} {{"
        constructor_return = constructor_return.rstrip(", ") + "}"
        lines.append(constructor_signature)
        lines.append(constructor_return)
        lines.append("}")

        if top_level:
            del PRINTED_SIGNATURES['go']
        return '\n'.join(lines)

    def to_c_construction(self) -> str:
        line = f"{self.c_name}_new("
        for field, t in self.get_c_fields().items():
            if isinstance(t, Object):
                line += "*"
            line += f"{t.to_c_value}, "
        line = line.rstrip(", ") + ")"
        return line

    def to_c_example(self) -> str:
        # TODO: Avoid Java keywords and shadowing C builtins
        test_var_name = any_to_lower_camel(self.name)
        lines = [f"{self.c_name} * {test_var_name} = {self.to_c_construction()};",
                 f"{self.c_name}_print({test_var_name});"]
        return '\n'.join(lines)

    def to_c(self) -> str:
        top_level = 'c' not in PRINTED_SIGNATURES
        if top_level:
            PRINTED_SIGNATURES['c'] = {self.get_name_and_field_signature()}
        elif self.get_name_and_field_signature() in PRINTED_SIGNATURES['c']:
            return ''
        else:
            PRINTED_SIGNATURES['c'].add(self.get_name_and_field_signature())

        lines = []
        if top_level:
            lines.append(f"#include <malloc.h>")  # Needed for any constructor
            lines.append(f"#include <stdio.h>")  # Needed for any print func
            for include in self.get_c_includes():
                lines.append(f"#include <{include}>")
            # Add another line if there were includes needed
            if lines:
                lines.append('')

        field_items = self.get_c_fields().items()
        for field, t in field_items:
            for field_type in t.embedded_objects:
                string = field_type.object_class.to_c()
                if string:
                    lines.append(string)
                    lines.append('')

        lines.append(f"struct {self.c_name} {{")
        for field, t in self.get_c_fields().items():
            lines.append(indent(1) + f"{t.to_c} {'* ' if t.c_is_variable_length_array else ''}{field};")
        lines.append("};")
        lines.append(f"typedef struct {self.c_name} {self.c_name};")
        lines.append('')

        # Constructor
        constructor_signature = f"{self.c_name}* {self.c_name}_new("
        for field, t in field_items:
            constructor_signature += f"{t.to_c} {field}{'[]' if t.c_is_variable_length_array else ''}, "
        constructor_signature = constructor_signature.rstrip(", ") + ") {"
        lines.append(constructor_signature)
        lines.append(indent(1) + f"{self.c_name}* p = malloc(sizeof({self.c_name}));")
        for field, t in field_items:
            lines.append(indent(1) + f"p->{field} = {field};")
        lines += [indent(1) + "return p;", '}']
        lines.append('')

        # Print method
        lines.append(f"void {self.c_name}_print({self.c_name}* p) {{")
        print_statements = [indent(1) + f"printf_s(\"{self.c_name}(\");"]
        for field, t in field_items:
            print_statements.append(indent(1) + t.to_c_printf(field))
            if print_statements[-1].count('",') == 1:
                print_statements[-1] = print_statements[-1].replace('",', ', ",')
            else:
                print_statements.append(indent(1) + 'printf_s(", ");')
        if field_items:
            if print_statements[-1] == indent(1) + 'printf_s(", ");':
                print_statements.pop()
            else:
                print_statements[-1] = print_statements[-1].replace(', ",', '",')
        print_statements.append(indent(1) + 'printf_s(")");')
        lines += print_statements
        lines += ["}", ""]

        # Example
        if top_level:
            example_lines = ["int main() {"]
            for line in self.to_c_example().splitlines():
                example_lines.append(indent(1) + line)
            example_lines += [indent(1) + "return 0;", '}']
            lines += example_lines

        if top_level:
            del PRINTED_SIGNATURES['c']
        return '\n'.join(lines)
