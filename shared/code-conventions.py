"""
Shared code conventions for the project.

This module defines standard Python style rules and project-specific guidelines
to ensure consistent code quality during automated reviews.
"""

from typing import TypedDict

class WhitespaceConfig(TypedDict):
    before_colon: bool
    after_comma: bool
    around_operators: bool

class StyleConfig(TypedDict):
    indentation: int
    max_line_length: int
    import_order: list[str]
    whitespace: WhitespaceConfig

class NamingConfig(TypedDict):
    variables: str
    functions: str
    classes: str
    constants: str

class DocstringsConfig(TypedDict):
    style: str
    required: bool

class TypeHintsConfig(TypedDict):
    required: bool
    for_parameters: bool
    for_return: bool

class TestingConfig(TypedDict):
    file_pattern: str
    coverage_threshold: int

class LoggingConfig(TypedDict):
    format: str
    level: str

class ProjectSpecificConfig(TypedDict):
    async_await: str
    error_handling: str
    comments: str

class ConventionsConfig(TypedDict):
    style: StyleConfig
    naming: NamingConfig
    docstrings: DocstringsConfig
    type_hints: TypeHintsConfig
    testing: TestingConfig
    logging: LoggingConfig
    project_specific: ProjectSpecificConfig

CONVENTIONS: ConventionsConfig = {
    "style": {
        "indentation": 4,
        "max_line_length": 120,
        "import_order": ["standard", "third-party", "local"],
        "whitespace": {
            "before_colon": False,
            "after_comma": True,
            "around_operators": True
        }
    },
    "naming": {
        "variables": "snake_case",
        "functions": "snake_case",
        "classes": "PascalCase",
        "constants": "UPPER_SNAKE_CASE"
    },
    "docstrings": {
        "style": "Google",
        "required": True
    },
    "type_hints": {
        "required": True,
        "for_parameters": True,
        "for_return": True
    },
    "testing": {
        "file_pattern": "test_*.py",
        "coverage_threshold": 80
    },
    "logging": {
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "level": "INFO"
    },
    "project_specific": {
        "async_await": "required for async functions",
        "error_handling": "use specific exceptions, avoid bare except",
        "comments": "use # for single-line comments, triple quotes for docstrings"
    }
}
