#!/usr/bin/env python

# Standard python modules
import re
import sys

# Local modules
# None

####################
# Global variables #
####################

# Operators: List of supported operators
# (listed from longest to shortest so they will be parsed correctly by the regular expression)
operators = [ '//', '**', '&&', '||', '==', '!=', '<>', '>=', '=>', '<=', '=<', '>>', '<<', '=',
              '+',  '-',  '*',  '/',  '%',  '^',  '&',  '|',  '>',  '<',  '(',  ')',  '!',  '~' ]

# Build delimiter regular expression from operators
reDelims = ''               # Start with empty string
sep      = ''               # Start with no seperator
for delim in operators:     # Loop through operators
    reDelims += sep + delim # Add operator and seperator
    sep      = ' '          # Change serperator to space
# Add escape to characters for operators that need it
reDelims = re.sub('(\*|\||\+|\-|\^|\(|\))', '\\\\\g<1>', reDelims)
# Make delimiter regular expression a big OR
reDelims = '(' + re.sub(' ', '|', reDelims) + ')'

# Classes: List of names of classes associated with the operators
# (must be listed in same order as operators)
classes   = [ 'OpFloorDivide',       'OpExponentiate',      'OpLogicalAnd',            'OpLogicalOr',            'OpEqualTo',
              'OpNotEqualTo',        'OpNotEqualTo',        'OpGreaterThanOrEqualTo',  'OpGreaterThanOrEqualTo', 'OpLessThanOrEqualTo',
              'OpLessThanOrEqualTo', 'OpShiftBitsLeft',     'OpShiftBitsRight',        'OpAssign',               'OpAdd',
              'OpSubtract',          'OpMultiply',          'OpDivide',                'OpModulus',              'OpBitwiseXor',
              'OpBitwiseAnd',        'OpBitwiseOr',         'OpGreaterThan',           'OpLessThan',             'OpLeftParenthesis',
              'OpRightParenthesis',  'OpLogicalNot',        'OpBitwiseInvert' ]

# Classes: List of names of classes in priority order
priority  = [ 'OpLogicalNot',        'OpBitwiseInvert',     'OpExponentiate',         'OpMultiply',              'OpDivide',
              'OpFloorDivide',       'OpModulus',           'OpAdd',                  'OpSubtract',              'OpShiftBitsLeft',
              'OpShiftBitsRight',    'OpGreaterThan',       'OpGreaterThanOrEqualTo', 'OpLessThan',              'OpLessThanOrEqualTo',
              'OpEqualTo',           'OpNotEqualTo',        'OpBitwiseAnd',           'OpBitwiseXor',            'OpBitwiseOr',
              'OpLogicalAnd',        'OpLogicalOr',         'OpAssign' ]

# Class for an generic operation item
class Term:
    # Construstor: Must be overridden!
    # returns nothing
    def __init__(self):
        raise NotImplementedError()

    # Evaulate: Must be overridden!
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

# Class for an operand
class Operand(Term):
    # Construstor: Must be overridden!
    # returns nothing
    def __init__(self):
        raise NotImplementedError()

    # Constructor: Must be overridden!
    # dictionary: Dictionary of defined items
    # returns     nothing
    def Evaluate(self, dictionary):
        raise NotImplementedError()

# Class for a constant
class Constant(Operand):
    # Constructor
    # value:  Value of constant
    # returns nothing
    def __init__(self, value):
        try:
          # First try to convert it to float (this handles boolean, binary, octal, hex, and of course decimal)
          self.value = float(value)
        except:
          # If that did not work it must be a string, see if it is boolean
          val = value.upper()
          if   val in ('TRUE', '"TRUE"'):   self.value = 1.0
          elif val in ('FALSE', '"FALSE"'): self.value = 0.0
          else:
            # A true string must have quotes around it
            assert value[0]  == '"' and value[-1] == '"', 'String must be surrounded by quotes'
            self.value = value

    # Evaluator
    # dictionary: Dictionary of defined items
    # returns     Constantd value
    def Evaluate(self, dictionary):
        return self.value

# Class for a variable
class Variable(Operand):
    # Constructor
    # returns nothing
    def __init__(self, name):
        # First remove quotes if present
        self.name = name

    # Evaluator
    # dictionary: Dictionary of defined items
    # returns     Value of variable
    def Evaluate(self, dictionary):
        # Make sure it is defiend
        if self.name not in dictionary:
            # Not a defined value: handle boolean strings
            name = self.name.upper()
            if name == 'TRUE':  return True
            if name == 'FALSE': return False
            # Could not evaluate variable
            raise Exception('Unknown variable: ' + self.name)
        # Return value of variable
        return dictionary[self.name]

# Class for an operator
class Operator(Term):
    # Constructor
    # returns nothing
    def __init__(self, operator):
        self.operator = operator

    # Evaluator: Must be overridden!
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        raise Exception('Unknown operator: ' + self.operator)

# The add operator (+)
class OpAdd(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '\+')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) + right.Evaluate(dictionary)

# The assignment operator (=)
class OpAssign(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '=')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        assert isinstance(left, Variable), 'Must Assign to Variable'
        name  = left.name
        value = right.Evaluate(dictionary)
        dictionary[name] = value
        return value

# The bitwise and operator (&)
class OpBitwiseAnd(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '&')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) & right.Evaluate(dictionary)

# The bitwise inversion operator (~)
class OpBitwiseInvert(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '~')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert right != None, 'Right item required'
        value = right.Evaluate(dictionary)
        return ~value.Evaluate(dictionary)

# The bitwsie or operator (|)
class OpBitwiseOr(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '\|')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) | right.Evaluate(dictionary)

# The bitwise exclusive or operator (^)
class OpBitwiseXor(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '\^')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) ^ right.Evaluate(dictionary)

# The divide operator (/)
class OpDivide(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '/')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) / right.Evaluate(dictionary)

# The equal to operator (==)
class OpEqualTo(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '==')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) == right.Evaluate(dictionary)

# The exponentiate operator (**)
class OpExponentiate(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '\*\*')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) ** right.Evaluate(dictionary)

# floor divide operator (//)
class OpFloorDivide(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '//')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) // right.Evaluate(dictionary)

# The greater than operator (>)
class OpGreaterThan(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '>')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None
        return left.Evaluate(dictionary) > right.Evaluate(dictionary)

# The greater than or equal to operator (>=, =>)
class OpGreaterThanOrEqualTo(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '>=')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) >= right.Evaluate(dictionary)

# The less than operator (<)
class OpLessThan(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '<')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) < right.Evaluate(dictionary)

# The less than or equal to operator (<=, =<)
class OpLessThanOrEqualTo(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '<=')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) <= right.Evaluate(dictionary)

# The left parenthesis operator (()
class OpLeftParenthesis(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '\(')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert right != None and follow != None, 'Right and follow items required'
        assert isinstance(follow, OpRightParenthesis), 'Must be followed by right parenthesis'
        return right.Evaluate(dictionary)

# The logical and operator (&&, and)
class OpLogicalAnd(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '&&')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) and right.Evaluate(dictionary)

# The logical not operator (!, not)
class OpLogicalNot(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '!')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert right != None, 'Right item required'
        value = right.Evaluate(dictionary)
        return not value.Evaluate(dictionary)

# The logical or operator (||, or)
class OpLogicalOr(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '\|\|')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) or right.Evaluate(dictionary)

# The modulus operator (%)
class OpModulus(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '%')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) % right.Evaluate(dictionary)

# The multiply operator (*)
class OpMultiply(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '\*')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        lft = left.Evaluate(dictionary)
        rgt = right.Evaluate(dictionary)
        return left.Evaluate(dictionary) * right.Evaluate(dictionary)

# The not equal to operator (!=, <>)
class OpNotEqualTo(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '!=')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) != right.Evaluate(dictionary)

# The right parenthesis operator ())
class OpRightParenthesis(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '\)')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        raise Exception('Unmatched right parenthesis encoundered: ")"')

# The shift bits left operator (<<)
class OpShiftBitsLeft(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '<<')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) << right.Evaluate(dictionary)

# The shift bits right operator (>>)
class OpShiftBitsRight(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '>>')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) >> right.Evaluate(dictionary)

# The subtract operator (-)
class OpSubtract(Operator):
    # Constructor
    # returns nothing
    def __init__(self):
        Operator.__init__(self, '\-')

    # Evaluator
    # left:       Left      expression (if any)
    # right:      Right     expression (if any)
    # dictionary: Dictionary to use during evaluation
    # returns     Resultant value
    def Evaluate(self, left, right, dictionary):
        assert left != None and right != None, 'Left and right items required'
        return left.Evaluate(dictionary) - right.Evaluate(dictionary)

# Class Operation
class Operation(Term):
    # Constructor
    # Constructor
    # returns nothing
    def __init__(self, left, operator, right):
        self.left     = left
        self.operator = operator
        self.right    = right

    # Evaluator
    def Evaluate(self, dictionary):
        if isinstance(self.operator, Operator):
            return self.operator.Evaluate(self.left, self.right, dictionary)
        elif isinstance(self.left, OpLeftParenthesis):
            assert isinstance(self.right, OpRightParenthesis), 'Missing matching right parenthesis'
            # Evaluate operations extracted within the parenthesis
            operations = self.operator
            return operations.Evaluate(dictionary)

# Class of operations
class Operations(Term):
    # Constructor
    # returns nothing
    def __init__(self, tokens):
        self.operations = tokens

    # Handle parenthesis
	# retuns nothing on success, DOES NOT RETURN if parenthesis are unbalanced
    def Parenthesize(self):
        # Scan forward through the operations
        stack = []                      # No left parenthesis encontered
        index = 0                       # Current operation
        maxx  = len(self.operations)    # Maximum numner of operations
        # Loop while there are operations to check
        while index < maxx:
            # See if we have a parenthesis
            operation = self.operations[index]
            if isinstance(operation, (OpLeftParenthesis, OpRightParenthesis)):
                if isinstance(operation, OpLeftParenthesis):
                    # Left parenthesis - mark its position
                    stack.append(index)
                else:
                    # Right parenthesis - check balance
                    assert len(stack) > 0, 'Unbalanced parenthesis'
                    # Get matching left parenthesis location
                    left = stack.pop()
                    # Make sure it makes sense
                    assert left + 1 < index
                    # Isolate operations between the parenthesis
                    operations = Operations(self.operations[left + 1:index])
                    # Build a parenthetical operation
                    lOperator = OpLeftParenthesis()
                    rOperator = OpRightParenthesis()
                    operation = Operation(lOperator, operations, rOperator)
                    # Rebuild operations with parenthetical operation in correct position
                    operations = [] if left == 0 else self.operations[0:left]
                    operations.append(operation)
                    if index < len(self.operations):
                        for remaining in self.operations[index + 1:]: operations.append(remaining)
                    self.operations = operations
                    # Upate index and maximum length
                    index = left
                    maxx  = len(self.operations)
            # Increment index
            index += 1
        assert len(stack) == 0, 'Unalanced parentheses'

    # Reduce all target operations
    # targetOperation: operation being targeted
    # useLeft:         indicates if left operand is to be used    
    def Reduce(self, targetOperation, useLeft):
        left  = None        # Assume no left value
        # Scan forward through the operations
        index = 0
        maxx  = len(self.operations)
        while index < maxx:
            operation = self.operations[index]
            # Reduce targetOperations in parenthetical isolations
            if hasattr(operation, 'left') and isinstance(operation.left, OpLeftParenthesis):
                operation.operator.Reduce(targetOperation, useLeft)
                index += 1
                continue
            # Continue if this is not one is a targeted operations
            if not operation.__class__.__name__ == targetOperation:
                index += 1
                continue
            # Handle left operand
            if useLeft:
                assert index > 0, 'No left token for {0}'.format(targetOperation)
                left  = self.operations[index - 1]
            # Handle right operand
            assert maxx > index, 'No right token for {0}'.format(targetOperation)
            right = self.operations[index + 1]
            # Create operation
            line = targetOperation + '()'
            operation = Operation(left, eval(line), right)
            # Update operations array appropriately
            operations = [] if index < 2 else self.operations[0:index - 1]
            operations.append(operation)
            if maxx > index + 2:
                for remaining in self.operations[index + 2:]: operations.append(remaining)
            self.operations = operations
            # Upate for next loop iteration
            maxx  = len(self.operations)
            # Don't update index (already updated ... for left, operator and right colapsed into one)
            
    # Evaluator
    def Evaluate(self, dictionary):
        # Process through the operations
        for operation in self.operations:
            result = operation.Evaluate(dictionary)
        return result

# Evaluator of a string
# local - variable definitions to use
def Evaluator(string, local):
    global priorty
    # Fix string for compatibility on all computer platforms
    string     = string.replace('\r\n', '\n').replace('\r', '\n')
    tokens     = Tokenize(string)
    operations = Operations(tokens)
    operations.Parenthesize()
    for operator in priority:
        operations.Reduce(operator, not operator in ('OpLogicalNot', 'OpBitwiseInvert'))
    value = operations.Evaluate(local)
    #print(value)
    return(value)

# Tokenize a string
def Tokenize(string):
    global operators, classes
    # Start with no tokens
    #print(string)
    tokens = []
    # Split line into tokens
    for token in Splitter(string):
        # Handle operators
        if token in operators:
            idx = operators.index(token)
            op  = eval(classes[idx])
            tokens.append(op())
        else:
            try:
                # The token is a constant if it is an Number, Boolean or String
                tokens.append(Constant(token))
            except:
                # ... otherwise it has to be a variable
                tokens.append(Variable(token))
    return tokens

# Split up a line of text into tokens
def Splitter(line):
  global reDelims
  # Ensure all delimiters are separated by spaces
  line = re.sub(reDelims, ' \g<1> ', line)
  # Now replace multiple-space gaps with single spaces
  line = re.sub('(\s+)',  ' ', line)
  # Now return the split up line
  return line.split()
