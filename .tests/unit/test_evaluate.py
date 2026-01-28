#!/usr/bin/env python
"""
Comprehensive test suite for evaluate.py
Tests all operators, precedence, variables, and edge cases
"""

import pytest
import sys
import os

# Add parent directory to path to import evaluate
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from evaluate import Evaluator


class TestArithmeticOperators:
    """Test all arithmetic operators"""
    
    def test_addition(self):
        assert Evaluator("5 + 3", {}) == 8
        assert Evaluator("x + y", {'x': 10, 'y': 20}) == 30
    
    def test_subtraction(self):
        assert Evaluator("10 - 3", {}) == 7
        assert Evaluator("x - y", {'x': 50, 'y': 20}) == 30
    
    def test_multiplication(self):
        assert Evaluator("4 * 3", {}) == 12
        assert Evaluator("x * y", {'x': 5, 'y': 6}) == 30
    
    def test_division(self):
        assert Evaluator("10 / 2", {}) == 5
        assert Evaluator("x / y", {'x': 15, 'y': 3}) == 5
    
    def test_floor_division(self):
        assert Evaluator("7 // 2", {}) == 3
        assert Evaluator("x // y", {'x': 17, 'y': 5}) == 3
    
    def test_modulus(self):
        assert Evaluator("10 % 3", {}) == 1
        assert Evaluator("x % y", {'x': 17, 'y': 5}) == 2
    
    def test_exponentiation(self):
        assert Evaluator("2 ** 3", {}) == 8
        assert Evaluator("x ** y", {'x': 3, 'y': 4}) == 81


class TestBitwiseOperators:
    """Test all bitwise operators"""
    
    def test_bitwise_and(self):
        assert Evaluator("12 & 10", {}) == 8  # 1100 & 1010 = 1000
        assert Evaluator("x & y", {'x': 12, 'y': 10}) == 8
    
    def test_bitwise_or(self):
        assert Evaluator("12 | 10", {}) == 14  # 1100 | 1010 = 1110
        assert Evaluator("x | y", {'x': 12, 'y': 10}) == 14
    
    def test_bitwise_xor(self):
        assert Evaluator("12 ^ 10", {}) == 6  # 1100 ^ 1010 = 0110
        assert Evaluator("x ^ y", {'x': 12, 'y': 10}) == 6
    
    @pytest.mark.xfail(reason="Bug: OpBitwiseInvert evaluates twice")
    def test_bitwise_invert(self):
        # Currently FAILS due to bug (evaluates twice)
        # After fix, ~5 should be -6
        result = Evaluator("~5", {})
        assert result == -6
    
    def test_shift_left(self):
        assert Evaluator("4 << 2", {}) == 16
        assert Evaluator("x << y", {'x': 4, 'y': 2}) == 16
    
    def test_shift_right(self):
        assert Evaluator("16 >> 2", {}) == 4
        assert Evaluator("x >> y", {'x': 16, 'y': 2}) == 4


class TestLogicalOperators:
    """Test all logical operators"""
    
    def test_logical_and(self):
        assert Evaluator("1 && 1", {}) == 1
        assert Evaluator("1 && 0", {}) == 0
        assert Evaluator("x && y", {'x': 1, 'y': 1}) == 1
    
    def test_logical_or(self):
        assert Evaluator("0 || 1", {}) == 1
        assert Evaluator("0 || 0", {}) == 0
        assert Evaluator("x || y", {'x': 0, 'y': 1}) == 1
    
    @pytest.mark.xfail(reason="Bug: OpLogicalNot evaluates twice")
    def test_logical_not(self):
        # Currently FAILS due to bug (evaluates twice)
        # After fix, !0 should be True/1
        result = Evaluator("!0", {})
        assert result == 1
        result = Evaluator("!1", {})
        assert result == 0


class TestComparisonOperators:
    """Test all comparison operators"""
    
    def test_equal_to(self):
        assert Evaluator("5 == 5", {}) == 1
        assert Evaluator("5 == 3", {}) == 0
    
    def test_not_equal_to(self):
        assert Evaluator("5 != 3", {}) == 1
        assert Evaluator("5 != 5", {}) == 0
        assert Evaluator("5 <> 3", {}) == 1  # Alternative syntax
    
    def test_greater_than(self):
        assert Evaluator("5 > 3", {}) == 1
        assert Evaluator("3 > 5", {}) == 0
    
    def test_less_than(self):
        assert Evaluator("3 < 5", {}) == 1
        assert Evaluator("5 < 3", {}) == 0
    
    def test_greater_than_or_equal(self):
        assert Evaluator("5 >= 3", {}) == 1
        assert Evaluator("5 >= 5", {}) == 1
        assert Evaluator("5 => 5", {}) == 1  # Alternative syntax
    
    def test_less_than_or_equal(self):
        assert Evaluator("3 <= 5", {}) == 1
        assert Evaluator("5 <= 5", {}) == 1
        assert Evaluator("5 =< 5", {}) == 1  # Alternative syntax


class TestParentheses:
    """Test parentheses handling"""
    
    def test_simple_parentheses(self):
        assert Evaluator("(5 + 3)", {}) == 8
    
    def test_precedence_with_parentheses(self):
        assert Evaluator("2 + 3 * 4", {}) == 14
        assert Evaluator("(2 + 3) * 4", {}) == 20
    
    def test_nested_parentheses(self):
        assert Evaluator("((2 + 3) * 4) + 1", {}) == 21
    
    def test_multiple_groups(self):
        assert Evaluator("(2 + 3) * (4 + 1)", {}) == 25


class TestVariables:
    """Test variable handling"""
    
    def test_simple_variable(self):
        assert Evaluator("x", {'x': 42}) == 42
    
    def test_variable_in_expression(self):
        assert Evaluator("x + y * z", {'x': 2, 'y': 3, 'z': 4}) == 14
    
    def test_assignment(self):
        vars = {}
        result = Evaluator("x = 42", vars)
        assert result == 42
        assert vars['x'] == 42
    
    def test_assignment_with_expression(self):
        vars = {'a': 10}
        result = Evaluator("b = a + 5", vars)
        assert result == 15
        assert vars['b'] == 15
    
    def test_undefined_variable(self):
        with pytest.raises(Exception, match="Unknown variable"):
            Evaluator("undefined", {})
    
    def test_boolean_string_true(self):
        # TRUE/FALSE as strings should work without being defined
        assert Evaluator("TRUE", {}) == True
        assert Evaluator("True", {}) == True
        assert Evaluator("true", {}) == True
    
    def test_boolean_string_false(self):
        assert Evaluator("FALSE", {}) == False
        assert Evaluator("False", {}) == False
        assert Evaluator("false", {}) == False


class TestConstants:
    """Test constant handling"""
    
    def test_integer(self):
        assert Evaluator("42", {}) == 42
    
    def test_float(self):
        assert Evaluator("3.14", {}) == 3.14
    
    def test_negative_number(self):
        # Negative numbers parsed as subtraction from zero context
        assert Evaluator("0 - 5", {}) == -5
    
    def test_boolean_true_quoted(self):
        result = Evaluator('"TRUE"', {})
        assert result == '"TRUE"'
    
    def test_boolean_false_quoted(self):
        result = Evaluator('"FALSE"', {})
        assert result == '"FALSE"'
    
    def test_string(self):
        result = Evaluator('"hello"', {})
        assert result == '"hello"'


class TestComplexExpressions:
    """Test complex real-world expressions"""
    
    def test_mixed_operations(self):
        assert Evaluator("2 + 3 * 4 - 5", {}) == 9
    
    def test_all_precedence(self):
        # Test operator precedence: ** > * / > + -
        assert Evaluator("1 + 2 * 3 ** 2", {}) == 19  # 1 + 2*9 = 19
    
    def test_complex_with_variables(self):
        vars = {'a': 10, 'b': 5, 'c': 2}
        assert Evaluator("a + b * c", vars) == 20
    
    def test_bitwise_and_arithmetic(self):
        assert Evaluator("(8 & 12) + (4 | 2)", {}) == 14  # 8 + 6 = 14
    
    def test_comparison_in_expression(self):
        # Comparisons return 1 or 0, can be used in expressions
        assert Evaluator("(5 > 3) + (2 < 1)", {}) == 1  # 1 + 0 = 1
    
    def test_logical_with_comparison(self):
        assert Evaluator("(5 > 3) && (2 < 4)", {}) == 1
        assert Evaluator("(5 < 3) || (2 < 4)", {}) == 1


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_division_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            Evaluator("1 / 0", {})
    
    def test_unbalanced_parentheses_left(self):
        with pytest.raises(AssertionError, match="Unalanced"):
            Evaluator("(1 + 2", {})
    
    def test_unbalanced_parentheses_right(self):
        with pytest.raises(Exception):
            Evaluator("1 + 2)", {})
    
    def test_string_without_quotes(self):
        # Non-quoted strings should fail (treated as undefined variables)
        with pytest.raises(Exception):
            Evaluator("hello", {})
    
    def test_empty_parentheses(self):
        with pytest.raises(Exception):
            Evaluator("()", {})


class TestOperatorPrecedence:
    """Test operator precedence is correct"""
    
    def test_multiplication_before_addition(self):
        assert Evaluator("2 + 3 * 4", {}) == 14  # not 20
    
    def test_exponentiation_before_multiplication(self):
        assert Evaluator("2 * 3 ** 2", {}) == 18  # not 36
    
    def test_comparison_before_logical(self):
        assert Evaluator("1 < 2 && 3 > 2", {}) == 1
    
    def test_bitwise_precedence(self):
        # Bitwise operators have specific precedence
        # This tests that & has higher precedence than |
        assert Evaluator("12 | 8 & 4", {}) == 12  # (12 | (8 & 4)) = 12 | 0 = 12


class TestRealWorldUseCases:
    """Test patterns likely used in BT configuration"""
    
    def test_path_construction(self):
        # Typical use: building paths from variables
        vars = {'BASE': '"C:/path"', 'SUB': '"subdir"'}
        # Note: string concatenation not supported, but variables work
        assert Evaluator("BASE", vars) == '"C:/path"'
    
    def test_conditional_value(self):
        # Using comparison to select values
        vars = {'DEBUG': 1, 'RELEASE': 0}
        assert Evaluator("DEBUG && 5", vars) == 5
        assert Evaluator("RELEASE && 5", vars) == 0
    
    def test_numeric_configuration(self):
        vars = {'CORES': 8, 'THREADS_PER_CORE': 2}
        assert Evaluator("CORES * THREADS_PER_CORE", vars) == 16
    
    def test_flag_combination(self):
        # Combining bit flags
        vars = {'FLAG_A': 1, 'FLAG_B': 2, 'FLAG_C': 4}
        assert Evaluator("FLAG_A | FLAG_B | FLAG_C", vars) == 7
