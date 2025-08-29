import sys
from dataclasses import dataclass
from datetime import datetime
from itertools import chain
from pathlib import Path
from typing import Iterator

TAB = "    "


@dataclass()
class TypeDefinition:
    """Type definition of Expr subclasses."""

    name: str
    attributes: list[tuple[str, str]]


class GenerateAst:
    """Generate AST."""

    @staticmethod
    def main(args: list) -> None:
        if len(args) != 1:
            print("Usage: generate_ast <output directory>", file=sys.stderr)
            sys.exit(64)

        output_dir: Path = Path(args[0])
        GenerateAst.__define_ast(
            output_dir,
            "Expr",
            [
                "Ternary  : condition Expr, consequent Expr, alternative Expr",
                "Binary   : left Expr, operator Token, right Expr",
                "Grouping : expression Expr",
                "Literal  : value object",
                "Unary    : operator Token, right Expr",
            ],
        )

    @staticmethod
    def __define_ast(output_dir: Path, base_name: str, types: list[str]) -> None:
        """Generate AST classes from type definitions."""
        output_dir.mkdir(
            parents=True,  # Create any missing parent dirs.
            exist_ok=True,  # Don't error if dir exists.
        )
        path: Path = output_dir / f"{base_name.lower()}.py"
        type_definitions: list[TypeDefinition] = (
            GenerateAst.__generate_type_definitions(types)
        )
        body: Iterator[str] = map(
            lambda line: line + "\n",
            [
                *GenerateAst.__generate_documentation(),
                *GenerateAst.__generate_imports(),
                *GenerateAst.__generate_visitor(base_name, type_definitions),
                *GenerateAst.__generate_base_class(base_name),
                *GenerateAst.__generate_child_classes(base_name, type_definitions),
            ],
        )

        with open(path, "w", encoding="utf-8") as writer:
            writer.writelines(body)

    @staticmethod
    def __generate_type_definitions(types: list[str]) -> list[TypeDefinition]:
        """Generate type definitions."""
        type_definitions: list[TypeDefinition] = []
        for type_spec in types:
            if ":" not in type_spec:
                print(f"Failed to generate type definition. Missing colon: {type_spec}")
                sys.exit(64)

            name_part, attrs_part = type_spec.split(":", 1)
            name: str = name_part.strip()

            attributes: list[tuple[str, str]] = []
            if not attrs_part.strip():
                print(
                    f"Failed to generate type definition. Missing attributes: {type_spec}"
                )
                sys.exit(64)
            else:
                attr_strings: list[str] = [
                    attr.strip() for attr in attrs_part.split(",")
                ]
                for attr_str in attr_strings:
                    attr_parts: list[str] = attr_str.split()

                    if len(attr_parts) != 2:
                        print(
                            f"Unable to generate type definition. Incomplete attribute: {attr_str}"
                        )
                        sys.exit(64)

                    attr_name, attr_type = attr_parts
                    attributes.append((attr_name, attr_type))

            type_definitions.append(TypeDefinition(name=name, attributes=attributes))

        return type_definitions

    @staticmethod
    def __generate_documentation() -> list[str]:
        """Generate documentation."""
        return [
            f"# Generated from GenerateAst class ({datetime.now()}).",
            "",
        ]

    @staticmethod
    def __generate_imports() -> list[str]:
        """Generate imports."""
        return [
            "from __future__ import annotations",
            "",
            "from abc import ABC, abstractmethod",
            "from dataclasses import dataclass",
            "from typing import Generic, TypeVar",
            "",
            "from lox.token import Token",
            "",
        ]

    @staticmethod
    def __generate_visitor(
        base_name: str, type_definitions: list[TypeDefinition]
    ) -> list[str]:
        """Generate Visitor interface."""
        generic = ['R = TypeVar("R")', "", ""]
        signature = ["class Visitor(ABC, Generic[R]):"]
        abstract_visit_methods = list(
            chain.from_iterable(
                [
                    f"{TAB}@abstractmethod",
                    f"{TAB}def visit_{type_definition.name.lower()}_{base_name.lower()}(self, {type_definition.name.lower()}: {type_definition.name}) -> R:",
                    f"{TAB}{TAB}pass",
                    "",
                ]
                for type_definition in type_definitions
            )
        )
        spacing = [""]

        # Iter 1 of abstract_visit_methods with nested loop:
        # abstract_visit_methods = [
        #     line
        #     for abstract_visit_method in [
        #         [
        #             f"{TAB}@abstractmethod",
        #             f"{TAB}def visit_{type_definition.name.lower()}_{base_name.lower()}(self, {type_definition.name.lower()}: {type_definition.name}) -> R:",
        #             f"{TAB}{TAB}pass",
        #             "",
        #         ]
        #         for type_definition in type_definitions
        #     ]
        #     for line in abstract_visit_method
        # ]

        return generic + signature + abstract_visit_methods + spacing

    @staticmethod
    def __generate_base_class(base_name: str) -> list[str]:
        """Generate base class."""
        signature = [
            "@dataclass(frozen=True)",
            f"class {base_name}(ABC):",
        ]
        abstract_accept_method = [
            f"{TAB}@abstractmethod",
            f"{TAB}def accept(self, visitor: Visitor[R]) -> R:",
            f"{TAB}{TAB}pass",
        ]
        spacing = [
            "",
            "",
        ]

        return signature + abstract_accept_method + spacing

    @staticmethod
    def __generate_child_classes(
        base_name: str, type_definitions: list[TypeDefinition]
    ) -> list[str]:
        """Generate child classes based on type definitions."""
        child_classes: list[str] = []
        for index, type_definition in enumerate(type_definitions):
            child_classes.extend(
                GenerateAst.__generate_child_class(base_name, type_definition)
            )

            if index != len(type_definitions) - 1:
                child_classes.extend(["", ""])

        return child_classes

    @staticmethod
    def __generate_child_class(
        base_name: str, type_definition: TypeDefinition
    ) -> list[str]:
        """Generate single child class based on type definition."""
        signature = [
            "@dataclass(frozen=True)",
            f"class {type_definition.name}({base_name}):",
        ]
        attributes = [
            *[
                f"{TAB}{attr_name}: {attr_type}"
                for attr_name, attr_type in type_definition.attributes
            ],
            "",
        ]
        accept_method = [
            f"{TAB}def accept(self, visitor: Visitor[R]) -> R:",
            f"{TAB}{TAB}return visitor.visit_{type_definition.name.lower()}_{base_name.lower()}(self)",
        ]

        return signature + attributes + accept_method


if __name__ == "__main__":
    # Testing.
    GenerateAst.main(["lox"])
    with open("lox/expr.py", "r", encoding="utf-8") as file:
        print(file.read())
