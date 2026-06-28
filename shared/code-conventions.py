"""
Shared code conventions for the project.

This module defines standard Python style rules and project-specific guidelines
to ensure consistent code quality during automated reviews.
"""

CONVENTIONS = {
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
