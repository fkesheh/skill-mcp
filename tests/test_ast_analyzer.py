"""Tests for AST analyzer utility."""

import pytest
from pathlib import Path
from skill_mcp.utils.ast_analyzer import PythonImportAnalyzer


@pytest.fixture
def tmp_python_files(tmp_path):
    """Create temporary Python files for testing."""
    return tmp_path


class TestPythonImportAnalyzer:
    """Test Python import analysis."""

    def test_extract_imports_standard_lib(self, tmp_python_files):
        """Test extracting standard library imports."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
""")

        result = PythonImportAnalyzer.extract_imports(test_file)

        assert "os" in result["standard_lib"]
        assert "sys" in result["standard_lib"]
        assert "json" in result["standard_lib"]
        assert "pathlib" in result["standard_lib"]
        assert "datetime" in result["standard_lib"]

    def test_extract_imports_third_party(self, tmp_python_files):
        """Test extracting third-party imports."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
import requests
import pandas
from flask import Flask
from numpy import array
""")

        result = PythonImportAnalyzer.extract_imports(test_file)

        assert "requests" in result["third_party"]
        assert "pandas" in result["third_party"]
        assert "flask" in result["third_party"]
        assert "numpy" in result["third_party"]

    def test_extract_imports_local(self, tmp_python_files):
        """Test extracting local imports."""
        # Create a local module
        local_module = tmp_python_files / "utils.py"
        local_module.write_text("# Local module")

        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
import utils
from utils import helper
""")

        result = PythonImportAnalyzer.extract_imports(test_file)

        assert "utils" in result["local"]

    def test_extract_imports_mixed(self, tmp_python_files):
        """Test extracting mixed imports."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
import os
import sys
import requests
import pandas
from pathlib import Path
from flask import Flask
""")

        result = PythonImportAnalyzer.extract_imports(test_file)

        # Standard library
        assert "os" in result["standard_lib"]
        assert "sys" in result["standard_lib"]
        assert "pathlib" in result["standard_lib"]

        # Third party
        assert "requests" in result["third_party"]
        assert "pandas" in result["third_party"]
        assert "flask" in result["third_party"]

    def test_extract_imports_from_submodule(self, tmp_python_files):
        """Test extracting imports from submodules."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
from os.path import join
from collections.abc import Mapping
from requests.adapters import HTTPAdapter
""")

        result = PythonImportAnalyzer.extract_imports(test_file)

        # Should extract the top-level module
        assert "os" in result["standard_lib"]
        assert "collections" in result["standard_lib"]
        assert "requests" in result["third_party"]

    def test_extract_imports_with_aliases(self, tmp_python_files):
        """Test extracting imports with aliases."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
import numpy as np
import pandas as pd
from requests import get as http_get
""")

        result = PythonImportAnalyzer.extract_imports(test_file)

        assert "numpy" in result["third_party"]
        assert "pandas" in result["third_party"]
        assert "requests" in result["third_party"]

    def test_extract_imports_invalid_syntax(self, tmp_python_files):
        """Test extracting imports from file with invalid syntax."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
import os
def invalid syntax here
import sys
""")

        result = PythonImportAnalyzer.extract_imports(test_file)

        # Should return empty structure on parse error
        assert result["standard_lib"] == []
        assert result["third_party"] == []
        assert result["local"] == []

    def test_extract_imports_empty_file(self, tmp_python_files):
        """Test extracting imports from empty file."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("")

        result = PythonImportAnalyzer.extract_imports(test_file)

        assert result["standard_lib"] == []
        assert result["third_party"] == []
        assert result["local"] == []

    def test_extract_function_calls_basic(self, tmp_python_files):
        """Test extracting basic function calls."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
def my_function():
    print("Hello")
    len([1, 2, 3])
    str(42)
""")

        result = PythonImportAnalyzer.extract_function_calls(test_file)

        assert "print" in result
        assert "len" in result
        assert "str" in result

    def test_extract_function_calls_with_methods(self, tmp_python_files):
        """Test extracting function calls with method calls."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
def test():
    obj.method()
    obj.property.another_method()
    MyClass().do_something()
""")

        result = PythonImportAnalyzer.extract_function_calls(test_file)

        assert "obj.method" in result
        assert "obj.property.another_method" in result
        assert "MyClass" in result

    def test_extract_function_calls_nested(self, tmp_python_files):
        """Test extracting nested function calls."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
result = int(str(len([1, 2, 3])))
""")

        result = PythonImportAnalyzer.extract_function_calls(test_file)

        assert "int" in result
        assert "str" in result
        assert "len" in result

    def test_extract_function_calls_invalid_syntax(self, tmp_python_files):
        """Test extracting function calls from invalid syntax."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("def invalid syntax")

        result = PythonImportAnalyzer.extract_function_calls(test_file)

        assert result == []

    def test_extract_env_var_usage_environ_dict(self, tmp_python_files):
        """Test extracting env var usage with os.environ dict access."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
import os
api_key = os.environ['API_KEY']
db_host = os.environ['DB_HOST']
""")

        result = PythonImportAnalyzer.extract_env_var_usage(test_file)

        assert "API_KEY" in result
        assert "DB_HOST" in result

    def test_extract_env_var_usage_getenv(self, tmp_python_files):
        """Test extracting env var usage with os.getenv."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
import os
api_key = os.getenv('API_KEY')
db_host = os.getenv('DB_HOST', 'localhost')
""")

        result = PythonImportAnalyzer.extract_env_var_usage(test_file)

        assert "API_KEY" in result
        assert "DB_HOST" in result

    def test_extract_env_var_usage_environ_get(self, tmp_python_files):
        """Test extracting env var usage with os.environ.get - NOT SUPPORTED."""
        # Note: The current implementation doesn't detect os.environ.get() calls
        # It only detects os.environ['KEY'] and os.getenv('KEY')
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
import os
api_key = os.environ.get('API_KEY')
""")

        result = PythonImportAnalyzer.extract_env_var_usage(test_file)

        # This is not currently detected by the implementation
        assert "API_KEY" not in result

    def test_extract_env_var_usage_mixed(self, tmp_python_files):
        """Test extracting env var usage with mixed methods."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
import os

var1 = os.environ['VAR1']
var2 = os.getenv('VAR2')
""")

        result = PythonImportAnalyzer.extract_env_var_usage(test_file)

        assert "VAR1" in result
        assert "VAR2" in result

    def test_extract_env_var_usage_no_vars(self, tmp_python_files):
        """Test extracting env var usage when none are used."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
import os
print("Hello")
""")

        result = PythonImportAnalyzer.extract_env_var_usage(test_file)

        assert len(result) == 0

    def test_extract_env_var_usage_invalid_syntax(self, tmp_python_files):
        """Test extracting env var usage from invalid syntax."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("def invalid syntax")

        result = PythonImportAnalyzer.extract_env_var_usage(test_file)

        assert len(result) == 0

    def test_get_all_defined_functions_functions_only(self, tmp_python_files):
        """Test getting all defined functions."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
def function1():
    pass

def function2(arg1, arg2):
    return arg1 + arg2

def _private_function():
    pass
""")

        result = PythonImportAnalyzer.get_all_defined_functions(test_file)

        assert "function1" in result
        assert "function2" in result
        assert "_private_function" in result

    def test_get_all_defined_functions_classes_only(self, tmp_python_files):
        """Test getting all defined classes."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
class MyClass:
    pass

class AnotherClass:
    def method(self):
        pass
""")

        result = PythonImportAnalyzer.get_all_defined_functions(test_file)

        assert "MyClass" in result
        assert "AnotherClass" in result

    def test_get_all_defined_functions_mixed(self, tmp_python_files):
        """Test getting all definitions (functions and classes)."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
class MyClass:
    def method(self):
        pass

def my_function():
    pass

class AnotherClass:
    pass

def another_function():
    pass
""")

        result = PythonImportAnalyzer.get_all_defined_functions(test_file)

        assert "MyClass" in result
        assert "AnotherClass" in result
        assert "my_function" in result
        assert "another_function" in result
        # Note: Methods ARE included by the current implementation
        assert "method" in result

    def test_get_all_defined_functions_nested(self, tmp_python_files):
        """Test getting definitions includes nested functions."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("""
def outer():
    def inner():
        pass
    return inner
""")

        result = PythonImportAnalyzer.get_all_defined_functions(test_file)

        # Both outer and inner should be found
        assert "outer" in result
        assert "inner" in result

    def test_get_all_defined_functions_empty_file(self, tmp_python_files):
        """Test getting definitions from empty file."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("")

        result = PythonImportAnalyzer.get_all_defined_functions(test_file)

        assert result == []

    def test_get_all_defined_functions_invalid_syntax(self, tmp_python_files):
        """Test getting definitions from invalid syntax."""
        test_file = tmp_python_files / "test.py"
        test_file.write_text("def invalid syntax")

        result = PythonImportAnalyzer.get_all_defined_functions(test_file)

        assert result == []
