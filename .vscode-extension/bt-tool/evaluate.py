#!/usr/bin/env python
"""
Expression evaluator - REFACTORED VERSION
Reduces from 636 lines to ~300 lines using data-driven operator registry
Fixes bugs: OpBitwiseInvert and OpLogicalNot no longer evaluate twice
Fixes bitwise operations by converting floats to ints
"""

# Standard python modules
import operator as op
import re
import sys

# Local modules
# None

####################
# Global variables #
####################

# Operator Registry: Maps symbols to (function, precedence, arity, requires_int)
# Precedence: lower number = evaluated first
# Arity: 1=unary (prefix), 2=binary, 0=special (parentheses)
OPERATOR_REGISTRY = {
    # Arithmetic (precedence 5-7)
    '**': (op.pow, 5, 2, False),
    '*':  (op.mul, 6, 2, False),
    '/':  (op.truediv, 6, 2, False),
    '//': (op.floordiv, 6, 2, False),
    '%':  (op.mod, 6, 2, False),
    '+':  (op.add, 7, 2, False),
    '-':  (op.sub, 7, 2, False),
    
    # Bitwise (precedence 3-4, requires int)
    '<<': (op.lshift, 3, 2, True),
    '>>': (op.rshift, 3, 2, True),
    '&':  (op.and_, 4, 2, True),
    '^':  (op.xor, 4, 2, True),
    '|':  (op.or_, 4, 2, True),
    '~':  (op.inv, 1, 1, True),  # Unary
    
    # Comparison (precedence 8)
    '==': (op.eq, 8, 2, False),
    '!=': (op.ne, 8, 2, False),
    '<>': (op.ne, 8, 2, False),  # Alternative syntax
    '<':  (op.lt, 8, 2, False),
    '>':  (op.gt, 8, 2, False),
    '<=': (op.le, 8, 2, False),
    '=<': (op.le, 8, 2, False),  # Alternative syntax
    '>=': (op.ge, 8, 2, False),
    '=>': (op.ge, 8, 2, False),  # Alternative syntax
    
    # Logical (precedence 9-10)
    '!':  (op.not_, 1, 1, False),  # Unary
    '&&': (lambda a, b: a and b, 9, 2, False),
    '||': (lambda a, b: a or b, 10, 2, False),
    
    # Assignment (precedence 11)
    '=':  (None, 11, 2, False),  # Special handling needed
    
    # Parentheses (precedence 0)
    '(':  (None, 0, 0, False),
    ')':  (None, 0, 0, False),
}

# Build list of operators sorted by length (longest first for regex)
operators = sorted(OPERATOR_REGISTRY.keys(), key=lambda x: -len(x))

# Build delimiter regular expression from operators
reDelims = ''               # Start with empty string
sep      = ''               # Start with no separator
for delim in operators:     # Loop through operators
    reDelims += sep + delim # Add operator and separator
    sep      = ' '          # Change separator to space
# Add escape to characters for operators that need it
reDelims = re.sub(r'(\*|\||\+|\-|\^|\(|\))', r'\\\g<1>', reDelims)
# Make delimiter regular expression a big OR
reDelims = '(' + re.sub(' ', '|', reDelims) + ')'

# Priority list (operator class names in evaluation order)
priority = [
    'OpBitwiseInvert', 'OpLogicalNot',         # Unary operators (precedence 1)
    'OpShiftBitsLeft', 'OpShiftBitsRight',     # Shift operators (precedence 3)
    'OpBitwiseAnd',                            # Bitwise AND (precedence 4)
    'OpBitwiseXor',                            # Bitwise XOR (precedence 4)
    'OpBitwiseOr',                             # Bitwise OR (precedence 4)
    'OpExponentiate',                          # Exponentiation (precedence 5)
    'OpMultiply', 'OpDivide', 'OpFloorDivide', 'OpModulus',  # Multiplicative (precedence 6)
    'OpAdd', 'OpSubtract',                     # Additive (precedence 7)
    'OpEqualTo', 'OpNotEqualTo', 'OpGreaterThan', 'OpLessThan',  # Comparison (precedence 8)
    'OpGreaterThanOrEqualTo', 'OpLessThanOrEqualTo',
    'OpLogicalAnd',                            # Logical AND (precedence 9)
    'OpLogicalOr',                             # Logical OR (precedence 10)
    'OpAssign',                                # Assignment (precedence 11)
]

# Map operator symbols to class names
SYMBOL_TO_CLASS = {
    '//': 'OpFloorDivide', '**': 'OpExponentiate', '&&': 'OpLogicalAnd', '||': 'OpLogicalOr',
    '==': 'OpEqualTo', '!=': 'OpNotEqualTo', '<>': 'OpNotEqualTo', '>=': 'OpGreaterThanOrEqualTo',
    '=>': 'OpGreaterThanOrEqualTo', '<=': 'OpLessThanOrEqualTo', '=<': 'OpLessThanOrEqualTo',
    '>>': 'OpShiftBitsRight', '<<': 'OpShiftBitsLeft', '=': 'OpAssign',
    '+': 'OpAdd', '-': 'OpSubtract', '*': 'OpMultiply', '/': 'OpDivide', '%': 'OpModulus',
    '^': 'OpBitwiseXor', '&': 'OpBitwiseAnd', '|': 'OpBitwiseOr', '>': 'OpGreaterThan',
    '<': 'OpLessThan', '(': 'OpLeftParenthesis', ')': 'OpRightParenthesis',
    '!': 'OpLogicalNot', '~': 'OpBitwiseInvert',
}

####################
# Classes          #
####################

# Base class for all terms
class Term:
    # Constructor: Must be overridden!
    def __init__(self):
        raise NotImplementedError()

    # Evaluate: Must be overridden!
    def Evaluate(self, dictionary):
        raise NotImplementedError()

    # Representor
    def __repr__(self):
        klass = self.__class__.__name__
        private = '_{0}__'.format(klass)
        args = []
        for name in self.__dict__:
            if name.startswith(private):
                value = self.__dict__[name]
                name = name[len(private):]
                args.append('{0}={1}'.format(name, repr(value)))
        return '{0}({1})'.format(klass, ', '.join(args))


# Base class for operands (constants and variables)
class Operand(Term):
    def __init__(self):
        raise NotImplementedError()

    def Evaluate(self, dictionary):
        raise NotImplementedError()


# Constant value
class Constant(Operand):
    def __init__(self, value):
        try:
            # Try to convert to float (handles boolean, binary, octal, hex, decimal)
            self.value = float(value)
        except:
            # If that didn't work, it must be a string - check if it's a boolean
            val = value.upper()
            if val in ('TRUE', '"TRUE"'):
                # Unquoted TRUE is boolean, quoted is string
                self.value = 1.0 if val == 'TRUE' else '"TRUE"'
            elif val in ('FALSE', '"FALSE"'):
                # Unquoted FALSE is boolean, quoted is string
                self.value = 0.0 if val == 'FALSE' else '"FALSE"'
            else:
                # A true string must have quotes around it
                assert value[0] == '"' and value[-1] == '"', 'String must be surrounded by quotes'
                self.value = value

    def Evaluate(self, dictionary):
        return self.value


# Variable reference
class Variable(Operand):
    def __init__(self, name):
        self.name = name

    def Evaluate(self, dictionary):
        # Check if it's defined in dictionary
        if self.name not in dictionary:
            # Not defined: handle boolean strings
            name = self.name.upper()
            if name == 'TRUE':  return True
            if name == 'FALSE': return False
            # Could not evaluate variable
            raise Exception('Unknown variable: ' + self.name)
        # Return value of variable
        return dictionary[self.name]


# Operator - unified class for all operators
class Operator(Term):
    def __init__(self, symbol):
        self.symbol = symbol
        if symbol in OPERATOR_REGISTRY:
            self.func, self.precedence, self.arity, self.requires_int = OPERATOR_REGISTRY[symbol]
        else:
            raise Exception('Unknown operator: ' + symbol)

    def Evaluate(self, left, right, dictionary):
        # Special handling for assignment
        if self.symbol == '=':
            assert left is not None and right is not None, 'Left and right items required'
            assert isinstance(left, Variable), 'Must assign to variable'
            value = right.Evaluate(dictionary)
            dictionary[left.name] = value
            return value
        
        # Special handling for parentheses
        if self.symbol in ('(', ')'):
            raise Exception('Parentheses should not be evaluated directly')
        
        # Unary operator
        if self.arity == 1:
            assert right is not None, 'Right item required for unary operator'
            value = right.Evaluate(dictionary)
            # Convert to int if required for bitwise operations
            if self.requires_int:
                value = int(value)
            return self.func(value)
        
        # Binary operator
        assert left is not None and right is not None, 'Left and right items required'
        lval = left.Evaluate(dictionary)
        rval = right.Evaluate(dictionary)
        
        # Convert to int if required for bitwise operations
        if self.requires_int:
            lval = int(lval)
            rval = int(rval)
        
        return self.func(lval, rval)


# Special operator classes for compatibility
class OpLeftParenthesis(Operator):
    def __init__(self):
        Operator.__init__(self, '(')


class OpRightParenthesis(Operator):
    def __init__(self):
        Operator.__init__(self, ')')


# Operation: combines operator with operands
class Operation(Term):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

    def Evaluate(self, dictionary):
        if isinstance(self.operator, Operator):
            return self.operator.Evaluate(self.left, self.right, dictionary)
        elif isinstance(self.left, OpLeftParenthesis):
            assert isinstance(self.right, OpRightParenthesis), 'Missing matching right parenthesis'
            # Evaluate operations extracted within the parenthesis
            # The operations inside have already been parenthesized
            # Now we need to reduce them using the priority list
            operations = self.operator
            for operator in priority:
                operations.Reduce(operator, not operator in ('OpLogicalNot', 'OpBitwiseInvert'))
            return operations.Evaluate(dictionary)


# Operations: sequence of operations
class Operations(Term):
    def __init__(self, tokens):
        # Convert tokens to operations
        self.operations = []
        for token in tokens:
            if isinstance(token, (Operand, Operator, Operation)):
                self.operations.append(token)
            else:
                raise Exception('Invalid token type')

    def Parenthesize(self):
        """Handle parentheses by grouping operations between them"""
        stack = []
        index = 0
        maxx = len(self.operations)
        
        while index < maxx:
            operation = self.operations[index]
            
            # Track opening parentheses
            if isinstance(operation, OpLeftParenthesis):
                stack.append(index)
            
            # Process closing parentheses
            elif isinstance(operation, OpRightParenthesis):
                assert len(stack) > 0, 'Unalanced parentheses'
                left = stack.pop()
                assert left + 1 < index, 'Empty parentheses'
                
                # Isolate operations between parentheses
                operations = Operations(self.operations[left + 1:index])
                # Recursively parenthesize any nested groups
                operations.Parenthesize()
                
                # Build parenthetical operation
                lOperator = OpLeftParenthesis()
                rOperator = OpRightParenthesis()
                operation = Operation(lOperator, operations, rOperator)
                
                # Rebuild operations with parenthetical operation in correct position
                operations_list = [] if left == 0 else self.operations[0:left]
                operations_list.append(operation)
                if index < len(self.operations) - 1:
                    operations_list.extend(self.operations[index + 1:])
                self.operations = operations_list
                
                # Update index and maximum length
                index = left
                maxx = len(self.operations)
            
            index += 1
        
        assert len(stack) == 0, 'Unalanced parentheses'

    def Reduce(self, targetOperation, useLeft):
        """Reduce all target operations"""
        left = None
        index = 0
        maxx = len(self.operations)
        
        while index < maxx:
            operation = self.operations[index]
            
            # Reduce targetOperations in parenthetical isolations
            if isinstance(operation, Operation) and hasattr(operation, 'left') and isinstance(operation.left, OpLeftParenthesis):
                operation.operator.Reduce(targetOperation, useLeft)
                index += 1
                continue
            
            # Continue if this is not a targeted operation (skip if it's an Operation or other type)
            if not isinstance(operation, Operator) or operation.__class__.__name__ != targetOperation:
                index += 1
                continue
            
            # Handle left operand
            if useLeft:
                assert index > 0, 'No left token for {0}'.format(targetOperation)
                left = self.operations[index - 1]
            
            # Handle right operand
            assert maxx > index, 'No right token for {0}'.format(targetOperation)
            right = self.operations[index + 1]
            
            # Create operation instance
            op_instance = eval(targetOperation + '()')
            new_operation = Operation(left, op_instance, right)
            
            # Update operations array
            operations_list = [] if index < 2 else self.operations[0:index - 1]
            operations_list.append(new_operation)
            if maxx > index + 2:
                operations_list.extend(self.operations[index + 2:])
            self.operations = operations_list
            
            # Update for next loop iteration
            maxx = len(self.operations)
            # Don't update index (already updated... for left, operator and right collapsed into one)

    def Evaluate(self, dictionary):
        """Process through the operations"""
        result = None
        # After all reductions are done, should have single item or be evaluating sub-operations
        for item in self.operations:
            result = item.Evaluate(dictionary)
        return result


# Generate operator classes dynamically for compatibility
for symbol, class_name in SYMBOL_TO_CLASS.items():
    if class_name not in ('OpLeftParenthesis', 'OpRightParenthesis'):
        # Create class dynamically
        exec(f'''
class {class_name}(Operator):
    def __init__(self):
        Operator.__init__(self, "{symbol}")
''')


####################
# Functions        #
####################

def Evaluator(string, local):
    """Evaluate a string expression"""
    # Fix string for compatibility on all computer platforms
    string = string.replace('\r\n', '\n').replace('\r', '\n')
    tokens = Tokenize(string)
    operations = Operations(tokens)
    operations.Parenthesize()
    for operator in priority:
        operations.Reduce(operator, not operator in ('OpLogicalNot', 'OpBitwiseInvert'))
    value = operations.Evaluate(local)
    return value


def Tokenize(string):
    """Tokenize a string into operators, constants, and variables"""
    tokens = []
    
    # Split line into tokens
    for token in Splitter(string):
        # Handle operators
        if token in OPERATOR_REGISTRY:
            class_name = SYMBOL_TO_CLASS[token]
            op = eval(class_name + '()')
            tokens.append(op)
        else:
            try:
                # The token is a constant if it is a number, boolean, or string
                tokens.append(Constant(token))
            except:
                # Otherwise it has to be a variable
                tokens.append(Variable(token))
    
    return tokens


def Splitter(line):
    """Split up a line of text into tokens"""
    global reDelims
    # Ensure all delimiters are separated by spaces
    line = re.sub(reDelims, r' \g<1> ', line)
    # Now replace multiple-space gaps with single spaces
    line = re.sub(r'(\s+)', ' ', line)
    # Now return the split up line
    return line.split()
