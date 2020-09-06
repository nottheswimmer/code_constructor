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

    class Decorators:
        @classmethod
        def handle_visit(cls, language: str):
            def handle_visited_language(decorated):
                def wrapper(self: 'MetaClass'):
                    top_level, visited = self.handle_visit_start(language)
                    if visited:
                        result = ''
                    else:
                        result = decorated(self, top_level)
                        self.handle_visit_end(language, top_level)
                    return result

                return wrapper

            return handle_visited_language

    # Core methods for generating code
    @Decorators.handle_visit('python')
    def generate_python(self, top_level: bool) -> str:
        lines = []
        if top_level:
            lines += self.generate_python_import_lines()
        lines += self.generate_python_related_classes_lines()
        lines += self.generate_python_class_lines()
        if top_level:
            lines += self.generate_python_main_function_lines()
        return '\n'.join(lines)

    @Decorators.handle_visit('java')
    def generate_java(self, top_level: bool) -> str:
        lines = []
        if top_level:
            lines += self.generate_java_import_lines()
        class_scope = 'public' if top_level else ''
        generate_main_method = top_level
        lines += self.generate_java_class_lines(class_scope, generate_main_method)
        lines += self.generate_java_related_classes_lines()
        return '\n'.join(lines)

    @Decorators.handle_visit('go')
    def generate_go(self, top_level: bool) -> str:
        lines = []
        if top_level:
            lines.append(self.generate_go_package_line())
            lines.append('')
        lines += self.generate_go_related_structs_lines()
        lines += self.generate_go_struct_lines()
        lines += self.generate_go_constructor_lines()
        if top_level:
            lines += self.generate_go_main_function_lines()
        return '\n'.join(lines)

    @Decorators.handle_visit('c')
    def generate_c(self, top_level: bool) -> str:
        lines = []
        if top_level:
            lines += self.generate_c_import_lines()
        lines += self.generate_c_related_structs_lines()
        lines += self.generate_c_struct_lines()
        lines += self.generate_c_constructor_lines()
        lines += self.generate_c_struct_print_function()
        if top_level:
            lines += self.generate_c_example_code_lines()
        return '\n'.join(lines)

    # Supplemental methods and functions to make generating code easier
    def handle_visit_start(self, language: str) -> Tuple[bool, bool]:
        visited = False
        top_level = language not in PRINTED_SIGNATURES
        if top_level:
            PRINTED_SIGNATURES[language] = {self.get_name_and_field_signature()}
        elif self.get_name_and_field_signature() in PRINTED_SIGNATURES[language]:
            visited = True
        else:
            PRINTED_SIGNATURES[language].add(self.get_name_and_field_signature())
        return top_level, visited

    def handle_visit_end(self, language, top_level):
        if top_level:
            del PRINTED_SIGNATURES[language]

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

    def get_python_imports(self) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, Set[str]]]:
        i_standard = {}
        i_third_party = {}
        i_local = {}
        for field_type in self.fields.values():
            i_standard.update(field_type.python_imports[0])
            i_third_party.update(field_type.python_imports[1])
            i_local.update(field_type.python_imports[2])
        return i_standard, i_third_party, i_local

    def get_java_fields(self) -> Dict[str, Type]:
        return {field: t for field, t in self.fields.items()}

    def get_java_imports(self) -> List[str]:
        imports = set()
        for field_type in self.fields.values():
            imports.update(field_type.java_imports)
        return sorted(imports)

    def get_go_fields(self) -> Dict[str, Type]:
        return {any_to_upper_camel(field): t for field, t in self.fields.items()}

    def get_c_fields(self) -> Dict[str, Type]:
        return {camel_to_lower_snake(field): t for field, t in self.fields.items()}

    def get_c_includes(self) -> List[str]:
        includes = set()
        for field_type in self.fields.values():
            includes.update(field_type.c_includes)
        return sorted(includes)

    def get_name_and_field_signature(self) -> str:
        """
        Return an arbitrary string unique to the name and fields of this class
        """
        return self.name + '@@@' + str(sorted(self.get_java_fields()))

    # Methods to generate code called by core code generation methods
    def generate_python_class_lines(self) -> List[str]:
        class_lines = [f"class {self.python_name}:"]
        class_lines += self.generate_python_constructor_lines()
        class_lines += self.generate_python_from_dict_classmethod_lines()
        class_lines += self.generate_python_from_json_classmethod_lines()
        class_lines += self.generate_python_to_dict_method_lines()
        class_lines += self.generate_python_to_json_method_lines()
        class_lines += self.generate_python_repr_method_lines()
        return class_lines

    def generate_python_repr_method_lines(self) -> List[str]:
        repr_lines = ['',
                      indent(1) + "def __repr__(self):"]
        if self.fields:
            repr_lines.append(indent(2) + f"return f\"{self.python_name}(\" \\")
            for field, t in self.get_python_fields().items():
                # 7 is the number of spaces in "return "
                repr_lines.append(indent(1) + " " * 7 + f"f\"{field}={{self.{field}!r}}, \" \\")
            repr_lines[-1] = repr_lines[-1].rstrip(", \" \\") + ")\""
        else:
            repr_lines.append(indent(2) + f"return f\"{self.python_name}()\"")
        return repr_lines

    def generate_python_to_json_method_lines(self) -> List[str]:
        to_json_lines = ['', indent(1) +
                         "def to_json(self) -> str:", indent(2) +
                         "return json.dumps(self.to_dict())"]
        return to_json_lines

    def generate_python_to_dict_method_lines(self) -> List[str]:
        to_dict_lines = ['',
                         indent(1) + "def to_dict(self) -> dict:"]
        if self.fields:
            first_item_prefix = indent(2) + "return {"
            other_item_prefix = indent(2) + "        "
            for field, t in self.get_python_fields().items():
                k, v = t.to_python_to_dict_pair(field)
                to_dict_lines.append(f"{first_item_prefix or other_item_prefix}{k!r}: {v}, ")
                first_item_prefix = ""
            to_dict_lines[-1] = to_dict_lines[-1].rstrip(", ") + "}"
        else:
            to_dict_lines.append(indent(2) + "return {}")
        return to_dict_lines

    def generate_python_from_json_classmethod_lines(self) -> List[str]:
        from_json_lines = ['',
                           indent(1) + '@classmethod',
                           indent(1) + "def from_json(cls, data: str):",
                           indent(2) + "return cls.from_dict(json.loads(data))"]
        return from_json_lines

    def generate_python_from_dict_classmethod_lines(self) -> List[str]:
        from_dict_lines = ['', indent(1) + '@classmethod',
                           indent(1) + "def from_dict(cls, d: dict):"]
        string_body = indent(2) + f"return cls("
        if self.fields:
            for field, t in self.get_python_fields().items():
                string_body += f"{field}={t.to_python_from_dict_value()}, "
        string_body = string_body.rstrip(", ") + ")"
        from_dict_lines.append(string_body)
        return from_dict_lines

    def generate_python_constructor_lines(self) -> List[str]:
        constructor_lines = [indent(1) + "def __init__(self, "]
        if self.fields:
            for field, t in self.get_python_fields().items():
                constructor_lines[0] += f"{field}: {t.to_python}, "
                constructor_lines.append(indent(2) + f"self.{field} = {field}")
        else:
            constructor_lines.append(indent(2) + "pass")
        # Remove trailing ", " and close signature / open body
        constructor_lines[0] = constructor_lines[0].rstrip(', ') + "):"
        return constructor_lines

    def generate_python_main_function_lines(self) -> List[str]:
        main_function_lines = ['',
                               'def main():']
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
        import_lines = ['import json']
        for import_group in self.get_python_imports():
            if not import_group:
                continue
            for key, values in import_group.items():
                if not values:
                    continue
                import_lines.append(self.generate_python_import_line(key, sorted(values)))
            import_lines.append('')
        return import_lines

    def generate_python_import_line(self, key: str, values: List[str]) -> str:
        import_line = f'from {key} import '
        for value in values:
            import_line += value + ', '
        import_line = import_line[:-2]
        return import_line

    def generate_python_object(self) -> str:
        line = f"{self.python_name}("
        for field, t in self.get_python_fields().items():
            line += f"{field}={t.to_python_value}, "
        line = line.rstrip(", ") + ")"
        return line

    def generate_python_example_lines(self) -> List[str]:
        example_var_name = add_suffix_to_reserved_python_words(camel_to_lower_snake(self.name), "_object")
        lines = [f"{example_var_name} = {self.generate_python_object()}", f"print({example_var_name})"]
        return lines

    def generate_java_object(self) -> str:
        line = f"new {self.java_name}("
        for field, t in self.get_java_fields().items():
            line += f"{t.to_java_value}, "
        line = line.rstrip(", ") + ")"
        return line

    def generate_java_example_lines(self) -> List[str]:
        # TODO: Avoid Java keywords and shadowing Java builtins
        test_var_name = any_to_lower_camel(self.name)
        lines = [f"{self.java_name} {test_var_name} = {self.generate_java_object()};",
                 f"System.out.println({test_var_name});"]
        return lines

    def generate_java_related_classes_lines(self) -> List[str]:
        lines = []
        for field, t in self.get_c_fields().items():
            for field_type in t.embedded_objects:
                string = field_type.object_class.generate_java()
                if string:
                    lines.append('')
                    lines.append(string)
        return lines

    def generate_java_class_lines(self, class_scope, generate_main_method) -> List[str]:
        lines = [f"{class_scope + ' ' if class_scope else ''}class {self.java_name} {{"]
        lines += self.generate_java_field_lines()
        lines.append('')
        if self.fields:
            lines += self.generate_java_constructor_lines()
            lines.append('')
            lines += self.generate_java_getter_and_setter_lines()
        lines += self.generate_java_to_string_method_lines()
        if generate_main_method:
            lines += self.generate_java_main_method_lines()
        lines.append("}")
        return lines

    def generate_java_main_method_lines(self) -> List[str]:
        lines = [indent(1) + "public static void main(String[] args) {"]
        for line in self.generate_java_example_lines():
            lines.append(indent(2) + line)
        lines.append(indent(1) + "}")
        lines.append('')
        return lines

    def generate_java_to_string_method_lines(self) -> List[str]:
        lines = [indent(1) + "public String toString() {"]
        string_body = indent(2) + f'return "{self.java_name}('
        if self.fields:
            for field, t in self.get_java_fields().items():
                if isinstance(t, Array):
                    string_body += f'{field}=" + Arrays.toString(this.{field}) + ", '
                else:
                    string_body += f'{field}=" + this.{field} + ", '
            string_body = string_body.rstrip(', ')
        string_body += ')";'
        lines.append(string_body)
        lines.append(indent(1) + "}")
        lines.append('')
        return lines

    def generate_java_constructor_lines(self) -> List[str]:
        constructor_lines = [indent(1) + f"public {self.java_name}("]
        for field, t in self.get_java_fields().items():
            constructor_lines[0] += f"{t.to_java} {field}, "
            constructor_lines.append(indent(2) + f"this.{field} = {field};")
        # Remove trailing ", " and close signature / open body
        constructor_lines[0] = constructor_lines[0][:-2] + ") {"
        constructor_lines.append(indent(1) + "}")
        return constructor_lines

    def generate_java_field_lines(self) -> List[str]:
        field_lines = []
        for field, t in self.get_java_fields().items():
            field_lines.append(indent(1) + f"private {t.to_java} {field};")
        return field_lines

    def generate_java_getter_and_setter_lines(self) -> List[str]:
        getter_and_settter_lines = []
        for field, t in self.get_java_fields().items():
            getter_and_settter_lines += self.generate_java_getter_lines(field, t)
            getter_and_settter_lines += self.generate_java_setter_lines(field, t)
        return getter_and_settter_lines

    def generate_java_setter_lines(self, field: str, t: Type) -> List[str]:
        setter_lines = [
            indent(1) + f"public void set{field[0].upper()}{field[1:]}({t.to_java} {field}) {{",
            indent(2) + f'this.{field} = {field};',
            indent(1) + '}',
            ''
        ]
        return setter_lines

    def generate_java_getter_lines(self, field: str, t: Type) -> List[str]:
        getter_lines = [
            indent(1) + f"public {t.to_java} get{field[0].upper()}{field[1:]}() {{",
            indent(2) + f'return this.{field};',
            indent(1) + '}',
            ''
        ]
        return getter_lines

    def generate_java_import_lines(self) -> List[str]:
        lines = []
        for java_import in self.get_java_imports():
            lines.append(f"import {java_import};")
        # Add another line if there were imports needed
        if lines:
            lines.append('')
        return lines

    def generate_go_constructor_lines(self) -> List[str]:
        lines = []
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
        return lines

    def generate_go_struct_lines(self) -> List[str]:
        lines = []
        lines.append(f"type {self.go_name} struct {{")
        struct_lines = []
        for field, t in self.get_go_fields().items():
            struct_lines.append(indent(1) + f"{field} {t.to_go} `json:\"{t.original_name}\"`")  # TODO: Scope
        lines += struct_lines
        lines.append("}")
        lines.append('')
        return lines

    def generate_go_related_structs_lines(self) -> List[str]:
        lines = []
        for field, t in self.get_go_fields().items():
            for field_type in t.embedded_objects:
                string = field_type.object_class.generate_go()
                if string:
                    lines.append(string)
                    lines.append('')
        return lines

    def generate_c_object(self) -> str:
        line = f"{self.c_name}_new("
        for field, t in self.get_c_fields().items():
            if isinstance(t, Object):
                line += "*"
            line += f"{t.to_c_value}, "
        line = line.rstrip(", ") + ")"
        return line

    def generate_c_example_lines(self) -> List[str]:
        # TODO: Avoid Java keywords and shadowing C builtins
        test_var_name = any_to_lower_camel(self.name)
        lines = [f"{self.c_name} * {test_var_name} = {self.generate_c_object()};",
                 f"{self.c_name}_print({test_var_name});"]
        return lines

    def generate_c_example_code_lines(self) -> List[str]:
        lines = []
        example_lines = ["int main() {"]
        for line in self.generate_c_example_lines():
            example_lines.append(indent(1) + line)
        example_lines += [indent(1) + "return 0;", '}']
        lines += example_lines
        return lines

    def generate_c_struct_print_function(self) -> List[str]:
        lines = [f"void {self.c_name}_print({self.c_name}* p) {{"]
        print_statements = [indent(1) + f"printf_s(\"{self.c_name}(\");"]
        for field, t in self.get_c_fields().items():
            print_statements.append(indent(1) + t.to_c_printf(field))
            if print_statements[-1].count('",') == 1:
                print_statements[-1] = print_statements[-1].replace('",', ', ",')
            else:
                print_statements.append(indent(1) + 'printf_s(", ");')
        if self.fields:
            if print_statements[-1] == indent(1) + 'printf_s(", ");':
                print_statements.pop()
            else:
                print_statements[-1] = print_statements[-1].replace(', ",', '",')
        print_statements.append(indent(1) + 'printf_s(")");')
        lines += print_statements
        lines += ["}", ""]
        return lines

    def generate_c_constructor_lines(self) -> List[str]:
        lines = []
        constructor_signature = f"{self.c_name}* {self.c_name}_new("
        for field, t in self.get_c_fields().items():
            constructor_signature += f"{t.to_c} {field}{'[]' if t.c_is_variable_length_array else ''}, "
        constructor_signature = constructor_signature.rstrip(", ") + ") {"
        lines.append(constructor_signature)
        lines.append(indent(1) + f"{self.c_name}* p = malloc(sizeof({self.c_name}));")
        for field, t in self.get_c_fields().items():
            lines.append(indent(1) + f"p->{field} = {field};")
        lines += [indent(1) + "return p;", '}']
        lines.append('')
        return lines

    def generate_c_struct_lines(self) -> List[str]:
        lines = [f"struct {self.c_name} {{"]
        for field, t in self.get_c_fields().items():
            lines.append(indent(1) + f"{t.to_c} {'* ' if t.c_is_variable_length_array else ''}{field};")
        lines.append("};")
        lines.append(f"typedef struct {self.c_name} {self.c_name};")
        lines.append('')
        return lines

    def generate_c_related_structs_lines(self) -> List[str]:
        lines = []
        for field, t in self.get_c_fields().items():
            for field_type in t.embedded_objects:
                string = field_type.object_class.generate_c()
                if string:
                    lines.append(string)
                    lines.append('')
        return lines

    def generate_c_import_lines(self) -> List[str]:
        lines = []
        lines.append(f"#include <malloc.h>")  # Needed for any constructor
        lines.append(f"#include <stdio.h>")  # Needed for any print func
        for include in self.get_c_includes():
            lines.append(f"#include <{include}>")
        # Add another line if there were includes needed
        if lines:
            lines.append('')
        return lines

    def generate_go_main_function_lines(self):
        lines = ["func main() { }"]  # TODO: A simple usage example
        return lines

    def generate_go_package_line(self):
        return "package main"

