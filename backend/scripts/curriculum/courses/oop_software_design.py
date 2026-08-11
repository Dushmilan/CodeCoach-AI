"""Object-Oriented Programming and Software Design — curriculum content module."""

COURSE = {
    "id": "oop-software-design",
    "title": "Object-Oriented Programming and Software Design",
    "description": (
        "Learn how to design reliable, maintainable software. Cover classes and "
        "encapsulation, composition and inheritance, polymorphism and abstraction, "
        "core design principles such as SOLID, and a hands-on refactoring project. "
        "Concepts are taught in Python but apply to any object-oriented language."
    ),
    "language": "python",
    "icon": "layers",
    "order": 13,
}

MODULES = [
    {
        "id": "oop-classes",
        "course_id": "oop-software-design",
        "title": "Classes and Encapsulation",
        "description": "Model real-world things with objects: state, behavior, constructors, and controlling access to data.",
        "order": 1,
    },
    {
        "id": "oop-inheritance",
        "course_id": "oop-software-design",
        "title": "Composition and Inheritance",
        "description": "Reuse code cleanly by understanding inheritance, method overriding, abstract contracts, and when composition beats inheritance.",
        "order": 2,
    },
    {
        "id": "oop-polymorphism",
        "course_id": "oop-software-design",
        "title": "Polymorphism and Abstraction",
        "description": "Write code that works with many shapes of object: method overrides, duck typing, and programming against abstractions.",
        "order": 3,
    },
    {
        "id": "oop-principles",
        "course_id": "oop-software-design",
        "title": "Design Principles",
        "description": "Apply SOLID, keep modules cohesive and loosely coupled, and recognize the strategy, factory, and observer patterns.",
        "order": 4,
    },
    {
        "id": "oop-refactor",
        "course_id": "oop-software-design",
        "title": "Refactoring Project",
        "description": "Turn a procedural script into clean, testable object-oriented modules by spotting smells and refactoring step by step.",
        "order": 5,
    },
]

_PY = "python"


def L(**kw):
    kw.setdefault("language", _PY)
    return kw


LESSONS = [
    # ── Module 1: Classes and Encapsulation ─────────────────────────────
    L(
        id="oop-classes-objects",
        course_id="oop-software-design",
        module_id="oop-classes",
        title="Objects, State, and Behavior",
        type="theory",
        order=1,
        content="""## Objects, State, and Behavior

Object-oriented programming (OOP) models a program as a collection of **objects**. An object bundles two things:

- **State** — the data the object holds (its *attributes* or *fields*).
- **Behavior** — the operations the object can perform (its *methods*).

A **class** is the blueprint; an **object** is a concrete instance of that blueprint.

```python
class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def describe(self):
        return f"{self.name} is {self.age} years old"
```

Creating an object instantiates the class:

```python
milo = Dog("Milo", 3)
print(milo.describe())   # Milo is 3 years old
```

`milo` is an object of type `Dog`. It has its own `name` and `age`, separate from any other `Dog` you create.

### Why objects?

| Procedural thinking            | Object thinking                    |
|--------------------------------|------------------------------------|
| Data and functions are separate | Data and its behavior live together |
| Functions operate on globals    | Methods operate on their own state  |
| Caller must track every piece   | Each object manages its own data    |

Objects reduce the amount of information you must keep in your head at once: the object guarantees its own invariants, and callers only work with its public methods.

---

**Next up:** constructors — how objects get their initial state."""
    ),
    L(
        id="oop-classes-constructors",
        course_id="oop-software-design",
        module_id="oop-classes",
        title="Constructors and `__init__`",
        type="theory",
        order=2,
        content="""## Constructors and `__init__`

A **constructor** sets up a new object's initial state. In Python the constructor is the special method `__init__`, which Python calls automatically right after an object is created.

```python
class Account:
    def __init__(self, owner, balance):
        self.owner = owner
        self.balance = balance
```

```python
acc = Account("Ada", 100)
print(acc.owner)    # Ada
print(acc.balance)  # 100
```

### Defaults in constructors

Constructor parameters can have defaults so callers can omit them:

```python
class Timer:
    def __init__(self, seconds=0):
        self.seconds = seconds

t = Timer()        # seconds = 0
t2 = Timer(60)     # seconds = 60
```

### Validating in the constructor

The constructor is the right place to enforce invariants — rules that must always hold:

```python
class BankAccount:
    def __init__(self, owner, balance):
        if balance < 0:
            raise ValueError("balance cannot be negative")
        self.owner = owner
        self.balance = balance
```

Failing fast in `__init__` prevents an object from ever existing in an invalid state, which removes whole classes of bugs downstream.

### The `self` parameter

The first parameter of every instance method, conventionally named `self`, refers to the object being operated on. Python passes it automatically:

```python
acc.deposit(50)      # Python calls Account.deposit(acc, 50)
```

---

**Next up:** encapsulation — controlling access to an object's data."""
    ),
    L(
        id="oop-classes-encapsulation",
        course_id="oop-software-design",
        module_id="oop-classes",
        title="Encapsulation and Access Control",
        type="theory",
        order=3,
        content="""## Encapsulation and Access Control

**Encapsulation** is the practice of hiding an object's internal details and only exposing a controlled interface. The object's state should only change through its methods, so the object can keep its own data consistent.

Python has no hard `private` keyword, but conventions communicate intent:

| Convention  | Meaning                                        |
|-------------|------------------------------------------------|
| `name`      | Public attribute — safe to use externally      |
| `_name`     | Protected — internal by convention             |
| `__name`    | Name-mangled — discouraged to touch outside    |

```python
class Thermostat:
    def __init__(self, target=21):
        self._target = target
        self._running = False

    def turn_on(self):
        self._running = True

    def set_target(self, value):
        if 5 <= value <= 35:
            self._target = value
```

The `_target` and `_running` attributes are *internal*. Outside code calls `turn_on()` and `set_target()` instead of poking the fields directly, so invalid values like `set_target(100)` are rejected.

### Why hide internals?

1. **Protection** — callers cannot break invariants.
2. **Freedom to change** — the internal representation can change without breaking callers.
3. **Clarity** — the public methods document the intended use.

### Methods that mutate vs methods that report

Keep a clear split between methods that change state and methods that only read it:

```python
def deposit(self, amount):      # mutates
    self._balance += amount

def balance(self):              # reports
    return self._balance
```

Encapsulation is the first line of defense for reliable software: data stays consistent because nobody can reach around the interface.

---

**Next up:** making objects readable with `__str__` and friends."""
    ),
    L(
        id="oop-classes-magic-methods",
        course_id="oop-software-design",
        module_id="oop-classes",
        title="Magic Methods: `__str__`, `__repr__`, and More",
        type="theory",
        order=4,
        content="""## Magic Methods: `__str__`, `__repr__`, and More

Python lets classes customize how they behave with built-in operations through **magic methods** (double-underscore methods). They are never called by name directly — Python invokes them behind the scenes.

### Human-readable output: `__str__`

```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Point({self.x}, {self.y})"

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
```

```python
p1 = Point(1, 2)
p2 = Point(3, 4)
print(p1)        # Point(1, 2)  — uses __str__
print(p1 + p2)   # Point(4, 6)  — uses __add__
```

### Common magic methods

| Method     | Trigger               | Purpose                          |
|------------|-----------------------|----------------------------------|
| `__init__` | `MyClass(...)`        | Build initial state              |
| `__str__`  | `str(obj)`, `print()` | Friendly, human-readable string  |
| `__repr__` | `repr(obj)`           | Unambiguous string for developers|
| `__len__`  | `len(obj)`            | Return a length                  |
| `__eq__`   | `a == b`              | Define value equality            |
| `__lt__`   | `a < b`               | Define ordering                  |

### A readable object is a debuggable object

Implementing `__str__` turns a cryptic `<__main__.Account object at 0x7f...>` into `Account(Ada, 100)`. That pays off every single time you inspect an object while debugging.

```python
class Account:
    def __init__(self, owner, balance):
        self.owner = owner
        self.balance = balance

    def __str__(self):
        return f"Account({self.owner}, {self.balance})"
```

---

**Next up:** your first exercises — a Rectangle class, a BankAccount, and a Stack."""
    ),
    L(
        id="oop-classes-exercise-rectangle",
        course_id="oop-software-design",
        module_id="oop-classes",
        title="Exercise: Rectangle Class",
        type="exercise",
        order=5,
        content="""## Exercise: Rectangle Class

Write a class `Rectangle` with:

- `__init__(width, height)` storing both dimensions.
- `area()` returning `width * height`.
- `perimeter()` returning `2 * (width + height)`.

Then write `solve(w, h)` that builds a `Rectangle(w, h)` and returns the string `"{area} {perimeter}"`.

### Sample

Input:

```text
3
4
```

Output:

```text
12 14
```

### How your code runs

The harness calls `solve(w, h)` with the two numbers. `solve` creates the object and returns a single string. Note that the instance parameter of the methods is named `_self` — Python lets you call it anything; the sandbox uses `_self` so the method signatures stay stable when wrapped.

### Starter code

```python
def solve(w, h):
    rect = Rectangle(w, h)
    return f"{rect.area()} {rect.perimeter()}"

class Rectangle:
    def __init__(_self, width, height):
        _self.width = width
        _self.height = height

    def area(_self):
        return _self.width * _self.height

    def perimeter(_self):
        return 2 * (_self.width + _self.height)

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    w = int(lines[0].strip())
    h = int(lines[1].strip())
    print(solve(w, h))

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(w, h):
    rect = Rectangle(w, h)
    return f"{rect.area()} {rect.perimeter()}"

class Rectangle:
    def __init__(_self, width, height):
        _self.width = width
        _self.height = height

    def area(_self):
        return _self.width * _self.height

    def perimeter(_self):
        return 2 * (_self.width + _self.height)

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    w = int(lines[0].strip())
    h = int(lines[1].strip())
    print(solve(w, h))

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "3\n4", "expected_output": "12 14", "description": "3 by 4 rectangle"},
            {"input": "5\n6", "expected_output": "30 22", "description": "5 by 6 rectangle"},
            {"input": "1\n1", "expected_output": "1 4", "description": "Unit square"},
            {"input": "10\n2", "expected_output": "20 24", "description": "Wide rectangle"},
        ],
    ),
    L(
        id="oop-classes-exercise-bank-account",
        course_id="oop-software-design",
        module_id="oop-classes",
        title="Exercise: Bank Account Simulation",
        type="exercise",
        order=6,
        content="""## Exercise: Bank Account Simulation

Write a class `BankAccount` with:

- `__init__(owner, balance)` storing both.
- `deposit(amount)` adding to the balance.
- `withdraw(amount)` removing from the balance **only if enough funds exist**; otherwise it must leave the balance unchanged.

Then write `solve(account)` that receives a JSON object describing an account and a list of operations, and returns the final balance.

```json
{"owner": "Ada", "balance": 100, "operations": [["deposit", 50], ["withdraw", 30]]}
```

### Sample

Input (one line):

```text
{"owner":"Ada","balance":100,"operations":[["deposit",50],["withdraw",30]]}
```

Output:

```text
120
```

### How your code runs

The harness parses the JSON object and calls `solve(account)`. Inside `solve`, build a `BankAccount` and apply every `[op, amount]` pair.

### Starter code

```python
def solve(account):
    acc = BankAccount(account["owner"], account["balance"])
    for op, amount in account["operations"]:
        if op == "deposit":
            acc.deposit(amount)
        elif op == "withdraw":
            acc.withdraw(amount)
    return acc.balance

class BankAccount:
    def __init__(_self, owner, balance):
        _self.owner = owner
        _self.balance = balance

    def deposit(_self, amount):
        _self.balance += amount

    def withdraw(_self, amount):
        if amount <= _self.balance:
            _self.balance -= amount

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    account = json.loads(data)
    print(solve(account))

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(account):
    acc = BankAccount(account["owner"], account["balance"])
    for op, amount in account["operations"]:
        if op == "deposit":
            acc.deposit(amount)
        elif op == "withdraw":
            acc.withdraw(amount)
    return acc.balance

class BankAccount:
    def __init__(_self, owner, balance):
        _self.owner = owner
        _self.balance = balance

    def deposit(_self, amount):
        _self.balance += amount

    def withdraw(_self, amount):
        if amount <= _self.balance:
            _self.balance -= amount

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    account = json.loads(data)
    print(solve(account))

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '{"owner":"Ada","balance":100,"operations":[["deposit",50],["withdraw",30]]}', "expected_output": "120", "description": "Deposit then withdraw"},
            {"input": '{"owner":"Bob","balance":10,"operations":[["withdraw",20]]}', "expected_output": "10", "description": "Withdraw refused when overdrawn"},
            {"input": '{"owner":"Cy","balance":0,"operations":[["deposit",100],["deposit",50]]}', "expected_output": "150", "description": "Two deposits"},
            {"input": '{"owner":"Dan","balance":500,"operations":[["withdraw",500]]}', "expected_output": "0", "description": "Exact balance withdrawal"},
        ],
    ),
    L(
        id="oop-classes-exercise-stack",
        course_id="oop-software-design",
        module_id="oop-classes",
        title="Exercise: Stack Class",
        type="exercise",
        order=7,
        content="""## Exercise: Stack Class

Write a class `Stack` implementing a last-in-first-out container:

- `push(value)` — add a value on top.
- `pop()` — remove and discard the top value (ignore if empty).
- `peek()` — return the top value without removing it.

Then write `solve(commands)` that receives a JSON list of commands such as `[["push",5],["push",7],["pop"]]` and returns the stack contents from **bottom to top** as a list.

### Sample

Input (one line):

```text
[["push",5],["push",7],["pop"]]
```

Output:

```text
[5]
```

### How your code runs

The harness parses the JSON array and calls `solve(commands)`. Process each `["push", value]` or `["pop"]` entry, then return the current stack contents.

### Starter code

```python
def solve(commands):
    stack = Stack()
    for command in commands:
        if command[0] == "push":
            stack.push(command[1])
        elif command[0] == "pop":
            stack.pop()
    return stack.items

class Stack:
    def __init__(_self):
        _self.items = []

    def push(_self, value):
        _self.items.append(value)

    def pop(_self):
        if _self.items:
            _self.items.pop()

    def peek(_self):
        if _self.items:
            return _self.items[-1]
        return None

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    commands = json.loads(data)
    print(json.dumps(solve(commands), separators=(",", ":")))

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(commands):
    stack = Stack()
    for command in commands:
        if command[0] == "push":
            stack.push(command[1])
        elif command[0] == "pop":
            stack.pop()
    return stack.items

class Stack:
    def __init__(_self):
        _self.items = []

    def push(_self, value):
        _self.items.append(value)

    def pop(_self):
        if _self.items:
            _self.items.pop()

    def peek(_self):
        if _self.items:
            return _self.items[-1]
        return None

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    commands = json.loads(data)
    print(json.dumps(solve(commands), separators=(",", ":")))

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '[["push",5],["push",7],["pop"]]', "expected_output": "[5]", "description": "Push push pop"},
            {"input": '[["push",1],["push",2],["push",3]]', "expected_output": "[1,2,3]", "description": "Three pushes"},
            {"input": '[["pop"],["push",9]]', "expected_output": "[9]", "description": "Pop from empty then push"},
            {"input": '[["push",4],["pop"],["pop"]]', "expected_output": "[]", "description": "Push then pop everything"},
        ],
    ),
    # ── Module 2: Composition and Inheritance ────────────────────────────
    L(
        id="oop-inheritance-reuse",
        course_id="oop-software-design",
        module_id="oop-inheritance",
        title="Code Reuse Through Inheritance",
        type="theory",
        order=1,
        content="""## Code Reuse Through Inheritance

**Inheritance** lets a new class (the *subclass*) reuse the behavior of an existing class (the *superclass*). The subclass automatically gets the superclass's methods and attributes, then adds or changes what it needs.

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "..."

class Dog(Animal):
    def speak(self):
        return "Woof!"
```

`Dog` inherits `__init__` and the `name` attribute, but overrides `speak`:

```python
d = Dog("Milo")
print(d.name)      # Milo   (inherited)
print(d.speak())   # Woof!  (overridden)
```

### The "is-a" test

Use inheritance when the relationship is truly **is-a**: a `Dog` *is an* `Animal`. Before subclassing, ask whether the subclass is genuinely a special case of the superclass.

### What gets reused

- **Attributes** — `self.name` works in `Dog` without redefining it.
- **Methods** — any method not overridden is inherited as-is.
- **Constructors** — if the subclass defines no `__init__`, it inherits the parent's.

```python
class LoudDog(Dog):
    def speak(self):
        return "WOOF! WOOF!"

print(LoudDog("Rex").name)    # Rex — inherited all the way down
```

Inheritance is the most direct form of code reuse: write behavior once in the base class, and every subclass benefits.

---

**Next up:** overriding methods and calling `super()`."""
    ),
    L(
        id="oop-inheritance-override",
        course_id="oop-software-design",
        module_id="oop-inheritance",
        title="Overriding Methods and `super()`",
        type="theory",
        order=2,
        content="""## Overriding Methods and `super()`

A subclass often needs the parent's behavior *plus* something extra. **Overriding** a method means redefining it in the subclass; calling `super()` runs the parent's version.

```python
class Employee:
    def __init__(self, name, salary):
        self.name = name
        self.salary = salary

    def monthly_pay(self):
        return self.salary / 12

class Manager(Employee):
    def __init__(self, name, salary, bonus):
        super().__init__(name, salary)
        self.bonus = bonus

    def monthly_pay(self):
        return super().monthly_pay() + self.bonus
```

```python
m = Manager("Ada", 120000, 500)
print(m.monthly_pay())   # 10500.0  (base pay plus bonus)
```

### Why call `super()`?

Without `super().__init__(name, salary)`, `Manager` would have to re-implement the base constructor — duplicating logic and risking drift. `super()` keeps the reuse explicit.

### Extend, don't destroy

A well-behaved override either:

- Replaces the behavior entirely (no `super()` call), or
- Extends it: runs `super()` first, then adds its own logic.

```python
class SecureEmployee(Employee):
    def __init__(self, name, salary, clearance):
        super().__init__(name, salary)
        self.clearance = clearance
```

### Overriding rules

- The subclass method signature should stay compatible with the parent's.
- Callers should not be able to tell (or care) which version runs.
- If the base method returns a value, the override should return a compatible value.

---

**Next up:** interfaces and abstract classes — contracts your code can rely on."""
    ),
    L(
        id="oop-inheritance-abstract",
        course_id="oop-software-design",
        module_id="oop-inheritance",
        title="Interfaces and Abstract Classes",
        type="theory",
        order=3,
        content="""## Interfaces and Abstract Classes

Sometimes a base class should define **what** a subclass must do without implementing **how**. That's the role of interfaces and abstract classes.

### Abstract classes

An abstract class cannot be instantiated directly — it exists to be inherited. Methods decorated with `@abstractmethod` must be implemented by every subclass.

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return 3.14159 * self.radius ** 2
```

`Shape` declares the contract: every shape must have an `area()` method. `Circle` fulfills it.

### The contract guarantees

Because every subclass of `Shape` must implement `area()`, code that works with `Shape` is guaranteed to work with any future shape — a `Triangle`, a `Hexagon`, anything.

### Interfaces in Python

Python has no separate `interface` keyword. An interface is usually just an abstract class with no state, or an informal set of methods expected by convention ("duck typing", coming soon).

```python
class Drawable(ABC):
    @abstractmethod
    def draw(self):
        pass
```

### Abstract vs concrete base

|                     | Abstract base class            | Concrete base class      |
|---------------------|--------------------------------|--------------------------|
| Instantiable?       | No                             | Yes                      |
| Implements methods  | Some or none                   | Fully implements them    |
| Purpose             | Define a contract for subclasses | Provide ready-to-use shared code |

A good rule of thumb: if a base class is only ever used as a parent, consider making it abstract so its contract is explicit.

---

**Next up:** composition — building objects from other objects, and when it beats inheritance."""
    ),
    L(
        id="oop-inheritance-composition",
        course_id="oop-software-design",
        module_id="oop-inheritance",
        title="Composition vs Inheritance Tradeoffs",
        type="theory",
        order=4,
        content="""## Composition vs Inheritance Tradeoffs

**Composition** builds objects out of other objects. Instead of a class *being* something, it *has* something:

```python
class Book:
    def __init__(self, title, pages):
        self.title = title
        self.pages = pages

class Library:
    def __init__(self, name):
        self.name = name
        self.books = []

    def add_book(self, book):
        self.books.append(book)

    def total_pages(self):
        return sum(book.pages for book in self.books)
```

A `Library` **has** books. That is composition: delegation through contained objects.

### Inheritance: is-a vs has-a

| Relationship | Wording                | Python                    |
|--------------|------------------------|---------------------------|
| Inheritance  | Dog **is a** Animal    | `class Dog(Animal)`       |
| Composition  | Library **has** Books  | `self.books = []`         |

### When to prefer composition

- The relationship is "has a", not "is a".
- You need flexibility: swap the contained object at runtime.
- Inheritance would create deep, fragile chains.
- You want to reuse behavior without taking on the parent's whole identity.

### When inheritance still wins

- True "is-a" modeling where subclasses genuinely extend the base.
- Shared attributes and methods that every subclass needs.
- Frameworks that expect you to override lifecycle methods.

### Favor composition by default

Composition is more flexible and less brittle: changing a contained object never breaks the container's other behavior, whereas changing a base class's internals can ripple through every subclass.

```python
class Printer:
    def print_doc(self, doc):
        return f"printing {doc}"

class Computer:
    def __init__(self):
        self.printer = Printer()   # has-a

pc = Computer()
print(pc.printer.print_doc("report"))   # printing report
```

---

**Next up:** exercises — a shape hierarchy, talking animals, and a composed library."""
    ),
    L(
        id="oop-inheritance-exercise-shapes",
        course_id="oop-software-design",
        module_id="oop-inheritance",
        title="Exercise: Shape Hierarchy",
        type="exercise",
        order=5,
        content="""## Exercise: Shape Hierarchy

Build a small inheritance hierarchy:

- `Shape` — base class with `area()` returning `0`.
- `Circle(Shape)` — takes a `radius`; `area()` returns `3.14159 * radius ** 2` rounded to 2 decimals.
- `Rectangle(Shape)` — takes `width` and `height`; `area()` returns `width * height`.

Then write `solve(spec)` that receives a JSON object describing one shape and returns its area. The object looks like `{"type":"circle","radius":3}` or `{"type":"rectangle","width":3,"height":4}`.

### Sample

Input (one line):

```text
{"type":"circle","radius":3}
```

Output:

```text
28.27
```

### How your code runs

The harness parses the JSON object and calls `solve(spec)`. Inside `solve`, build the right shape via `make_shape(spec)` and return its `.area()`.

### Starter code

```python
def solve(spec):
    shape = make_shape(spec)
    return shape.area()

class Shape:
    def area(_self):
        return 0

class Circle(Shape):
    def __init__(_self, radius):
        _self.radius = radius

    def area(_self):
        return round(3.14159 * _self.radius ** 2, 2)

class Rectangle(Shape):
    def __init__(_self, width, height):
        _self.width = width
        _self.height = height

    def area(_self):
        return _self.width * _self.height

def make_shape(spec):
    if spec["type"] == "circle":
        return Circle(spec["radius"])
    return Rectangle(spec["width"], spec["height"])

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    spec = json.loads(data)
    print(solve(spec))

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(spec):
    shape = make_shape(spec)
    return shape.area()

class Shape:
    def area(_self):
        return 0

class Circle(Shape):
    def __init__(_self, radius):
        _self.radius = radius

    def area(_self):
        return round(3.14159 * _self.radius ** 2, 2)

class Rectangle(Shape):
    def __init__(_self, width, height):
        _self.width = width
        _self.height = height

    def area(_self):
        return _self.width * _self.height

def make_shape(spec):
    if spec["type"] == "circle":
        return Circle(spec["radius"])
    return Rectangle(spec["width"], spec["height"])

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    spec = json.loads(data)
    print(solve(spec))

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '{"type":"circle","radius":3}', "expected_output": "28.27", "description": "Circle of radius 3"},
            {"input": '{"type":"rectangle","width":3,"height":4}', "expected_output": "12", "description": "Rectangle 3x4"},
            {"input": '{"type":"circle","radius":1}', "expected_output": "3.14", "description": "Unit circle"},
            {"input": '{"type":"rectangle","width":5,"height":5}', "expected_output": "25", "description": "Square via rectangle"},
        ],
    ),
    L(
        id="oop-inheritance-exercise-animals",
        course_id="oop-software-design",
        module_id="oop-inheritance",
        title="Exercise: Talking Animals",
        type="exercise",
        order=6,
        content="""## Exercise: Talking Animals

Build an animal hierarchy:

- `Animal` — base class storing a `name`; `speak()` returns `"..."`.
- `Dog(Animal)` — `speak()` returns `"Woof!"`.
- `Cat(Animal)` — `speak()` returns `"Meow!"`.

Then write `solve(kind)` that receives a lowercase animal name and returns the sound that animal makes. Use a lookup such as `{"dog": Dog, "cat": Cat}` to pick the class.

### Sample

Input (one line):

```text
dog
```

Output:

```text
Woof!
```

### How your code runs

The harness passes the animal name as a single string. `solve` builds the correct animal and returns its `speak()` result.

### Starter code

```python
def solve(kind):
    animal = {"dog": Dog, "cat": Cat}.get(kind, Animal)("?")
    return animal.speak()

class Animal:
    def __init__(_self, name):
        _self.name = name

    def speak(_self):
        return "..."

class Dog(Animal):
    def speak(_self):
        return "Woof!"

class Cat(Animal):
    def speak(_self):
        return "Meow!"

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    print(solve(data))

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(kind):
    animal = {"dog": Dog, "cat": Cat}.get(kind, Animal)("?")
    return animal.speak()

class Animal:
    def __init__(_self, name):
        _self.name = name

    def speak(_self):
        return "..."

class Dog(Animal):
    def speak(_self):
        return "Woof!"

class Cat(Animal):
    def speak(_self):
        return "Meow!"

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    print(solve(data))

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "dog", "expected_output": "Woof!", "description": "A dog barks"},
            {"input": "cat", "expected_output": "Meow!", "description": "A cat meows"},
            {"input": "cow", "expected_output": "...", "description": "Unknown animal falls back"},
        ],
    ),
    L(
        id="oop-inheritance-exercise-library",
        course_id="oop-software-design",
        module_id="oop-inheritance",
        title="Exercise: Composing a Library",
        type="exercise",
        order=7,
        content="""## Exercise: Composing a Library

Practice composition with two classes:

- `Book(title, pages)` storing both.
- `Library(name)` with `add_book(book)` and `total_pages()` returning the sum of all books' pages.

Then write `solve(books)` that receives a JSON list of `[title, pages]` pairs, adds a `Book` for each to a `Library`, and returns the library's total pages.

### Sample

Input (one line):

```text
[["Clean Code", 464], ["Refactoring", 448]]
```

Output:

```text
912
```

### How your code runs

The harness parses the JSON array and calls `solve(books)`. Build the library, add the books, return `library.total_pages()`.

### Starter code

```python
def solve(books):
    library = Library("main")
    for title, pages in books:
        library.add_book(Book(title, pages))
    return library.total_pages()

class Book:
    def __init__(_self, title, pages):
        _self.title = title
        _self.pages = pages

class Library:
    def __init__(_self, name):
        _self.name = name
        _self.books = []

    def add_book(_self, book):
        _self.books.append(book)

    def total_pages(_self):
        return sum(book.pages for book in _self.books)

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    books = json.loads(data)
    print(solve(books))

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(books):
    library = Library("main")
    for title, pages in books:
        library.add_book(Book(title, pages))
    return library.total_pages()

class Book:
    def __init__(_self, title, pages):
        _self.title = title
        _self.pages = pages

class Library:
    def __init__(_self, name):
        _self.name = name
        _self.books = []

    def add_book(_self, book):
        _self.books.append(book)

    def total_pages(_self):
        return sum(book.pages for book in _self.books)

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    books = json.loads(data)
    print(solve(books))

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '[["Clean Code",464],["Refactoring",448]]', "expected_output": "912", "description": "Two books"},
            {"input": '[["Python Crash Course",624]]', "expected_output": "624", "description": "Single book"},
            {"input": "[]", "expected_output": "0", "description": "Empty library"},
            {"input": '[["A",10],["B",20],["C",30]]', "expected_output": "60", "description": "Three small books"},
        ],
    ),
    # ── Module 3: Polymorphism and Abstraction ──────────────────────────
    L(
        id="oop-poly-dispatch",
        course_id="oop-software-design",
        module_id="oop-polymorphism",
        title="Overrides and Dynamic Dispatch",
        type="theory",
        order=1,
        content="""## Overrides and Dynamic Dispatch

**Polymorphism** ("many forms") lets one name mean different things depending on the object's actual type. Thanks to **dynamic dispatch**, Python decides *at runtime* which method implementation to call.

```python
class Shape:
    def area(self):
        return 0

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return 3.14159 * self.radius ** 2

class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height
```

Now a single loop can handle every shape without caring about its concrete type:

```python
shapes = [Circle(3), Rectangle(2, 5), Circle(1)]

total = 0.0
for shape in shapes:          # each object is a Shape
    total += shape.area()     # dispatch picks the right area()
print(total)
```

### What makes it work

1. Every subclass guarantees the same method name (`area`).
2. The caller only relies on the base interface.
3. Python looks up the method on the **actual object**, not the declared type.

### The payoff

Adding a `Triangle` later requires **zero changes** to the loop. Polymorphism lets you write code that is open for extension — new types slot in without touching existing logic.

### Compare to type checks

```python
# Without polymorphism — you must handle every case yourself
if isinstance(shape, Circle):
    total += 3.14159 * shape.radius ** 2
elif isinstance(shape, Rectangle):
    total += shape.width * shape.height
```

Polymorphism moves that decision into the classes, where it belongs.

---

**Next up:** duck typing — when the interface is just a convention."""
    ),
    L(
        id="oop-poly-ducktyping",
        course_id="oop-software-design",
        module_id="oop-polymorphism",
        title="Duck Typing",
        type="theory",
        order=2,
        content="""## Duck Typing

"If it walks like a duck and quacks like a duck, it's a duck." Python applies this philosophy to objects: you don't need a formal base class for polymorphism. **If an object has the methods you call, it works.**

```python
class ConsoleLogger:
    def log(self, message):
        return f"console: {message}"

class FileLogger:
    def log(self, message):
        return f"file: {message}"

class NetworkLogger:
    def log(self, message):
        return f"network: {message}"
```

Any code that calls `.log(message)` works with all three — no inheritance required:

```python
def record(logger, message):
    return logger.log(message)

print(record(ConsoleLogger(), "start"))   # console: start
print(record(FileLogger(), "start"))      # file: start
```

### Duck typing in action

Python's built-ins are full of duck typing:

- `len(x)` works for anything with `__len__`.
- `for item in x` works for anything iterable.
- `f"{obj}"` works for anything with `__str__`.

```python
def total(items):
    return sum(items)

print(total([1, 2, 3]))       # list
print(total((4, 5, 6)))       # tuple
```

### Trust the interface, not the type

Duck typing encourages programming to the **behavior** an object exposes rather than its declared class. This is more flexible but places a responsibility on you: document and test the expected interface, because Python won't enforce it.

### EAFP — easier to ask forgiveness

Python idioms favor trying the operation and handling failure over pre-checking types:

```python
try:
    logger.log(msg)
except AttributeError:
    print("logger has no log() method")
```

---

**Next up:** programming to abstractions — depending on interfaces, not concrete details."""
    ),
    L(
        id="oop-poly-abstractions",
        course_id="oop-software-design",
        module_id="oop-polymorphism",
        title="Programming to Abstractions",
        type="theory",
        order=3,
        content="""## Programming to Abstractions

Good design programs against **abstractions** (interfaces) rather than **concretions** (specific implementations). You depend on *what* an object can do, not *which* implementation it is.

### The problem with concrete dependencies

```python
def notify_user(user, mode):
    if mode == "email":
        send_email(user.email, "Update")       # tightly coupled
    elif mode == "sms":
        send_sms(user.phone, "Update")
    elif mode == "push":
        send_push(user.device_id, "Update")
```

Every new channel means editing `notify_user`. The function knows too much.

### Programming to an abstraction

```python
class Notifier:
    def send(self, user, message):
        pass

class EmailNotifier(Notifier):
    def send(self, user, message):
        return f"email to {user.email}: {message}"

class SmsNotifier(Notifier):
    def send(self, user, message):
        return f"sms to {user.phone}: {message}"
```

The caller depends only on the `Notifier` contract:

```python
def notify_user(user, message, notifier):
    return notifier.send(user, message)   # any Notifier works
```

### Why it matters

- **Replaceability** — swap implementations without touching callers.
- **Testability** — inject a fake notifier in tests.
- **Extensibility** — add new implementations without editing old code.

### Three rules of thumb

1. Name parameters by the abstraction (`notifier`), not the concrete type.
2. Accept the smallest interface that does the job.
3. Build the specific object once, at the "edges" of your program, and pass it in.

---

**Next up:** dependency inversion — how high-level modules stay independent of low-level details."""
    ),
    L(
        id="oop-poly-dependency-inversion",
        course_id="oop-software-design",
        module_id="oop-polymorphism",
        title="Dependency Inversion",
        type="theory",
        order=4,
        content="""## Dependency Inversion

The **Dependency Inversion Principle** (the D in SOLID) says high-level modules should not depend on low-level modules — *both* should depend on abstractions. In plain terms: your business logic should not know which logger, database, or network stack it is using.

### The inverted flow

Instead of the caller creating its dependencies internally:

```python
class OrderService:
    def __init__(self):
        self.logger = FileLogger()          # hard-wired detail

    def place_order(self, order):
        self.logger.log("placing order")    # bound to FileLogger
```

...you **inject** the dependency through the constructor:

```python
class OrderService:
    def __init__(self, logger):             # abstraction injected
        self.logger = logger

    def place_order(self, order):
        self.logger.log("placing order")    # any logger works
```

### Constructor injection

```python
service = OrderService(ConsoleLogger())
service2 = OrderService(FileLogger())
service3 = OrderService(CloudLogger())
```

The same `OrderService` works with any object exposing `log(message)` — a duck-typed interface.

### Why "inversion"?

Without injection, `OrderService` points down to `FileLogger`. With injection, both depend on the *abstraction* ("a logger with a `log` method"), so the direction of the dependency is inverted. High-level logic stops being coupled to low-level details.

### Benefits

- Swap infrastructure (files, cloud, memory) without touching business logic.
- Write unit tests with a fake logger.
- Each class stays small and focused on one responsibility.

---

**Next up:** exercises — polymorphic shapes, a strategy pattern, and dependency-injected logging."""
    ),
    L(
        id="oop-poly-exercise-total-area",
        course_id="oop-software-design",
        module_id="oop-polymorphism",
        title="Exercise: Polymorphic Total Area",
        type="exercise",
        order=5,
        content="""## Exercise: Polymorphic Total Area

Reuse the shape hierarchy from Module 2, but this time work with a **collection** of shapes to show polymorphism in action.

- `Shape` — base class with `area()` returning `0`.
- `Circle(Shape)` — `area()` returns `3.14159 * radius ** 2` rounded to 2 decimals.
- `Rectangle(Shape)` — `area()` returns `width * height`.

Write `solve(shapes)` that receives a JSON list of shape objects and returns the **total area**, rounded to 2 decimals.

### Sample

Input (one line):

```text
[{"type":"circle","radius":3},{"type":"rectangle","width":2,"height":5}]
```

Output:

```text
38.27
```

### How your code runs

The harness parses the JSON array and calls `solve(shapes)`. Loop over the objects, build each shape with `make_shape(spec)`, and sum every `shape.area()`.

### Starter code

```python
def solve(shapes):
    total = 0.0
    for spec in shapes:
        total += make_shape(spec).area()
    return round(total, 2)

class Shape:
    def area(_self):
        return 0

class Circle(Shape):
    def __init__(_self, radius):
        _self.radius = radius

    def area(_self):
        return round(3.14159 * _self.radius ** 2, 2)

class Rectangle(Shape):
    def __init__(_self, width, height):
        _self.width = width
        _self.height = height

    def area(_self):
        return _self.width * _self.height

def make_shape(spec):
    if spec["type"] == "circle":
        return Circle(spec["radius"])
    return Rectangle(spec["width"], spec["height"])

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    shapes = json.loads(data)
    print(solve(shapes))

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(shapes):
    total = 0.0
    for spec in shapes:
        total += make_shape(spec).area()
    return round(total, 2)

class Shape:
    def area(_self):
        return 0

class Circle(Shape):
    def __init__(_self, radius):
        _self.radius = radius

    def area(_self):
        return round(3.14159 * _self.radius ** 2, 2)

class Rectangle(Shape):
    def __init__(_self, width, height):
        _self.width = width
        _self.height = height

    def area(_self):
        return _self.width * _self.height

def make_shape(spec):
    if spec["type"] == "circle":
        return Circle(spec["radius"])
    return Rectangle(spec["width"], spec["height"])

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    shapes = json.loads(data)
    print(solve(shapes))

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '[{"type":"circle","radius":3},{"type":"rectangle","width":2,"height":5}]', "expected_output": "38.27", "description": "Circle plus rectangle"},
            {"input": '[{"type":"rectangle","width":2,"height":3},{"type":"rectangle","width":4,"height":5}]', "expected_output": "26.0", "description": "Two rectangles"},
            {"input": '[{"type":"circle","radius":1},{"type":"circle","radius":1}]', "expected_output": "6.28", "description": "Two unit circles"},
            {"input": '[]', "expected_output": "0.0", "description": "No shapes"},
        ],
    ),
    L(
        id="oop-poly-exercise-strategy",
        course_id="oop-software-design",
        module_id="oop-polymorphism",
        title="Exercise: Strategy Pattern (Min/Max)",
        type="exercise",
        order=6,
        content="""## Exercise: Strategy Pattern (Min/Max)

Implement the **Strategy pattern**: a family of algorithms (`MinStrategy`, `MaxStrategy`), each exposing a `compute(nums)` method, selected at runtime by a factory.

- `MinStrategy.compute(nums)` returns `min(nums)`.
- `MaxStrategy.compute(nums)` returns `max(nums)`.
- `select_strategy(mode)` returns the right strategy for `"min"` or `"max"`.

Write `solve(mode, nums)` that selects the strategy and returns its result.

### Sample

Input:

```text
"min"
[3,1,2]
```

Output:

```text
1
```

### How your code runs

The harness passes `mode` (a quoted string) on line 1 and the JSON list on line 2. Your `solve` picks the strategy and calls `strategy.compute(nums)`.

### Starter code

```python
def solve(mode, nums):
    strategy = select_strategy(mode)
    return strategy.compute(nums)

class MinStrategy:
    def compute(_self, nums):
        return min(nums)

class MaxStrategy:
    def compute(_self, nums):
        return max(nums)

def select_strategy(mode):
    if mode == "min":
        return MinStrategy()
    return MaxStrategy()

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    mode = lines[0].strip().strip('"')
    nums = json.loads(lines[1].strip())
    print(solve(mode, nums))

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(mode, nums):
    strategy = select_strategy(mode)
    return strategy.compute(nums)

class MinStrategy:
    def compute(_self, nums):
        return min(nums)

class MaxStrategy:
    def compute(_self, nums):
        return max(nums)

def select_strategy(mode):
    if mode == "min":
        return MinStrategy()
    return MaxStrategy()

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    mode = lines[0].strip().strip('"')
    nums = json.loads(lines[1].strip())
    print(solve(mode, nums))

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '"min"\n[3,1,2]', "expected_output": "1", "description": "Minimum of three"},
            {"input": '"max"\n[3,1,2]', "expected_output": "3", "description": "Maximum of three"},
            {"input": '"min"\n[5,5,5]', "expected_output": "5", "description": "All equal"},
            {"input": '"max"\n[-1,-5,-2]', "expected_output": "-1", "description": "Negative values"},
        ],
    ),
    L(
        id="oop-poly-exercise-logger-di",
        course_id="oop-software-design",
        module_id="oop-polymorphism",
        title="Exercise: Dependency-Injected Logger",
        type="exercise",
        order=7,
        content="""## Exercise: Dependency-Injected Logger

Apply **dependency injection** with duck-typed loggers:

- `ConsoleLogger.log(message)` returns `"LOG: " + message`.
- `FileLogger.log(message)` returns `"FILE: " + message`.
- `make_logger(kind)` returns the right logger for `"console"` or `"file"`.

Write `solve(logger_type, message)` that builds the logger and returns the formatted log line.

### Sample

Input:

```text
"console"
Server started
```

Output:

```text
LOG: Server started
```

### How your code runs

The harness passes the logger type (a quoted string) on line 1 and the message on line 2. Your `solve` injects the chosen logger and delegates to it.

### Starter code

```python
def solve(logger_type, message):
    logger = make_logger(logger_type)
    return logger.log(message)

class ConsoleLogger:
    def log(_self, message):
        return "LOG: " + str(message)

class FileLogger:
    def log(_self, message):
        return "FILE: " + str(message)

def make_logger(kind):
    if kind == "console":
        return ConsoleLogger()
    return FileLogger()

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    logger_type = lines[0].strip().strip('"')
    message = lines[1].strip()
    print(solve(logger_type, message))

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(logger_type, message):
    logger = make_logger(logger_type)
    return logger.log(message)

class ConsoleLogger:
    def log(_self, message):
        return "LOG: " + str(message)

class FileLogger:
    def log(_self, message):
        return "FILE: " + str(message)

def make_logger(kind):
    if kind == "console":
        return ConsoleLogger()
    return FileLogger()

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    logger_type = lines[0].strip().strip('"')
    message = lines[1].strip()
    print(solve(logger_type, message))

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '"console"\nServer started', "expected_output": "LOG: Server started", "description": "Console logger"},
            {"input": '"file"\nUser login', "expected_output": "FILE: User login", "description": "File logger"},
            {"input": '"console"\nerror: bad input', "expected_output": "LOG: error: bad input", "description": "Console with error message"},
            {"input": '"file"\n404 not found', "expected_output": "FILE: 404 not found", "description": "File with numeric-ish message"},
        ],
    ),
    # ── Module 4: Design Principles ─────────────────────────────────────
    L(
        id="oop-principles-srp-ocp",
        course_id="oop-software-design",
        module_id="oop-principles",
        title="SOLID: SRP and OCP",
        type="theory",
        order=1,
        content="""## SOLID: SRP and OCP

**SOLID** is a set of five design principles that keep object-oriented code maintainable. This lesson covers the first two.

### Single Responsibility Principle (SRP)

A class should have **one reason to change**. It should do one thing and do it well.

```python
# Overloaded class — three responsibilities
class Report:
    def compute(self, data):
        ...
    def format(self, data):
        ...
    def save(self, data):
        ...
```

Split responsibilities into separate classes, each focused:

```python
class ReportComputer:
    def compute(self, data):
        ...

class ReportFormatter:
    def format(self, data):
        ...

class ReportSaver:
    def save(self, data):
        ...
```

When a class has one responsibility, it is easier to understand, test, and modify without breaking unrelated behavior.

### Open/Closed Principle (OCP)

Software should be **open for extension but closed for modification**. Add new behavior by adding new code (new subclasses), not by editing existing code.

```python
class AreaCalculator:
    def area(self, shape):
        if isinstance(shape, Circle):
            return 3.14159 * shape.radius ** 2
        elif isinstance(shape, Rectangle):
            return shape.width * shape.height
        # adding a Triangle means editing this method
```

With polymorphism the same goal needs no edits:

```python
class Shape:
    def area(self):
        return 0

class Triangle(Shape):
    def area(self):
        return 0.5 * self.base * self.height
```

Adding `Triangle` never touches `AreaCalculator` — the system is *open for extension* (new subclass) and *closed for modification* (no existing code changes).

---

**Next up:** LSP, ISP, and DIP — the rest of SOLID."""
    ),
    L(
        id="oop-principles-lsp-isp-dip",
        course_id="oop-software-design",
        module_id="oop-principles",
        title="SOLID: LSP, ISP, and DIP",
        type="theory",
        order=2,
        content="""## SOLID: LSP, ISP, and DIP

Three more SOLID principles complete the set.

### Liskov Substitution Principle (LSP)

A subclass must be usable wherever its superclass is expected, without breaking anything.

```python
class Bird:
    def move(self):
        return "fly"

class Ostrich(Bird):
    def move(self):     # overrides correctly — it walks
        return "walk"

def travel(bird):
    return bird.move()

print(travel(Bird()))       # fly
print(travel(Ostrich()))    # walk  — still fine
```

Breaking LSP usually shows up as `if isinstance(...)` checks or overrides that raise unexpected errors. If a subclass cannot honor the parent's contract, it should not inherit from it.

### Interface Segregation Principle (ISP)

Clients should not be forced to depend on methods they don't use. Prefer several small, specific interfaces over one fat one.

```python
class Worker:
    def work(self):
        ...
    def attend_meeting(self):
        ...
    def code_review(self):
        ...
```

A contractor who only codes is forced to implement irrelevant methods. Split the interface so each client depends only on what it needs.

### Dependency Inversion Principle (DIP)

High-level modules should not depend on low-level modules; both should depend on abstractions.

```python
class Checkout:
    def __init__(self, payment):   # inject the abstraction
        self.payment = payment

    def pay(self, amount):
        self.payment.process(amount)
```

Swap in credit-card, PayPal, or a fake payment for tests without touching `Checkout`.

### The five in one line

1. **S**ingle Responsibility — one reason to change.
2. **O**pen/Closed — extend without modifying.
3. **L**iskov Substitution — subclasses honor the contract.
4. **I**nterface Segregation — small, specific interfaces.
5. **D**ependency Inversion — depend on abstractions.

---

**Next up:** cohesion and coupling — how well a module holds together and how little it depends on others."""
    ),
    L(
        id="oop-principles-cohesion-coupling",
        course_id="oop-software-design",
        module_id="oop-principles",
        title="Cohesion and Coupling",
        type="theory",
        order=3,
        content="""## Cohesion and Coupling

Two quality measures describe how a codebase is organized: **cohesion** (inside a module) and **coupling** (between modules).

### Cohesion — how related the parts are

High cohesion means the elements of a class or module belong together and serve a single purpose.

```python
# High cohesion: every method deals with account balances
class Account:
    def deposit(self, amount):
        self.balance += amount

    def withdraw(self, amount):
        if amount <= self.balance:
            self.balance -= amount
```

Low cohesion looks like a grab-bag: an `Utils` class with `parse_csv`, `send_email`, and `compute_hash` unrelated to each other.

### Coupling — how much modules depend on each other

Low coupling means modules interact through small, stable interfaces. High coupling means changes in one module ripple into many others.

```python
# High coupling: this module reaches into Order internals
class Invoice:
    def build(self, order):
        total = 0
        for item in order.items:          # depends on internals
            total += item._price * item._qty
```

```python
# Low coupling: Invoice depends only on a stable contract
class Invoice:
    def build(self, order):
        return order.total()              # a clean public method
```

### The goal

Aim for **high cohesion and low coupling**:

- High cohesion keeps related logic together, so a module is easy to understand and test alone.
- Low coupling means modules can change independently without breaking each other.
- SRP produces high cohesion; programming to abstractions produces low coupling.

### A warning sign

If a change to one class forces edits in five others, coupling is too high. Introduce an interface between them and let each side depend on the abstraction.

---

**Next up:** common design patterns — strategy, factory, and observer."""
    ),
    L(
        id="oop-principles-patterns",
        course_id="oop-software-design",
        module_id="oop-principles",
        title="Common Patterns: Strategy, Factory, Observer",
        type="theory",
        order=4,
        content="""## Common Patterns: Strategy, Factory, Observer

**Design patterns** are proven, reusable solutions to recurring design problems. Three appear constantly.

### Strategy — swap algorithms at runtime

Encapsulate a family of algorithms behind a common interface and select one dynamically.

```python
class MinStrategy:
    def compute(self, nums):
        return min(nums)

class MaxStrategy:
    def compute(self, nums):
        return max(nums)

def pick(strategy, nums):
    return strategy.compute(nums)
```

### Factory — create objects without naming the class

The caller asks for an object by a simple description; the factory decides the concrete class.

```python
def create_shape(kind, size):
    if kind == "circle":
        return Circle(size)
    if kind == "square":
        return Square(size)
    raise ValueError("unknown shape")
```

The factory centralizes construction logic, so callers stay free of `if` chains.

### Observer — notify many without coupling to them

One subject pushes events to a list of subscribers, each implementing the same notification method.

```python
class NewsChannel:
    def __init__(self):
        self.subscribers = []

    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)

    def publish(self, message):
        for subscriber in self.subscribers:
            subscriber.notify(message)
```

### Choosing a pattern

| Pattern   | Use when...                                    |
|-----------|------------------------------------------------|
| Strategy  | You want to swap algorithms at runtime.        |
| Factory   | Construction logic is complex or repetitive.   |
| Observer  | Many objects must react to one event.          |

Patterns are tools, not goals — apply them when they genuinely reduce complexity.

---

**Next up:** exercises — an email validator, a shape factory, and an observer notification center."""
    ),
    L(
        id="oop-principles-exercise-email",
        course_id="oop-software-design",
        module_id="oop-principles",
        title="Exercise: Email Validator Class",
        type="exercise",
        order=5,
        content="""## Exercise: Email Validator Class

Encapsulate validation rules in a class. Write `EmailValidator` with a `validate(email)` method that returns `True` when an email passes **all** rules, else `False`:

- Non-empty.
- Contains exactly one `@`.
- The `@` is not the first or last character.
- Contains a `.` after the `@`.
- Contains no spaces.

Then write `solve(email)` that builds a validator and returns `validator.validate(email)`.

### Sample

Input (one line):

```text
ada@example.com
```

Output:

```text
true
```

### How your code runs

The harness passes the email as a single string. `solve` returns a boolean, which prints as `true` or `false`.

### Starter code

```python
def solve(email):
    return EmailValidator().validate(email)

class EmailValidator:
    def validate(_self, email):
        if not email:
            return False
        if " " in email:
            return False
        parts = email.split("@")
        if len(parts) != 2:
            return False
        if not parts[0] or not parts[1]:
            return False
        return "." in parts[1]

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    print(str(solve(data)).lower())

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(email):
    return EmailValidator().validate(email)

class EmailValidator:
    def validate(_self, email):
        if not email:
            return False
        if " " in email:
            return False
        parts = email.split("@")
        if len(parts) != 2:
            return False
        if not parts[0] or not parts[1]:
            return False
        return "." in parts[1]

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    print(str(solve(data)).lower())

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "ada@example.com", "expected_output": "true", "description": "Valid email"},
            {"input": "ada.example.com", "expected_output": "false", "description": "Missing @ symbol"},
            {"input": "ada@localhost", "expected_output": "false", "description": "No dot after @"},
            {"input": "ada @x.com", "expected_output": "false", "description": "Contains a space"},
            {"input": "@example.com", "expected_output": "false", "description": "@ is first character"},
        ],
    ),
    L(
        id="oop-principles-exercise-factory",
        course_id="oop-software-design",
        module_id="oop-principles",
        title="Exercise: Shape Factory",
        type="exercise",
        order=6,
        content="""## Exercise: Shape Factory

Build a **factory** that creates shape objects from a type string:

- `Circle(size)` — `area()` returns `3.14159 * size ** 2` rounded to 2 decimals.
- `Square(size)` — `area()` returns `size * size`.
- `ShapeFactory.create(kind, size)` returns the correct shape.

Write `solve(kind, size)` that asks the factory for a shape and returns its area.

### Sample

Input:

```text
"circle"
2
```

Output:

```text
12.57
```

### How your code runs

The harness passes the kind (a quoted string) on line 1 and the size on line 2. Your `solve` uses the factory and returns `shape.area()`.

### Starter code

```python
def solve(kind, size):
    shape = ShapeFactory().create(kind, size)
    return shape.area()

class Circle:
    def __init__(_self, size):
        _self.size = size

    def area(_self):
        return round(3.14159 * _self.size ** 2, 2)

class Square:
    def __init__(_self, size):
        _self.size = size

    def area(_self):
        return _self.size * _self.size

class ShapeFactory:
    def create(_self, kind, size):
        if kind == "circle":
            return Circle(size)
        return Square(size)

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    kind = lines[0].strip().strip('"')
    size = int(lines[1].strip())
    print(solve(kind, size))

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(kind, size):
    shape = ShapeFactory().create(kind, size)
    return shape.area()

class Circle:
    def __init__(_self, size):
        _self.size = size

    def area(_self):
        return round(3.14159 * _self.size ** 2, 2)

class Square:
    def __init__(_self, size):
        _self.size = size

    def area(_self):
        return _self.size * _self.size

class ShapeFactory:
    def create(_self, kind, size):
        if kind == "circle":
            return Circle(size)
        return Square(size)

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    kind = lines[0].strip().strip('"')
    size = int(lines[1].strip())
    print(solve(kind, size))

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '"circle"\n2', "expected_output": "12.57", "description": "Circle of size 2"},
            {"input": '"square"\n4', "expected_output": "16", "description": "Square of size 4"},
            {"input": '"circle"\n5', "expected_output": "78.54", "description": "Circle of size 5"},
            {"input": '"square"\n3', "expected_output": "9", "description": "Square of size 3"},
        ],
    ),
    L(
        id="oop-principles-exercise-observer",
        course_id="oop-software-design",
        module_id="oop-principles",
        title="Exercise: Observer Notification Center",
        type="exercise",
        order=7,
        content="""## Exercise: Observer Notification Center

Implement a simple **observer** pattern:

- `NotificationCenter` with `subscribe(channel, name)` and `notify(message)`.
- `notify(message)` returns a list of strings, one per subscriber, formatted as `"channel: name - message"`.

Write `solve(data)` that receives a JSON object with a `subscribers` list and a `message`, and returns the notifications in subscription order.

### Sample

Input (one line):

```text
{"subscribers":[["email","alice"],["sms","bob"]],"message":"hello"}
```

Output:

```text
["email: alice - hello","sms: bob - hello"]
```

### How your code runs

The harness parses the JSON object and calls `solve(data)`. Subscribe each `[channel, name]` pair, then return `center.notify(message)`.

### Starter code

```python
def solve(data):
    center = NotificationCenter()
    for channel, name in data["subscribers"]:
        center.subscribe(channel, name)
    return center.notify(data["message"])

class NotificationCenter:
    def __init__(_self):
        _self.subscribers = []

    def subscribe(_self, channel, name):
        _self.subscribers.append((channel, name))

    def notify(_self, message):
        return [f"{channel}: {name} - {message}" for channel, name in _self.subscribers]

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    payload = json.loads(data)
    print(json.dumps(solve(payload), separators=(",", ":")))

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(data):
    center = NotificationCenter()
    for channel, name in data["subscribers"]:
        center.subscribe(channel, name)
    return center.notify(data["message"])

class NotificationCenter:
    def __init__(_self):
        _self.subscribers = []

    def subscribe(_self, channel, name):
        _self.subscribers.append((channel, name))

    def notify(_self, message):
        return [f"{channel}: {name} - {message}" for channel, name in _self.subscribers]

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    payload = json.loads(data)
    print(json.dumps(solve(payload), separators=(",", ":")))

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '{"subscribers":[["email","alice"],["sms","bob"]],"message":"hello"}', "expected_output": '["email: alice - hello","sms: bob - hello"]', "description": "Two subscribers"},
            {"input": '{"subscribers":[["push","carol"]],"message":"deploy"}', "expected_output": '["push: carol - deploy"]', "description": "Single subscriber"},
            {"input": '{"subscribers":[],"message":"silence"}', "expected_output": "[]", "description": "No subscribers"},
        ],
    ),
    # ── Module 5: Refactoring Project ───────────────────────────────────
    L(
        id="oop-refactor-smells",
        course_id="oop-software-design",
        module_id="oop-refactor",
        title="Refactoring and Code Smells",
        type="theory",
        order=1,
        content="""## Refactoring and Code Smells

**Refactoring** is restructuring existing code without changing its behavior — making it cleaner while the tests keep proving it still works. Before you can refactor well, you must recognize **code smells**: signals that something is wrong.

### Common smells

| Smell                  | What it looks like                                   |
|------------------------|------------------------------------------------------|
| Duplicated code        | The same few lines copy-pasted in several places.    |
| Long function          | One function doing five unrelated jobs.              |
| God object             | A class that holds the whole program's state.        |
| Feature envy           | A method using another object's data more than its own. |
| Data clump             | The same few fields passed around together, again and again. |

### Example: data clump

```python
def create_order(user_name, user_email, user_id, product, qty):
    ...
```

`user_name`, `user_email`, `user_id` travel together — they are begging to become a `User` object.

### Why refactor at all?

- Cleaner code is cheaper to change later.
- Smells usually point to upcoming bugs.
- Refactoring makes the next feature easier to add.

### The golden rule

**Refactor only when tests are green.** You are not changing behavior, so you must be able to prove it. Run the tests before and after every small step.

---

**Next up:** extracting classes from a procedural script."""
    ),
    L(
        id="oop-refactor-extract",
        course_id="oop-software-design",
        module_id="oop-refactor",
        title="Extracting Classes from Procedural Code",
        type="theory",
        order=2,
        content="""## Extracting Classes from Procedural Code

A classic refactoring turns a long procedural script into objects. Start with code that uses loose variables, then group state and behavior into classes.

### Before — procedural

```python
def main():
    name = "Ada"
    score = 92
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    else:
        grade = "C"
    print(name, grade)
```

Every piece of state (`name`, `score`, `grade`) floats at the top level, and the grade logic is embedded in `main`.

### Step 1 — extract a class

```python
class Student:
    def __init__(self, name, score):
        self.name = name
        self.score = score

    def grade(self):
        if self.score >= 90:
            return "A"
        if self.score >= 80:
            return "B"
        return "C"

    def report_line(self):
        return f"{self.name}: {self.grade()}"
```

### Step 2 — slim the caller

```python
def main():
    student = Student("Ada", 92)
    print(student.report_line())   # Ada: A
```

### What changed

- State and its logic now live together in `Student`.
- `main` became a thin orchestration layer.
- The grade rules are reusable and testable in isolation.

### Refactoring recipe

1. Identify a cluster of variables that belong together.
2. Create a class with those fields.
3. Move the functions that operate on them into methods.
4. Run the tests — output must be identical.

---

**Next up:** encapsulating data and behavior."""
    ),
    L(
        id="oop-refactor-encapsulate",
        course_id="oop-software-design",
        module_id="oop-refactor",
        title="Encapsulating Data and Behavior",
        type="theory",
        order=3,
        content="""## Encapsulating Data and Behavior

Encapsulation means an object owns its data and the rules that keep it valid. Refactoring procedural code often means *moving behavior in*: methods take over operations that used to happen outside the object.

### Before — behavior outside the data

```python
class Cart:
    def __init__(self):
        self.items = []

cart = Cart()
cart.items.append({"name": "Pen", "price": 2, "qty": 3})

total = 0
for item in cart.items:          # caller knows too much
    total += item["price"] * item["qty"]
```

The caller reaches into the `items` list and repeats the total logic everywhere.

### After — behavior inside the class

```python
class Cart:
    def __init__(self):
        self._items = []

    def add(self, name, price, qty):
        self._items.append({"name": name, "price": price, "qty": qty})

    def total(self):
        return sum(item["price"] * item["qty"] for item in self._items)
```

```python
cart = Cart()
cart.add("Pen", 2, 3)
print(cart.total())      # 6
```

### The pattern of the refactor

1. Find a loop or calculation that reads an object's fields.
2. Move it into the object as a method.
3. Replace external uses with method calls.
4. Hide the raw fields behind a clear interface.

### Result

Callers stop knowing *how* totals are computed. If the storage changes (say, a `Product` class replaces dicts), only `Cart` changes — every caller keeps calling `cart.total()`.

---

**Next up:** a safe refactoring workflow backed by tests."""
    ),
    L(
        id="oop-refactor-workflow",
        course_id="oop-software-design",
        module_id="oop-refactor",
        title="Refactoring Workflow and Testing",
        type="theory",
        order=4,
        content="""## Refactoring Workflow and Testing

Refactoring is safe when it is boring: small steps, constant verification, no behavior changes. This is the workflow used for the project exercises in this module.

### The refactoring loop

1. **Get green** — run the existing tests; they must pass before you touch anything.
2. **Pick one smell** — one small change at a time.
3. **Refactor** — move code, extract a class, rename, encapsulate.
4. **Re-run the tests** — the same expected outputs must still pass.
5. **Repeat** — another small step, another green run.

### A worked example

```python
# Step 1: tests pass
def main():
    scores = [60, 80, 100]
    avg = sum(scores) / len(scores)
    print(avg, max(scores), min(scores))
```

```python
# Step 2: extract a Grades class, step by step
class Grades:
    def __init__(self, scores):
        self._scores = scores

    def average(self):
        return sum(self._scores) / len(self._scores)

    def highest(self):
        return max(self._scores)

    def lowest(self):
        return min(self._scores)
```

After each extraction, the printed output stays exactly the same.

### Guardrails

- **Small steps** — a big rewrite is not a refactor; it's a rewrite.
- **Behavior lock** — use tests to prove output is unchanged.
- **No feature work** — refactoring adds no new features; it makes future features cheaper.
- **Commit frequently** — if a step breaks something, you can go back easily.

### When to stop

Stop when the code is clear enough that the next feature is obviously easy to add. Refactoring has diminishing returns — perfection is not the goal, maintainability is.

---

**Next up:** the project exercises — reports, grade classes, and a shopping cart."""
    ),
    L(
        id="oop-refactor-exercise-student-report",
        course_id="oop-software-design",
        module_id="oop-refactor",
        title="Exercise: Student Report Formatting",
        type="exercise",
        order=5,
        content="""## Exercise: Student Report Formatting

Build a `Student` class that produces a readable report line:

- `__init__(name, score)` storing both.
- `grade()` returning the letter grade: `A` (90+), `B` (80+), `C` (70+), `D` (60+), else `F`.
- `report_line()` returning `"Name: A"` (a `__str__`-style representation).

Write `solve(students)` that receives a JSON list of `{"name": ..., "score": ...}` objects and returns each student's report line, one per line.

### Sample

Input (one line):

```text
[{"name":"Ada","score":92},{"name":"Bob","score":78}]
```

Output:

```text
Ada: A
Bob: C
```

### How your code runs

The harness parses the JSON array and calls `solve(students)`. Build a `Student` for each entry, collect `report_line()`, and join with newlines.

### Starter code

```python
def solve(students):
    lines = []
    for entry in students:
        student = Student(entry["name"], entry["score"])
        lines.append(student.report_line())
    return "\n".join(lines)

class Student:
    def __init__(_self, name, score):
        _self.name = name
        _self.score = score

    def grade(_self):
        if _self.score >= 90:
            return "A"
        if _self.score >= 80:
            return "B"
        if _self.score >= 70:
            return "C"
        if _self.score >= 60:
            return "D"
        return "F"

    def report_line(_self):
        return f"{_self.name}: {_self.grade()}"

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    students = json.loads(data)
    print(solve(students))

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(students):
    lines = []
    for entry in students:
        student = Student(entry["name"], entry["score"])
        lines.append(student.report_line())
    return "\\n".join(lines)

class Student:
    def __init__(_self, name, score):
        _self.name = name
        _self.score = score

    def grade(_self):
        if _self.score >= 90:
            return "A"
        if _self.score >= 80:
            return "B"
        if _self.score >= 70:
            return "C"
        if _self.score >= 60:
            return "D"
        return "F"

    def report_line(_self):
        return f"{_self.name}: {_self.grade()}"

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    students = json.loads(data)
    print(solve(students))

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '[{"name":"Ada","score":92},{"name":"Bob","score":78}]', "expected_output": "Ada: A\nBob: C", "description": "Two students"},
            {"input": '[{"name":"Pat","score":100}]', "expected_output": "Pat: A", "description": "Perfect score"},
            {"input": '[{"name":"Sam","score":45}]', "expected_output": "Sam: F", "description": "Failing score"},
            {"input": '[]', "expected_output": "", "description": "No students"},
        ],
    ),
    L(
        id="oop-refactor-exercise-grades",
        course_id="oop-software-design",
        module_id="oop-refactor",
        title="Exercise: Grades Class from a Script",
        type="exercise",
        order=6,
        content="""## Exercise: Grades Class from a Script

Refactor a procedural calculation into a `Grades` class:

- `__init__(scores)` storing the list.
- `average()` returning `sum(scores) / len(scores)` rounded to 2 decimals.
- `highest()` and `lowest()` returning the max and min.

Write `solve(scores)` that receives a JSON list of numbers and returns `"{average} {highest} {lowest}"`.

### Sample

Input (one line):

```text
[60,80,100]
```

Output:

```text
80.0 100 60
```

### How your code runs

The harness parses the JSON array and calls `solve(scores)`. Build a `Grades`, then combine the three method results into one string.

### Starter code

```python
def solve(scores):
    grades = Grades(scores)
    return f"{grades.average()} {grades.highest()} {grades.lowest()}"

class Grades:
    def __init__(_self, scores):
        _self.scores = scores

    def average(_self):
        return round(sum(_self.scores) / len(_self.scores), 2)

    def highest(_self):
        return max(_self.scores)

    def lowest(_self):
        return min(_self.scores)

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    scores = json.loads(data)
    print(solve(scores))

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(scores):
    grades = Grades(scores)
    return f"{grades.average()} {grades.highest()} {grades.lowest()}"

class Grades:
    def __init__(_self, scores):
        _self.scores = scores

    def average(_self):
        return round(sum(_self.scores) / len(_self.scores), 2)

    def highest(_self):
        return max(_self.scores)

    def lowest(_self):
        return min(_self.scores)

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    scores = json.loads(data)
    print(solve(scores))

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "[60,80,100]", "expected_output": "80.0 100 60", "description": "Three scores"},
            {"input": "[75]", "expected_output": "75.0 75 75", "description": "Single score"},
            {"input": "[10,20,30]", "expected_output": "20.0 30 10", "description": "Low scores"},
            {"input": "[91,84,77,69,52]", "expected_output": "74.6 91 52", "description": "Mixed scores"},
        ],
    ),
    L(
        id="oop-refactor-exercise-cart",
        course_id="oop-software-design",
        module_id="oop-refactor",
        title="Exercise: Shopping Cart with Products",
        type="exercise",
        order=7,
        content="""## Exercise: Shopping Cart with Products

Encapsulate a cart and its items:

- `Product(name, price)` storing both.
- `Cart` with `add(product, qty)` and `total()` returning the total price rounded to 2 decimals.

Write `solve(items)` that receives a JSON list of `{"name": ..., "price": ..., "qty": ...}` objects, adds a `Product` per item to a `Cart`, and returns `cart.total()`.

### Sample

Input (one line):

```text
[{"name":"Pen","price":2,"qty":3},{"name":"Book","price":10,"qty":1}]
```

Output:

```text
16.00
```

### How your code runs

The harness parses the JSON array and calls `solve(items)`. Build the cart, add products, and return the formatted total.

### Starter code

```python
def solve(items):
    cart = Cart()
    for entry in items:
        product = Product(entry["name"], entry["price"])
        cart.add(product, entry["qty"])
    return f"{cart.total():.2f}"

class Product:
    def __init__(_self, name, price):
        _self.name = name
        _self.price = price

class Cart:
    def __init__(_self):
        _self._items = []

    def add(_self, product, qty):
        _self._items.append((product, qty))

    def total(_self):
        total = 0.0
        for product, qty in _self._items:
            total += product.price * qty
        return total

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    items = json.loads(data)
    print(solve(items))

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(items):
    cart = Cart()
    for entry in items:
        product = Product(entry["name"], entry["price"])
        cart.add(product, entry["qty"])
    return f"{cart.total():.2f}"

class Product:
    def __init__(_self, name, price):
        _self.name = name
        _self.price = price

class Cart:
    def __init__(_self):
        _self._items = []

    def add(_self, product, qty):
        _self._items.append((product, qty))

    def total(_self):
        total = 0.0
        for product, qty in _self._items:
            total += product.price * qty
        return total

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    items = json.loads(data)
    print(solve(items))

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '[{"name":"Pen","price":2,"qty":3},{"name":"Book","price":10,"qty":1}]', "expected_output": "16.00", "description": "Two products"},
            {"input": '[{"name":"Mug","price":5,"qty":2}]', "expected_output": "10.00", "description": "Single product"},
            {"input": '[{"name":"Pen","price":2,"qty":3},{"name":"Pad","price":1.5,"qty":2}]', "expected_output": "9.00", "description": "Decimal price"},
            {"input": "[]", "expected_output": "0.00", "description": "Empty cart"},
        ],
    ),
]
