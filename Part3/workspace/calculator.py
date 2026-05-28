import sys

OPERATORS = {
    '+': lambda a, b: a + b,
    '-': lambda a, b: a - b,
    '*': lambda a, b: a * b,
    '/': lambda a, b: a / b,
    '%': lambda a, b: a % b,
    '**': lambda a, b: a ** b,
}

HELP_TEXT = """
Calculator CLI
Usage: python calculator.py <number> <operator> <number>
Operators: + - * / % **
Examples:
  python calculator.py 3 + 5
  python calculator.py 10 ** 2
  python calculator.py 9 % 4
Type 'help' for this message.
"""

def parse_args(args):
    if len(args) == 1 and args[0].lower() == 'help':
        print(HELP_TEXT)
        sys.exit(0)
    if len(args) != 3:
        raise ValueError("Expected: <number> <operator> <number>")
    try:
        a = float(args[0])
        b = float(args[2])
    except ValueError:
        raise ValueError("Both operands must be valid numbers.")
    op = args[1]
    if op not in OPERATORS:
        raise ValueError(f"Unknown operator '{op}'. Supported: {list(OPERATORS.keys())}")
    return a, op, b

def calculate(a, op, b):
    if op == '/' and b == 0:
        raise ValueError("Division by zero is not allowed.")
    if op == '%' and b == 0:
        raise ValueError("Modulo by zero is not allowed.")
    return OPERATORS[op](a, b)

def main():
    if len(sys.argv) < 2:
        print("Error: No arguments provided.")
        print(HELP_TEXT)
        sys.exit(1)
    try:
        a, op, b = parse_args(sys.argv[1:])
        result = calculate(a, op, b)
        print(f"{a} {op} {b} = {result}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
