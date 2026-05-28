# ============================================================
# TEMPLATES -- Part 3: Mo-Assistant
# ============================================================
# Pre-written responses for common questions.
# When a message matches a template, Mo-Assistant replies
# instantly with the pre-written answer -- no Claude call needed.
#
# WHY THIS MATTERS:
# Every Claude call costs tokens and takes 1-2 seconds.
# Questions like "who are you?" or "write a hello world" don't
# need AI to answer. A pre-written reply is:
#   - FREE  (0 tokens)
#   - FAST  (instant, no API call)
#   - CONSISTENT (always the same reliable answer)
#
# HOW MATCHING WORKS:
# We check if any keyword from a template appears in the message.
# If yes -> return that template's response.
# If no match found -> return None -> caller falls through to Claude.
#
# HOW TO ADD A NEW TEMPLATE:
# Add a new block to the TEMPLATES list below:
#   {
#       "keywords": ["word1", "word2"],   <- any of these trigger it
#       "response": "Your reply here."    <- what Mo-Assistant says
#   }
#
# TEMPLATES ARE GROUPED BY CATEGORY:
#   1. Identity & status
#   2. Hello world
#   3. String operations
#   4. List operations
#   5. Dictionary operations
#   6. File operations
#   7. Error handling
#   8. Functions & classes
#   9. Loops & comprehensions
#  10. API requests
#  11. Algorithms
#  12. Terminal & environment
# ============================================================


# ─── TEMPLATES ──────────────────────────────────────────────

TEMPLATES = [
    # ════════════════════════════════════════════════════════
    # CATEGORY 1: IDENTITY & STATUS
    # ════════════════════════════════════════════════════════
    {
        "keywords": [
            "who are you",
            "what are you",
            "introduce yourself",
            "your name",
            "what is mo-alshayeb-agent",
            "tell me about yourself",
        ],
        "response": (
            "I am Mo-Alshayeb-Agent, a software engineering agent built by Mo. "
            "I can write Python code, review and debug code, answer software "
            "engineering questions, and collaborate with other agents on projects."
        ),
    },
    {
        "keywords": [
            "what can you do",
            "your capabilities",
            "what do you do",
            "how can you help",
            "what are your skills",
        ],
        "response": (
            "Here is what I can help with:\n"
            "- Write Python functions and scripts\n"
            "- Review and debug existing code\n"
            "- Answer software engineering questions\n"
            "- Suggest architecture and design improvements\n"
            "Just ask and I will get to work!"
        ),
    },
    {
        "keywords": [
            "are you online",
            "are you there",
            "are you active",
            "is mo-alshayeb-agent online",
            "mo-alshayeb-agent status",
        ],
        "response": "Mo-Alshayeb-Agent is online and ready to collaborate!",
    },
    {
        "keywords": [
            "how do you work",
            "how are you built",
            "what model are you",
            "which ai are you",
            "what powers you",
        ],
        "response": (
            "I am built with Python and the Anthropic Claude API (Haiku model). "
            "I watch the group chat, decide when to reply using smart filtering, "
            "use pre-written templates for common questions (saves tokens), "
            "and fall back to Claude AI for complex answers. "
            "I can also write real Python files directly to a workspace folder."
        ),
    },
    # ════════════════════════════════════════════════════════
    # CATEGORY 3: STRING OPERATIONS
    # ════════════════════════════════════════════════════════
    {
        "keywords": [
            "reverse a string",
            "reverse string",
            "flip a string",
            "string reverse",
            "backwards string",
        ],
        "response": (
            "Here are two ways to reverse a string in Python:\n\n"
            "```python\n"
            "# Method 1: slicing (most Pythonic)\n"
            "def reverse_string(s):\n"
            "    return s[::-1]\n\n"
            "# Method 2: built-in reversed()\n"
            "def reverse_string(s):\n"
            "    return ''.join(reversed(s))\n\n"
            "print(reverse_string('hello'))  # Output: olleh\n"
            "```"
        ),
    },
    {
        "keywords": [
            "count words",
            "word count",
            "count characters",
            "string length",
            "len of string",
        ],
        "response": (
            "Counting in Python strings:\n\n"
            "```python\n"
            "text = 'Hello World'\n\n"
            "# Count characters\n"
            "print(len(text))          # 11\n\n"
            "# Count words\n"
            "print(len(text.split()))  # 2\n\n"
            "# Count a specific character\n"
            "print(text.count('l'))    # 3\n"
            "```"
        ),
    },
    {
        "keywords": [
            "uppercase",
            "lowercase",
            "upper case",
            "lower case",
            "capitalize string",
            "string case",
        ],
        "response": (
            "String case operations in Python:\n\n"
            "```python\n"
            "text = 'Hello World'\n\n"
            "print(text.upper())      # HELLO WORLD\n"
            "print(text.lower())      # hello world\n"
            "print(text.capitalize()) # Hello world\n"
            "print(text.title())      # Hello World\n"
            "print(text.swapcase())   # hELLO wORLD\n"
            "```"
        ),
    },
    # ════════════════════════════════════════════════════════
    # CATEGORY 4: LIST OPERATIONS
    # ════════════════════════════════════════════════════════
    {
        "keywords": [
            "sort a list",
            "sort list",
            "order a list",
            "sort array",
            "sorted list",
        ],
        "response": (
            "Sorting lists in Python:\n\n"
            "```python\n"
            "numbers = [3, 1, 4, 1, 5, 9, 2, 6]\n\n"
            "# Sort in place (modifies original)\n"
            "numbers.sort()\n"
            "print(numbers)  # [1, 1, 2, 3, 4, 5, 6, 9]\n\n"
            "# Return new sorted list (original unchanged)\n"
            "numbers = [3, 1, 4, 1, 5]\n"
            "sorted_nums = sorted(numbers)\n\n"
            "# Sort in reverse order\n"
            "numbers.sort(reverse=True)\n\n"
            "# Sort a list of strings\n"
            "names = ['Charlie', 'Alice', 'Bob']\n"
            "names.sort()  # ['Alice', 'Bob', 'Charlie']\n"
            "```"
        ),
    },
    {
        "keywords": [
            "remove duplicates",
            "unique list",
            "remove duplicate",
            "list without duplicates",
            "distinct values",
        ],
        "response": (
            "Remove duplicates from a list in Python:\n\n"
            "```python\n"
            "numbers = [1, 2, 2, 3, 3, 3, 4]\n\n"
            "# Method 1: convert to set (order not preserved)\n"
            "unique = list(set(numbers))\n\n"
            "# Method 2: keep original order\n"
            "unique = list(dict.fromkeys(numbers))\n\n"
            "print(unique)  # [1, 2, 3, 4]\n"
            "```"
        ),
    },
    {
        "keywords": [
            "flatten list",
            "nested list",
            "list of lists",
            "flatten nested",
            "2d list to 1d",
        ],
        "response": (
            "Flatten a nested list in Python:\n\n"
            "```python\n"
            "nested = [[1, 2], [3, 4], [5, 6]]\n\n"
            "# Method 1: list comprehension\n"
            "flat = [item for sublist in nested for item in sublist]\n\n"
            "# Method 2: itertools\n"
            "import itertools\n"
            "flat = list(itertools.chain.from_iterable(nested))\n\n"
            "print(flat)  # [1, 2, 3, 4, 5, 6]\n"
            "```"
        ),
    },
    # ════════════════════════════════════════════════════════
    # CATEGORY 5: DICTIONARY OPERATIONS
    # ════════════════════════════════════════════════════════
    {
        "keywords": [
            "what is a dictionary",
            "how to use dictionary",
            "python dict",
            "key value",
            "create dict",
        ],
        "response": (
            "Python dictionaries store key-value pairs:\n\n"
            "```python\n"
            "# Create a dictionary\n"
            "person = {'name': 'Mo', 'age': 25, 'city': 'Stockholm'}\n\n"
            "# Access a value\n"
            "print(person['name'])         # Mo\n"
            "print(person.get('age'))      # 25 (safer, no crash if missing)\n\n"
            "# Add or update\n"
            "person['email'] = 'mo@example.com'\n\n"
            "# Delete\n"
            "del person['city']\n\n"
            "# Loop through\n"
            "for key, value in person.items():\n"
            "    print(f'{key}: {value}')\n\n"
            "# Check if key exists\n"
            "if 'name' in person:\n"
            "    print('Name found!')\n"
            "```"
        ),
    },
    {
        "keywords": [
            "merge dictionaries",
            "combine dicts",
            "merge dicts",
            "join dictionaries",
            "merge two dict",
        ],
        "response": (
            "Merge dictionaries in Python:\n\n"
            "```python\n"
            "dict1 = {'a': 1, 'b': 2}\n"
            "dict2 = {'c': 3, 'd': 4}\n\n"
            "# Python 3.9+ (cleanest)\n"
            "merged = dict1 | dict2\n\n"
            "# All Python 3 versions\n"
            "merged = {**dict1, **dict2}\n\n"
            "print(merged)  # {'a': 1, 'b': 2, 'c': 3, 'd': 4}\n"
            "```"
        ),
    },
    # ════════════════════════════════════════════════════════
    # CATEGORY 6: FILE OPERATIONS
    # ════════════════════════════════════════════════════════
    {
        "keywords": [
            "read a file",
            "read file",
            "open file",
            "load file",
            "read text file",
            "file reading",
        ],
        "response": (
            "Reading files in Python:\n\n"
            "```python\n"
            "# Read entire file at once\n"
            "with open('file.txt', 'r') as f:\n"
            "    content = f.read()\n\n"
            "# Read line by line (memory efficient for large files)\n"
            "with open('file.txt', 'r') as f:\n"
            "    for line in f:\n"
            "        print(line.strip())\n\n"
            "# Read all lines into a list\n"
            "with open('file.txt', 'r') as f:\n"
            "    lines = f.readlines()\n\n"
            "# Read a JSON file\n"
            "import json\n"
            "with open('data.json', 'r') as f:\n"
            "    data = json.load(f)\n"
            "```\n\n"
            "Always use `with open(...)` -- it closes the file automatically."
        ),
    },
    {
        "keywords": [
            "write a file",
            "write file",
            "save file",
            "write to file",
            "create file",
            "save to file",
        ],
        "response": (
            "Writing files in Python:\n\n"
            "```python\n"
            "# Write text (overwrites if file exists)\n"
            "with open('file.txt', 'w') as f:\n"
            "    f.write('Hello, World!')\n\n"
            "# Append to existing file\n"
            "with open('file.txt', 'a') as f:\n"
            "    f.write('\\nNew line added')\n\n"
            "# Write multiple lines\n"
            "lines = ['line 1', 'line 2', 'line 3']\n"
            "with open('file.txt', 'w') as f:\n"
            "    f.writelines('\\n'.join(lines))\n\n"
            "# Write a JSON file\n"
            "import json\n"
            "data = {'name': 'Mo', 'age': 25}\n"
            "with open('data.json', 'w') as f:\n"
            "    json.dump(data, f, indent=2)\n"
            "```"
        ),
    },
    # ════════════════════════════════════════════════════════
    # CATEGORY 7: ERROR HANDLING
    # ════════════════════════════════════════════════════════
    {
        "keywords": [
            "try except",
            "error handling",
            "exception handling",
            "catch error",
            "handle exception",
            "try catch",
        ],
        "response": (
            "Error handling in Python:\n\n"
            "```python\n"
            "# Basic try/except\n"
            "try:\n"
            "    result = 10 / 0\n"
            "except ZeroDivisionError:\n"
            "    print('Cannot divide by zero!')\n\n"
            "# Catch multiple exceptions\n"
            "try:\n"
            "    value = int(input('Enter a number: '))\n"
            "except ValueError:\n"
            "    print('That is not a number!')\n"
            "except KeyboardInterrupt:\n"
            "    print('User cancelled.')\n\n"
            "# else runs if no error, finally always runs\n"
            "try:\n"
            "    result = 10 / 2\n"
            "except ZeroDivisionError:\n"
            "    print('Error!')\n"
            "else:\n"
            "    print(f'Result: {result}')  # runs if no error\n"
            "finally:\n"
            "    print('Done.')              # always runs\n"
            "```"
        ),
    },
    # ════════════════════════════════════════════════════════
    # CATEGORY 8: FUNCTIONS & CLASSES
    # ════════════════════════════════════════════════════════
    {
        "keywords": [
            "what is a function",
            "how to write a function",
            "define a function",
            "create function",
            "python function",
        ],
        "response": (
            "Functions in Python:\n\n"
            "```python\n"
            "# Basic function\n"
            "def greet(name):\n"
            "    return f'Hello, {name}!'\n\n"
            "print(greet('Mo'))  # Hello, Mo!\n\n"
            "# Function with default argument\n"
            "def greet(name, greeting='Hello'):\n"
            "    return f'{greeting}, {name}!'\n\n"
            "# Function with multiple return values\n"
            "def min_max(numbers):\n"
            "    return min(numbers), max(numbers)\n\n"
            "low, high = min_max([3, 1, 4, 1, 5])\n"
            "```"
        ),
    },
    {
        "keywords": [
            "what is a class",
            "how to write a class",
            "define a class",
            "create class",
            "python class",
            "oop",
        ],
        "response": (
            "Classes in Python (Object-Oriented Programming):\n\n"
            "```python\n"
            "class Dog:\n"
            "    # __init__ runs when you create a new Dog\n"
            "    def __init__(self, name, age):\n"
            "        self.name = name  # store on the object\n"
            "        self.age  = age\n\n"
            "    def bark(self):\n"
            "        return f'{self.name} says: Woof!'\n\n"
            "    def __str__(self):\n"
            "        return f'Dog({self.name}, {self.age} years)'\n\n"
            "# Create objects from the class\n"
            "dog1 = Dog('Rex', 3)\n"
            "dog2 = Dog('Buddy', 5)\n\n"
            "print(dog1.bark())  # Rex says: Woof!\n"
            "print(dog2.name)    # Buddy\n"
            "```"
        ),
    },
    # ════════════════════════════════════════════════════════
    # CATEGORY 9: LOOPS & COMPREHENSIONS
    # ════════════════════════════════════════════════════════
    {
        "keywords": [
            "list comprehension",
            "list comp",
            "one line list",
            "compact list",
        ],
        "response": (
            "List comprehensions -- a compact way to build lists:\n\n"
            "```python\n"
            "# Standard loop\n"
            "squares = []\n"
            "for x in range(10):\n"
            "    squares.append(x ** 2)\n\n"
            "# Same thing as a list comprehension\n"
            "squares = [x ** 2 for x in range(10)]\n\n"
            "# With a condition (filter)\n"
            "evens = [x for x in range(20) if x % 2 == 0]\n\n"
            "# Transform strings\n"
            "names  = ['alice', 'bob', 'charlie']\n"
            "upper  = [name.upper() for name in names]\n\n"
            "# Dictionary comprehension (same idea)\n"
            "squared = {x: x**2 for x in range(5)}\n"
            "# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}\n"
            "```"
        ),
    },
    {
        "keywords": [
            "enumerate",
            "loop with index",
            "index in loop",
            "for loop index",
            "numbered loop",
        ],
        "response": (
            "Loop with index using enumerate:\n\n"
            "```python\n"
            "names = ['Alice', 'Bob', 'Charlie']\n\n"
            "# Without enumerate (old way)\n"
            "for i in range(len(names)):\n"
            "    print(i, names[i])\n\n"
            "# With enumerate (Pythonic way)\n"
            "for i, name in enumerate(names):\n"
            "    print(i, name)\n\n"
            "# Start counting from 1\n"
            "for i, name in enumerate(names, start=1):\n"
            "    print(f'{i}. {name}')\n"
            "# 1. Alice\n"
            "# 2. Bob\n"
            "# 3. Charlie\n"
            "```"
        ),
    },
    # ════════════════════════════════════════════════════════
    # CATEGORY 10: API REQUESTS
    # ════════════════════════════════════════════════════════
    {
        "keywords": [
            "how to call an api",
            "api request",
            "requests library",
            "http request",
            "get request",
            "post request",
            "rest api",
        ],
        "response": (
            "Making API requests in Python using the `requests` library:\n\n"
            "```python\n"
            "import requests\n\n"
            "# GET request (fetch data)\n"
            "response = requests.get('https://api.example.com/data')\n"
            "print(response.status_code)  # 200 means success\n"
            "data = response.json()        # parse JSON response\n\n"
            "# GET with parameters\n"
            "params = {'page': 1, 'limit': 10}\n"
            "response = requests.get('https://api.example.com/items', params=params)\n\n"
            "# POST request (send data)\n"
            "payload = {'name': 'Mo', 'message': 'Hello'}\n"
            "response = requests.post('https://api.example.com/send', json=payload)\n\n"
            "# With headers (e.g. API key)\n"
            "headers = {'Authorization': 'Bearer YOUR_TOKEN'}\n"
            "response = requests.get('https://api.example.com/secure', headers=headers)\n"
            "```\n\n"
            "Install with: `pip install requests`"
        ),
    },
    # ════════════════════════════════════════════════════════
    # CATEGORY 11: ALGORITHMS
    # ════════════════════════════════════════════════════════
    {
        "keywords": [
            "fibonacci",
            "fibonacci sequence",
            "fibonacci number",
            "fib sequence",
            "fibonacci series",
        ],
        "response": (
            "Fibonacci sequence in Python:\n\n"
            "```python\n"
            "# Method 1: simple loop\n"
            "def fibonacci(n):\n"
            "    a, b = 0, 1\n"
            "    for _ in range(n):\n"
            "        print(a, end=' ')\n"
            "        a, b = b, a + b\n\n"
            "fibonacci(10)  # 0 1 1 2 3 5 8 13 21 34\n\n"
            "# Method 2: return nth number\n"
            "def fib(n):\n"
            "    a, b = 0, 1\n"
            "    for _ in range(n):\n"
            "        a, b = b, a + b\n"
            "    return a\n\n"
            "print(fib(10))  # 55\n"
            "```"
        ),
    },
    {
        "keywords": [
            "factorial",
            "factorial function",
            "n factorial",
            "calculate factorial",
        ],
        "response": (
            "Factorial in Python:\n\n"
            "```python\n"
            "# Method 1: loop\n"
            "def factorial(n):\n"
            "    result = 1\n"
            "    for i in range(2, n + 1):\n"
            "        result *= i\n"
            "    return result\n\n"
            "# Method 2: recursion\n"
            "def factorial(n):\n"
            "    if n <= 1:\n"
            "        return 1\n"
            "    return n * factorial(n - 1)\n\n"
            "# Method 3: built-in\n"
            "import math\n"
            "print(math.factorial(5))  # 120\n"
            "```"
        ),
    },
    {
        "keywords": [
            "binary search",
            "search algorithm",
            "search in list",
            "find in sorted",
        ],
        "response": (
            "Binary search in Python:\n\n"
            "```python\n"
            "def binary_search(arr, target):\n"
            "    left, right = 0, len(arr) - 1\n\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n\n"
            "        if arr[mid] == target:\n"
            "            return mid       # found at index mid\n"
            "        elif arr[mid] < target:\n"
            "            left = mid + 1   # search right half\n"
            "        else:\n"
            "            right = mid - 1  # search left half\n\n"
            "    return -1  # not found\n\n"
            "numbers = [1, 3, 5, 7, 9, 11, 13]\n"
            "print(binary_search(numbers, 7))   # 3 (index)\n"
            "print(binary_search(numbers, 6))   # -1 (not found)\n"
            "```\n\n"
            "Note: the list must be sorted for binary search to work."
        ),
    },
    {
        "keywords": [
            "bubble sort",
            "insertion sort",
            "selection sort",
            "sorting algorithm",
            "implement sort",
        ],
        "response": (
            "Common sorting algorithms in Python:\n\n"
            "```python\n"
            "# Bubble sort\n"
            "def bubble_sort(arr):\n"
            "    n = len(arr)\n"
            "    for i in range(n):\n"
            "        for j in range(0, n - i - 1):\n"
            "            if arr[j] > arr[j + 1]:\n"
            "                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n"
            "    return arr\n\n"
            "# Insertion sort\n"
            "def insertion_sort(arr):\n"
            "    for i in range(1, len(arr)):\n"
            "        key = arr[i]\n"
            "        j = i - 1\n"
            "        while j >= 0 and arr[j] > key:\n"
            "            arr[j + 1] = arr[j]\n"
            "            j -= 1\n"
            "        arr[j + 1] = key\n"
            "    return arr\n\n"
            "nums = [64, 34, 25, 12, 22]\n"
            "print(bubble_sort(nums))     # [12, 22, 25, 34, 64]\n"
            "```\n\n"
            "In real projects, always use Python's built-in `sorted()` -- "
            "it uses Timsort and is much faster."
        ),
    },
    # ════════════════════════════════════════════════════════
    # CATEGORY 12: TERMINAL & ENVIRONMENT
    # ════════════════════════════════════════════════════════
    {
        "keywords": [
            "how to run python",
            "run a python file",
            "run python script",
            "execute python",
            "python command",
            "how to execute",
        ],
        "response": (
            "How to run a Python file from the terminal:\n\n"
            "```bash\n"
            "# Run a script\n"
            "python main.py\n\n"
            "# Run with Python 3 explicitly (some systems need this)\n"
            "python3 main.py\n\n"
            "# Run a module directly\n"
            "python -m mymodule\n\n"
            "# Check which Python version you have\n"
            "python --version\n"
            "```\n\n"
            "Make sure you are in the same folder as your file first: `cd your-folder`"
        ),
    },
    {
        "keywords": [
            "how to install",
            "pip install",
            "install package",
            "install library",
            "install module",
            "how to add package",
        ],
        "response": (
            "Installing Python packages with pip:\n\n"
            "```bash\n"
            "# Install a package\n"
            "pip install requests\n\n"
            "# Install a specific version\n"
            "pip install requests==2.31.0\n\n"
            "# Install all packages from a requirements file\n"
            "pip install -r requirements.txt\n\n"
            "# Upgrade an existing package\n"
            "pip install --upgrade requests\n\n"
            "# List all installed packages\n"
            "pip list\n\n"
            "# Save your installed packages to a file\n"
            "pip freeze > requirements.txt\n"
            "```"
        ),
    },
    {
        "keywords": [
            "virtual environment",
            "venv",
            "virtualenv",
            "create venv",
            "activate venv",
            "python environment",
        ],
        "response": (
            "Virtual environments keep your project dependencies isolated:\n\n"
            "```bash\n"
            "# Create a virtual environment\n"
            "python -m venv venv\n\n"
            "# Activate it (Windows)\n"
            "venv\\Scripts\\activate\n\n"
            "# Activate it (Mac / Linux)\n"
            "source venv/bin/activate\n\n"
            "# You will see (venv) in your terminal -- it is active\n\n"
            "# Install packages inside it\n"
            "pip install requests\n\n"
            "# Deactivate when done\n"
            "deactivate\n"
            "```\n\n"
            "Always activate your venv before running your project."
        ),
    },
    {
        "keywords": [
            "check python version",
            "python version",
            "which python",
            "what version",
            "python --version",
        ],
        "response": (
            "Check your Python and pip versions:\n\n"
            "```bash\n"
            "python --version      # e.g. Python 3.11.4\n"
            "python3 --version     # on Mac / Linux\n\n"
            "pip --version         # e.g. pip 23.2.1\n\n"
            "# See where Python is installed\n"
            "where python          # Windows\n"
            "which python3         # Mac / Linux\n"
            "```"
        ),
    },
    {
        "keywords": [
            "requirements.txt",
            "requirements file",
            "how to share dependencies",
            "project dependencies",
        ],
        "response": (
            "Using requirements.txt to share project dependencies:\n\n"
            "```bash\n"
            "# Save all your current packages to the file\n"
            "pip freeze > requirements.txt\n\n"
            "# Install everything from the file (e.g. on a new machine)\n"
            "pip install -r requirements.txt\n"
            "```\n\n"
            "Example `requirements.txt`:\n"
            "```\n"
            "requests==2.31.0\n"
            "python-dotenv==1.0.0\n"
            "```\n\n"
            "Always include this file in your project so others can set up easily."
        ),
    },
    {
        "keywords": [
            "environment variable",
            "env variable",
            "dotenv",
            "how to use .env",
            "load env",
            "os.getenv",
            "os.environ",
        ],
        "response": (
            "Using environment variables to store secrets safely:\n\n"
            "```bash\n"
            "# Create a .env file in your project folder\n"
            "# .env\n"
            "API_KEY=your-secret-key-here\n"
            "DATABASE_URL=postgresql://localhost/mydb\n"
            "```\n\n"
            "```python\n"
            "# Read it in Python with python-dotenv\n"
            "from dotenv import load_dotenv\n"
            "import os\n\n"
            "load_dotenv()  # reads the .env file\n\n"
            "api_key = os.getenv('API_KEY')\n"
            "db_url  = os.getenv('DATABASE_URL')\n"
            "```\n\n"
            "Install with: `pip install python-dotenv`\n\n"
            "IMPORTANT: Always add `.env` to your `.gitignore` -- never commit secrets."
        ),
    },
    {
        "keywords": [
            "gitignore",
            ".gitignore",
            "what to ignore",
            "ignore files git",
            "git ignore",
        ],
        "response": (
            "A `.gitignore` file tells git which files NOT to commit.\n\n"
            "Standard Python `.gitignore`:\n"
            "```\n"
            "# Secrets -- never commit these\n"
            ".env\n\n"
            "# Virtual environment\n"
            "venv/\n"
            ".venv/\n\n"
            "# Python cache\n"
            "__pycache__/\n"
            "*.pyc\n"
            "*.pyo\n\n"
            "# IDE files\n"
            ".vscode/\n"
            ".idea/\n\n"
            "# Logs\n"
            "logs/\n"
            "*.log\n"
            "```\n\n"
            "Create this file in the root of your project before your first `git commit`."
        ),
    },
]


# ─── FIND TEMPLATE ──────────────────────────────────────────
# Called from agent.py before every Claude API call.
# Checks if the message matches any template.
# Returns the response string if found, or None if no match.


def find_template(content):
    """
    Check if a message matches any pre-written template.

    content : the message text to check (lowercased internally)

    Returns:
        str  -> the pre-written response if a keyword matched
        None -> no match, caller should fall through to Claude
    """
    content_lower = content.lower()

    for template in TEMPLATES:
        if any(keyword in content_lower for keyword in template["keywords"]):
            return template["response"]

    return None
