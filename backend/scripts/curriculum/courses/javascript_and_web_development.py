"""JavaScript and Web Development — curriculum content module."""

COURSE = {
    "id": "javascript-and-web-development",
    "title": "JavaScript and Web Development",
    "description": (
        "Learn JavaScript from the ground up and build for the browser: language "
        "fundamentals, modern ES2015+ features, HTML and CSS, the DOM and browser "
        "APIs, and finally an interactive frontend project. Every concept is paired "
        "with runnable exercises plus hands-on DOM practice."
    ),
    "language": "javascript",
    "icon": "globe",
    "order": 10,
}

MODULES = [
    {
        "id": "js-fundamentals",
        "course_id": "javascript-and-web-development",
        "title": "JavaScript Fundamentals",
        "description": "Variables, data types, operators, functions, arrays, and objects — the building blocks of every JavaScript program.",
        "order": 1,
    },
    {
        "id": "js-modern",
        "course_id": "javascript-and-web-development",
        "title": "Modern JavaScript",
        "description": "Destructuring, modules, higher-order functions, and async basics — the ES2015+ features modern developers use daily.",
        "order": 2,
    },
    {
        "id": "js-dom",
        "course_id": "javascript-and-web-development",
        "title": "HTML, CSS and the DOM",
        "description": "Document structure, styling, events, and forms — the trio that turns scripts into real web pages.",
        "order": 3,
    },
    {
        "id": "js-browser-apis",
        "course_id": "javascript-and-web-development",
        "title": "Browser APIs",
        "description": "Fetch, JSON, localStorage, and error handling — talking to servers and persisting data in the browser.",
        "order": 4,
    },
    {
        "id": "js-project",
        "course_id": "javascript-and-web-development",
        "title": "Frontend Project",
        "description": "Plan, build, and polish a complete interactive browser application using everything you have learned.",
        "order": 5,
    },
]

_JS = "javascript"


def L(**kw):
    kw.setdefault("language", _JS)
    return kw


LESSONS = [
    # ── Module 1: JavaScript Fundamentals ──────────────────────────────
    L(
        id="js-fundamentals-values-variables",
        course_id="javascript-and-web-development",
        module_id="js-fundamentals",
        title="Values and Variables",
        type="theory",
        order=1,
        content="""## Values and Variables

Every JavaScript program is made of **values** — numbers, text, and so on — stored in **variables** so you can refer to them later.

### Declaring variables

| Keyword | Scope    | When to use                              |
|---------|----------|------------------------------------------|
| `let`   | block    | A value you will reassign                 |
| `const` | block    | A value that should not change (default)  |
| `var`   | function | Legacy — avoid in new code                |

```javascript
const name = "Ada";
let score = 92;
score = 95;        // fine for let
// name = "Grace"; // TypeError: assignment to constant
```

### Core data types

| Type       | Examples                        |
|------------|---------------------------------|
| `number`   | `42`, `3.14`, `-7`              |
| `string`   | `"hello"`, `'world'`            |
| `boolean`  | `true`, `false`                 |
| `null`     | `null` (explicitly empty)       |
| `undefined`| `undefined` (never assigned)    |
| `object`   | `{...}`, `[...]`                |

### Checking types

The `typeof` operator reports a value's type:

```javascript
typeof 42        // "number"
typeof "hi"      // "string"
typeof true      // "boolean"
typeof []        // "object" (arrays are objects)
typeof null      // "object" (a famous historical quirk)
```

### Naming rules

- Names are case-sensitive and cannot start with a digit.
- Use `camelCase`: `totalPrice`, not `total_price` or `TotalPrice`.
- Choose names that say what the value means.

### Dynamic typing

Variables are not locked to a type. You can reassign a `let` from a number to a string and JavaScript adapts at runtime — powerful, but another reason `const` is the default.

```javascript
let thing = 5;
thing = "now a string";   // legal
```

---

**Next up:** operators — combining and comparing values."""
    ),
    L(
        id="js-fundamentals-operators",
        course_id="javascript-and-web-development",
        module_id="js-fundamentals",
        title="Operators and Expressions",
        type="theory",
        order=2,
        content="""## Operators and Expressions

An **expression** is any combination of values and operators that evaluates to a result. Operators do the combining.

### Arithmetic

```javascript
5 + 2    // 7
5 - 2    // 3
5 * 2    // 10
5 / 2    // 2.5
5 % 2    // 1  (remainder)
2 ** 3   // 8  (exponent)
```

### Comparison

Comparisons always produce a boolean:

```javascript
5 === 5      // true   (strict equal)
5 === "5"    // false  (different types)
5 !== 5      // false  (strict not equal)
5 < 10       // true
5 <= 5       // true
```

Prefer `===` and `!==`. The loose `==` performs type coercion and causes surprising bugs (`0 == false` is `true`).

### Logical operators

```javascript
true && false   // false  (AND)
true || false   // true   (OR)
!true           // false  (NOT)
```

`&&` and `||` short-circuit: they stop evaluating as soon as the answer is known.

### Falsy values

JavaScript treats six values as "falsey" — everything else is truthy:

```text
false, 0, "", null, undefined, NaN
```

`0` is falsy, so `if (0)` does not run even though `0` is a valid number.

### Assignment shortcuts

```javascript
let count = 0;
count += 5;    // count is now 5
count *= 2;    // count is now 10
count++;       // count is now 11
```

### Operator precedence

`*` and `/` bind tighter than `+` and `-`, so `2 + 3 * 4` is `14`. When in doubt, add parentheses — they are free and make intent obvious.

```javascript
const total = (2 + 3) * 4;   // 20
```

---

**Next up:** functions — the reusable building blocks of JavaScript."""
    ),
    L(
        id="js-fundamentals-functions",
        course_id="javascript-and-web-development",
        module_id="js-fundamentals",
        title="Functions",
        type="theory",
        order=3,
        content="""## Functions

A **function** is a reusable block of code that takes inputs (parameters) and returns a result. Functions keep code organized and prevent repetition.

### Function declarations

```javascript
function add(a, b) {
  return a + b;
}

add(3, 5);   // 8
```

`return` sends a value back; a function without `return` gives `undefined`.

### Function expressions

```javascript
const add = function (a, b) {
  return a + b;
};
```

### Arrow functions

```javascript
const add = (a, b) => a + b;
```

Arrow functions are the modern style: concise and they behave predictably with `this` (important later). They work everywhere expressions work.

### Parameters and arguments

- **Parameters** are the names in the definition.
- **Arguments** are the values passed at the call site.

```javascript
function greet(name, punctuation = "!") {
  return "Hello, " + name + punctuation;
}

greet("Ada");        // "Hello, Ada!"
greet("Ada", "?");   // "Hello, Ada?"
```

Defaults make optional parameters explicit.

### Returning early

`return` can appear multiple times to exit with different results:

```javascript
function classify(score) {
  if (score >= 90) return "A";
  if (score >= 75) return "B";
  return "C";
}
```

### Scope

Variables declared inside a function are **local** to it and disappear when it finishes. Variables outside are **global** and visible everywhere:

```javascript
const globalMessage = "visible everywhere";

function demo() {
  const localOnly = "hidden outside";
  return globalMessage;
}
```

Keeping state local is what makes functions predictable and testable.

---

**Next up:** arrays and objects — the containers that model real data."""
    ),
    L(
        id="js-fundamentals-arrays-objects",
        course_id="javascript-and-web-development",
        module_id="js-fundamentals",
        title="Arrays and Objects",
        type="theory",
        order=4,
        content="""## Arrays and Objects

**Arrays** hold ordered lists of values; **objects** hold named properties. Together they model almost all real-world data.

### Arrays

```javascript
const fruits = ["apple", "banana", "cherry"];
fruits[0];            // "apple"
fruits.length;        // 3
fruits[fruits.length - 1];   // "cherry"
```

Common methods:

```javascript
const nums = [1, 2, 3];
nums.push(4);          // add to end     → [1, 2, 3, 4]
nums.pop();            // remove end     → [1, 2, 3]
nums.indexOf(2);       // 1 (or -1 if absent)
nums.includes(3);      // true
nums.slice(1);         // [2, 3] (new array, original untouched)
```

### Objects

Objects map keys to values:

```javascript
const user = {
  name: "Ada",
  age: 36,
  "favorite language": "JavaScript",
};

user.name;             // "Ada" (dot notation)
user["age"];           // 36 (bracket notation)
user.admin = true;     // add a property
```

### Arrays of objects

The most common data shape in web apps is an array of objects — users, posts, products:

```javascript
const users = [
  { name: "Ada", score: 92 },
  { name: "Linus", score: 87 },
];

users[1].score;        // 87
```

### Looping

```javascript
for (const fruit of fruits) {
  console.log(fruit);
}

for (const key in user) {
  console.log(key, user[key]);
}
```

### Mutation vs new values

`push`, `pop`, and property assignment **mutate** in place. `slice` and `concat` return **new** arrays. Prefer creating new values where practical — it makes data flow easier to reason about.

---

**Next up:** exercises — string helpers, array search, and FizzBuzz."""
    ),
    L(
        id="js-fundamentals-exercise-vowels",
        course_id="javascript-and-web-development",
        module_id="js-fundamentals",
        title="Exercise: Count Vowels",
        type="exercise",
        order=5,
        content="""## Exercise: Count Vowels

Write a function `solve(text)` that returns the number of vowels (`a`, `e`, `i`, `o`, `u`) in a string, ignoring case.

### Sample

Input: `hello`

Output: `2`

### How your code runs

The runner calls your first declared function with the input parsed as JSON (a plain string stays a string). Return the count as a number.

### Starter code

```javascript
function solve(text) {
  let count = 0;
  for (const ch of text.toLowerCase()) {
    if ("aeiou".includes(ch)) count++;
  }
  return count;
}

function main() {
  const input = require('fs').readFileSync(0, 'utf-8').trim();
  if (!input) return;
  console.log(solve(input));
}

if (require.main === module) main();
```

Good luck!""",
        starter_code="""function solve(text) {
  let count = 0;
  for (const ch of text.toLowerCase()) {
    if ("aeiou".includes(ch)) count++;
  }
  return count;
}

function main() {
  const input = require('fs').readFileSync(0, 'utf-8').trim();
  if (!input) return;
  console.log(solve(input));
}

if (require.main === module) main();
""",
        test_cases=[
            {"input": "hello", "expected_output": "2", "description": "hello has two vowels"},
            {"input": "JAVASCRIPT", "expected_output": "3", "description": "Uppercase counts too"},
            {"input": "rhythm", "expected_output": "0", "description": "No vowels"},
            {"input": "aeiou", "expected_output": "5", "description": "All vowels"},
        ],
    ),
    L(
        id="js-fundamentals-exercise-search",
        course_id="javascript-and-web-development",
        module_id="js-fundamentals",
        title="Exercise: Find the Target",
        type="exercise",
        order=6,
        content="""## Exercise: Find the Target

Write a function `solve(nums, target)` that returns the **index** of `target` inside `nums`, or `-1` if it is not present.

### Sample

Input:

```text
[4, 1, 9, 7]
9
```

Output:

```text
2
```

### How your code runs

The runner calls your function with two arguments parsed from the two input lines: the first is a JSON array, the second a number.

### Starter code

```javascript
function solve(nums, target) {
  return nums.indexOf(target);
}

function main() {
  const lines = require('fs').readFileSync(0, 'utf-8').trim().split('\\n');
  if (!lines[0]) return;
  const nums = JSON.parse(lines[0]);
  const target = Number(lines[1]);
  console.log(solve(nums, target));
}

if (require.main === module) main();
```

Good luck!""",
        starter_code="""function solve(nums, target) {
  return nums.indexOf(target);
}

function main() {
  const lines = require('fs').readFileSync(0, 'utf-8').trim().split('\\n');
  if (!lines[0]) return;
  const nums = JSON.parse(lines[0]);
  const target = Number(lines[1]);
  console.log(solve(nums, target));
}

if (require.main === module) main();
""",
        test_cases=[
            {"input": "[4, 1, 9, 7]\n9", "expected_output": "2", "description": "Found in the middle"},
            {"input": "[4, 1, 9, 7]\n4", "expected_output": "0", "description": "Found at the start"},
            {"input": "[4, 1, 9, 7]\n5", "expected_output": "-1", "description": "Not present"},
            {"input": "[7]\n7", "expected_output": "0", "description": "Single-element array"},
        ],
    ),
    L(
        id="js-fundamentals-exercise-fizzbuzz",
        course_id="javascript-and-web-development",
        module_id="js-fundamentals",
        title="Exercise: FizzBuzz",
        type="exercise",
        order=7,
        content="""## Exercise: FizzBuzz

Write a function `solve(n)` that returns an **array of strings** for the numbers 1 through `n`:

- divisible by 3 → `"Fizz"`
- divisible by 5 → `"Buzz"`
- divisible by both → `"FizzBuzz"`
- otherwise → the number as a string

### Sample

Input: `5`

Output:

```text
["1","2","Fizz","4","Buzz"]
```

### How your code runs

The runner calls `solve(n)` with a single number. Return the array of strings; the harness prints it as JSON.

### Starter code

```javascript
function solve(n) {
  const result = [];
  for (let i = 1; i <= n; i++) {
    if (i % 15 === 0) result.push("FizzBuzz");
    else if (i % 3 === 0) result.push("Fizz");
    else if (i % 5 === 0) result.push("Buzz");
    else result.push(String(i));
  }
  return result;
}

function main() {
  const input = require('fs').readFileSync(0, 'utf-8').trim();
  if (!input) return;
  console.log(JSON.stringify(solve(Number(input))));
}

if (require.main === module) main();
```

Good luck!""",
        starter_code="""function solve(n) {
  const result = [];
  for (let i = 1; i <= n; i++) {
    if (i % 15 === 0) result.push("FizzBuzz");
    else if (i % 3 === 0) result.push("Fizz");
    else if (i % 5 === 0) result.push("Buzz");
    else result.push(String(i));
  }
  return result;
}

function main() {
  const input = require('fs').readFileSync(0, 'utf-8').trim();
  if (!input) return;
  console.log(JSON.stringify(solve(Number(input))));
}

if (require.main === module) main();
""",
        test_cases=[
            {"input": "5", "expected_output": '["1","2","Fizz","4","Buzz"]', "description": "Short run"},
            {"input": "15", "expected_output": '["1","2","Fizz","4","Buzz","Fizz","7","8","Fizz","Buzz","11","Fizz","13","14","FizzBuzz"]', "description": "Full classic run"},
            {"input": "1", "expected_output": '["1"]', "description": "Single number"},
            {"input": "3", "expected_output": '["1","2","Fizz"]', "description": "Fizz appears"},
        ],
    ),
    # ── Module 2: Modern JavaScript ────────────────────────────────────
    L(
        id="js-modern-destructuring",
        course_id="javascript-and-web-development",
        module_id="js-modern",
        title="Destructuring and Spread",
        type="theory",
        order=1,
        content="""## Destructuring and Spread

Modern JavaScript makes working with arrays and objects far less verbose through **destructuring** (unpacking values) and **spread** (spreading values out).

### Array destructuring

```javascript
const [first, second] = [10, 20, 30];
first;    // 10
second;   // 20
```

Swap variables without a temporary one:

```javascript
let a = 1;
let b = 2;
[a, b] = [b, a];   // a=2, b=1
```

The rest element gathers the remaining items:

```javascript
const [head, ...tail] = [1, 2, 3, 4];
head;   // 1
tail;   // [2, 3, 4]
```

### Object destructuring

```javascript
const user = { name: "Ada", age: 36 };
const { name, age } = user;
name;   // "Ada"
```

Rename with `:` and provide defaults with `=`:

```javascript
const { name: displayName, admin = false } = user;
```

### Spread

Spread copies arrays and objects:

```javascript
const nums = [1, 2, 3];
const more = [...nums, 4];      // [1, 2, 3, 4]

const base = { name: "Ada" };
const user = { ...base, age: 36 };
```

Later properties override earlier ones — the classic way to apply defaults:

```javascript
const settings = { ...defaults, ...userOverrides };
```

### Why it matters

Destructuring is everywhere in modern code — React props, API responses, config objects. It makes the shape of data explicit and removes repetitive `obj.` prefixes.

---

**Next up:** modules — splitting code into files with import and export."""
    ),
    L(
        id="js-modern-modules",
        course_id="javascript-and-web-development",
        module_id="js-modern",
        title="Modules: import and export",
        type="theory",
        order=2,
        content="""## Modules: import and export

As programs grow, code is split into files. **ES modules** are JavaScript's official way to share code between files using `import` and `export`.

### Named exports

```javascript
// math.js
export function square(x) {
  return x * x;
}
export const PI = 3.14159;
```

```javascript
// app.js
import { square, PI } from "./math.js";
square(5);   // 25
```

### Default exports

Each module can have one **default export** — the main thing it provides:

```javascript
// greeting.js
export default function greet(name) {
  return `Hello, ${name}!`;
}
```

```javascript
// app.js
import greet from "./greeting.js";
```

### Importing everything

```javascript
import * as math from "./math.js";
math.square(3);   // 9
```

### Module rules

- Modules are **always in strict mode**.
- Each module has its **own scope** — nothing leaks to the global object.
- `import` is hoisted and each module runs once, even if imported in several places.

### In the browser

```html
<script type="module" src="app.js"></script>
```

Module scripts are deferred and can `import` other files. For production, **bundlers** like Vite, Webpack, or esbuild combine modules into optimized files.

### CommonJS vs ES modules

Node historically used CommonJS:

```javascript
const fs = require("fs");
module.exports = { square };
```

The ecosystem is converging on ES modules, but `require` still appears in tooling and older codebases. Both are worth recognizing.

---

**Next up:** higher-order functions — map, filter, and reduce."""
    ),
    L(
        id="js-modern-higher-order",
        course_id="javascript-and-web-development",
        module_id="js-modern",
        title="Higher-Order Functions",
        type="theory",
        order=3,
        content="""## Higher-Order Functions

A **higher-order function** takes a function as an argument or returns one. The most useful trio is `map`, `filter`, and `reduce` — they replace most manual loops over arrays.

### map — transform every element

```javascript
const nums = [1, 2, 3];
const doubled = nums.map((n) => n * 2);   // [2, 4, 6]
```

`map` always returns a new array of the **same length**.

### filter — keep matching elements

```javascript
const nums = [1, 2, 3, 4, 5, 6];
const evens = nums.filter((n) => n % 2 === 0);   // [2, 4, 6]
```

`filter` keeps elements where the callback returns `true`.

### reduce — boil the array down

```javascript
const nums = [1, 2, 3, 4];
const total = nums.reduce((acc, n) => acc + n, 0);   // 10
```

`reduce` threads an **accumulator** through the array. The first argument is the previous accumulator (starting at the initial value), the second is the current element.

### Chaining

The three compose beautifully:

```javascript
const nums = [1, 2, 3, 4, 5, 6];
const result = nums
  .filter((n) => n % 2 === 0)      // [2, 4, 6]
  .map((n) => n * n)               // [4, 16, 36]
  .reduce((acc, n) => acc + n, 0); // 56
```

### Callbacks

A **callback** is any function passed to another function. Array methods, `setTimeout`, event listeners, and `fetch` all rely on them:

```javascript
setTimeout(() => console.log("later"), 1000);
```

### Why prefer them

- No off-by-one indexing bugs.
- No manual accumulator bookkeeping.
- Each method has a single, clear purpose — code reads as a pipeline.

---

**Next up:** async basics — promises and async/await."""
    ),
    L(
        id="js-modern-async-basics",
        course_id="javascript-and-web-development",
        module_id="js-modern",
        title="Async Basics",
        type="theory",
        order=4,
        content="""## Async Basics

JavaScript is single-threaded: it cannot run two scripts at the same time. Long operations — network requests, timers, file reads — must not block the thread, so they are **asynchronous**: they start now and finish later.

### Callbacks

The original pattern passes a function to run when the work completes:

```javascript
setTimeout(() => {
  console.log("one second later");
}, 1000);
```

Nesting many callbacks produces "callback hell":

```javascript
getData((a) => {
  getMore(a, (b) => {
    getEvenMore(b, (c) => {
      // hard to read, hard to fix
    });
  });
});
```

### Promises

A **Promise** represents a value that will exist later. It is either `pending`, `fulfilled`, or `rejected`:

```javascript
fetch("/api/users")
  .then((res) => res.json())
  .then((users) => console.log(users))
  .catch((err) => console.error(err));
```

`.then` chains steps; `.catch` handles failure anywhere in the chain.

### async / await

`async` functions always return a Promise. Inside them, `await` pauses until a Promise settles:

```javascript
async function loadUsers() {
  const res = await fetch("/api/users");
  const users = await res.json();
  return users;
}
```

`await` reads top-to-bottom — no nesting. Errors propagate with `try/catch`:

```javascript
try {
  const users = await loadUsers();
  console.log(users);
} catch (err) {
  console.error("failed to load", err);
}
```

### The mental model

- `await` does **not** make things synchronous — the thread stays free; your code just waits its turn.
- Everything after `await` runs later as a microtask.
- `Promise.all` runs independent tasks in parallel.

Async is how browsers fetch data, load images, and respond to input. This module's exercises keep async logic pure and synchronous, but the browser API module puts it to real use.

---

**Next up:** exercises — reduce, closures, and a destructuring swap."""
    ),
    L(
        id="js-modern-exercise-reduce-sum",
        course_id="javascript-and-web-development",
        module_id="js-modern",
        title="Exercise: Reduce to Sum",
        type="exercise",
        order=5,
        content="""## Exercise: Reduce to Sum

Write a function `solve(nums)` that returns the **sum** of all numbers in the array using `.reduce()`. The computation happens inside your `solve` function.

### Sample

Input:

```text
[1, 2, 3, 4]
```

Output:

```text
10
```

### How your code runs

The runner calls `solve(nums)` with a single JSON array. Use `reduce` with an initial value of `0` and return the number.

### Starter code

```javascript
function solve(nums) {
  return nums.reduce((sum, n) => sum + n, 0);
}

function main() {
  const input = require('fs').readFileSync(0, 'utf-8').trim();
  if (!input) return;
  console.log(solve(JSON.parse(input)));
}

if (require.main === module) main();
```

Good luck!""",
        starter_code="""function solve(nums) {
  return nums.reduce((sum, n) => sum + n, 0);
}

function main() {
  const input = require('fs').readFileSync(0, 'utf-8').trim();
  if (!input) return;
  console.log(solve(JSON.parse(input)));
}

if (require.main === module) main();
""",
        test_cases=[
            {"input": "[1, 2, 3, 4]", "expected_output": "10", "description": "Simple sum"},
            {"input": "[5, -2, 10]", "expected_output": "13", "description": "Negative values"},
            {"input": "[]", "expected_output": "0", "description": "Empty array"},
            {"input": "[100]", "expected_output": "100", "description": "Single element"},
        ],
    ),
    L(
        id="js-modern-exercise-closures-counter",
        course_id="javascript-and-web-development",
        module_id="js-modern",
        title="Exercise: Closure Counter",
        type="exercise",
        order=6,
        content="""## Exercise: Closure Counter

Write a function `solve(ops)` that drives a **counter built with a closure**. A closure is a function that remembers the variables from the scope where it was created.

The counter exposes methods as strings in the `ops` array:

- `"inc"` — increment the count
- `"dec"` — decrement the count
- `"get"` — record the current count into the result

`solve` returns the **array of values recorded by `"get"` calls**.

### Sample

Input:

```text
["inc", "inc", "get", "inc", "get"]
```

Output:

```text
[2, 3]
```

### How your code runs

The runner calls `solve(ops)` with a JSON array of strings. Build the counter as a closure that keeps `count` private, then dispatch each operation.

### Starter code

```javascript
function solve(ops) {
  let count = 0;
  const results = [];
  const counter = {
    inc: () => { count += 1; },
    dec: () => { count -= 1; },
    get: () => count,
  };
  for (const op of ops) {
    if (op === "inc") counter.inc();
    else if (op === "dec") counter.dec();
    else if (op === "get") results.push(counter.get());
  }
  return results;
}

function main() {
  const input = require('fs').readFileSync(0, 'utf-8').trim();
  if (!input) return;
  console.log(JSON.stringify(solve(JSON.parse(input))));
}

if (require.main === module) main();
```

Good luck!""",
        starter_code="""function solve(ops) {
  let count = 0;
  const results = [];
  const counter = {
    inc: () => { count += 1; },
    dec: () => { count -= 1; },
    get: () => count,
  };
  for (const op of ops) {
    if (op === "inc") counter.inc();
    else if (op === "dec") counter.dec();
    else if (op === "get") results.push(counter.get());
  }
  return results;
}

function main() {
  const input = require('fs').readFileSync(0, 'utf-8').trim();
  if (!input) return;
  console.log(JSON.stringify(solve(JSON.parse(input))));
}

if (require.main === module) main();
""",
        test_cases=[
            {"input": '["inc", "inc", "get", "inc", "get"]', "expected_output": "[2,3]", "description": "Increments and reads"},
            {"input": '["get"]', "expected_output": "[0]", "description": "Starts at zero"},
            {"input": '["inc", "dec", "dec", "get"]', "expected_output": "[-1]", "description": "Goes negative"},
            {"input": '["inc", "get", "get"]', "expected_output": "[1,1]", "description": "Reading does not change the count"},
        ],
    ),
    L(
        id="js-modern-exercise-destructure-swap",
        course_id="javascript-and-web-development",
        module_id="js-modern",
        title="Exercise: Destructuring Swap",
        type="exercise",
        order=7,
        content="""## Exercise: Destructuring Swap

Write a function `solve(a, b)` that returns an array `[b, a]` — the values swapped — using **array destructuring** rather than a temporary variable.

### Sample

Input:

```text
3
5
```

Output:

```text
[5, 3]
```

### How your code runs

The runner calls `solve(a, b)` with two numbers parsed from the two input lines. Use `[a, b] = [b, a]` inside the function and return the array.

### Starter code

```javascript
function solve(a, b) {
  [a, b] = [b, a];
  return [a, b];
}

function main() {
  const lines = require('fs').readFileSync(0, 'utf-8').trim().split('\\n');
  if (!lines[0]) return;
  const a = Number(lines[0]);
  const b = Number(lines[1]);
  console.log(JSON.stringify(solve(a, b)));
}

if (require.main === module) main();
```

Good luck!""",
        starter_code="""function solve(a, b) {
  [a, b] = [b, a];
  return [a, b];
}

function main() {
  const lines = require('fs').readFileSync(0, 'utf-8').trim().split('\\n');
  if (!lines[0]) return;
  const a = Number(lines[0]);
  const b = Number(lines[1]);
  console.log(JSON.stringify(solve(a, b)));
}

if (require.main === module) main();
""",
        test_cases=[
            {"input": "3\n5", "expected_output": "[5,3]", "description": "Simple swap"},
            {"input": "10\n10", "expected_output": "[10,10]", "description": "Equal values"},
            {"input": "-1\n7", "expected_output": "[7,-1]", "description": "Negative value"},
            {"input": "0\n0", "expected_output": "[0,0]", "description": "Zeros"},
        ],
    ),
    # ── Module 3: HTML, CSS and the DOM ────────────────────────────────
    L(
        id="js-dom-structure",
        course_id="javascript-and-web-development",
        module_id="js-dom",
        title="HTML Document Structure",
        type="theory",
        order=1,
        content="""## HTML Document Structure

**HTML** gives a web page its structure. It is a tree of nested **elements**, and the browser parses it into the **DOM** (Document Object Model) that JavaScript can inspect and modify.

### A minimal page

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>My Page</title>
  </head>
  <body>
    <h1>Hello!</h1>
    <p>This is a paragraph.</p>
  </body>
</html>
```

- `<head>` holds metadata — title, stylesheet links, settings.
- `<body>` holds everything the user sees.

### Elements and attributes

An element is an opening tag, content, and a closing tag. Attributes configure it:

```html
<a href="https://example.com" class="nav-link">Visit</a>
<img src="photo.jpg" alt="A photo" />
<input type="text" placeholder="Your name" />
```

- `id` must be **unique** on a page — good for hooks JavaScript targets.
- `class` can repeat — good for styling groups.

### Semantic elements

Modern HTML describes meaning, not just appearance:

| Tag          | Meaning                              |
|--------------|--------------------------------------|
| `<header>`   | Intro or navigation region           |
| `<nav>`      | Navigation links                     |
| `<main>`     | Primary content                      |
| `<section>`  | A themed group of content            |
| `<article>`  | A self-contained piece               |
| `<footer>`   | Closing region                       |
| `<button>`   | A clickable action (not `<div>`)     |

Semantic tags improve accessibility and make code self-documenting.

### Nesting

Elements nest to form the tree the DOM mirrors:

```html
<ul>
  <li>One</li>
  <li>Two</li>
</ul>
```

`<li>` elements are children of the `<ul>`. JavaScript later navigates exactly this parent/child structure.

---

**Next up:** CSS — styling the structure."""
    ),
    L(
        id="js-dom-styling",
        course_id="javascript-and-web-development",
        module_id="js-dom",
        title="Styling with CSS",
        type="theory",
        order=2,
        content="""## Styling with CSS

**CSS** (Cascading Style Sheets) controls how HTML looks. A rule pairs a **selector** (which elements) with **declarations** (how they look).

### Anatomy of a rule

```css
.nav-link {
  color: #1e90ff;
  font-weight: bold;
}
```

`.nav-link` is a class selector (leading dot). An `#id` selector uses a hash; a plain name is a type selector:

```css
h1 { color: navy; }
#app { max-width: 800px; }
```

### Common properties

```css
.card {
  background: #f5f5f5;
  padding: 16px;
  margin: 8px 0;
  border: 1px solid #ccc;
  border-radius: 8px;
}
```

### The box model

Every element is a box: content, then **padding**, then **border**, then **margin** (outside to inside). Understanding this explains most layout surprises.

```css
.box {
  padding: 12px;   /* space inside the border */
  margin: 12px;    /* space outside the border */
}
```

### Flexbox

A one-line tool for laying out rows or columns:

```css
.toolbar {
  display: flex;
  gap: 8px;
  justify-content: space-between;
}
```

### Adding CSS to a page

```html
<link rel="stylesheet" href="styles.css" />
```

Or inline on an element (highest priority, use sparingly):

```html
<p style="color: red;">Important</p>
```

### CSS in the DOM course

JavaScript frequently toggles classes to change styles:

```javascript
element.classList.add("highlighted");
element.classList.remove("highlighted");
element.classList.toggle("highlighted");
```

Style stays in CSS; JavaScript only switches which classes apply. That separation keeps both files clean.

---

**Next up:** events — making pages respond to users."""
    ),
    L(
        id="js-dom-events",
        course_id="javascript-and-web-development",
        module_id="js-dom",
        title="Events and the DOM",
        type="theory",
        order=3,
        content="""## Events and the DOM

The **DOM** is JavaScript's live view of the page. **Events** are how the page tells your code what the user did.

### Selecting elements

```javascript
const button = document.querySelector("#submit");
const buttons = document.querySelectorAll(".btn");
```

`querySelector` returns the first match; `querySelectorAll` returns all matches.

### Reading and writing

```javascript
const title = document.querySelector("#title");
title.textContent = "New title";
title.textContent;          // "New title"
```

### Adding an event listener

```javascript
const button = document.querySelector("#submit");
button.addEventListener("click", (event) => {
  console.log("Clicked!", event.target);
});
```

The callback receives an **event object** with details like `target` (the element that fired) and, for keyboard events, `key`.

### Common events

| Event      | Fires when                          |
|------------|-------------------------------------|
| `click`    | Element is clicked                  |
| `input`    | An input's value changes            |
| `change`   | A select/checkbox changes           |
| `submit`   | A form is submitted                 |
| `keydown`  | A key is pressed                    |
| `DOMContentLoaded` | The HTML has been parsed   |

### Creating and removing nodes

```javascript
const li = document.createElement("li");
li.textContent = "New item";
document.querySelector("#list").appendChild(li);
```

`textContent` is safe by default — unlike `innerHTML`, it never parses HTML, which prevents many XSS issues.

### Event delegation

Attach one listener to a container and let events bubble up:

```javascript
document.querySelector("#list").addEventListener("click", (event) => {
  if (event.target.matches("li")) {
    console.log("Item:", event.target.textContent);
  }
});
```

This stays correct even when items are added later — a key technique for dynamic lists.

---

**Next up:** forms — collecting and validating user input."""
    ),
    L(
        id="js-dom-forms",
        course_id="javascript-and-web-development",
        module_id="js-dom",
        title="Forms and User Input",
        type="theory",
        order=4,
        content="""## Forms and User Input

**Forms** are the standard way to collect input. JavaScript intercepts submission, reads the values, validates them, and decides what happens next.

### A simple form

```html
<form id="signup">
  <input type="text" id="name" name="name" placeholder="Name" required />
  <input type="email" id="email" name="email" placeholder="Email" required />
  <button type="submit">Sign up</button>
</form>
```

### Reading values

```javascript
const form = document.querySelector("#signup");
form.addEventListener("submit", (event) => {
  event.preventDefault();   // stop the page reloading
  const name = document.querySelector("#name").value;
  const email = document.querySelector("#email").value;
  console.log({ name, email });
});
```

Always call `event.preventDefault()` on submit — otherwise the browser reloads the page.

### Input types

| Type        | Purpose                 | Example value       |
|-------------|-------------------------|---------------------|
| `text`      | Short text              | `"Ada"`             |
| `email`     | Email address           | `"a@b.com"`         |
| `number`    | Numeric input           | `"36"`              |
| `password`  | Masked text             | `"secret"`          |
| `checkbox`  | On/off boolean          | `true`/`false`      |
| `select`    | Pick from options       | chosen value        |

### Checking a checkbox

```javascript
const subscribe = document.querySelector("#subscribe");
subscribe.checked;   // true or false
```

### Client-side validation

HTML attributes like `required` help, but real validation needs JavaScript:

```javascript
function validate(email) {
  if (!email.includes("@")) return "Enter a valid email.";
  if (email.length < 5) return "Email is too short.";
  return null;   // no error
}
```

### Showing errors

Create message elements dynamically and clear them on the next attempt:

```javascript
const errorBox = document.querySelector("#errors");
errorBox.textContent = "";
errorBox.textContent = validate(email);
```

Client-side validation improves UX; it never replaces server-side validation — a theme you will revisit in the backend course.

---

**Next up:** exercises — chunking, plus DOM practice with events and forms."""
    ),
    L(
        id="js-dom-exercise-chunking",
        course_id="javascript-and-web-development",
        module_id="js-dom",
        title="Exercise: Array Chunking",
        type="exercise",
        order=5,
        content="""## Exercise: Array Chunking

Write a function `solve(arr, size)` that splits an array into chunks of at most `size` elements and returns an array of chunks. Chunking is the logic behind paginated lists and infinite scroll grids.

### Sample

Input:

```text
[1, 2, 3, 4, 5]
2
```

Output:

```text
[[1,2],[3,4],[5]]
```

### How your code runs

The runner calls `solve(arr, size)` with a JSON array and a number. Use a loop and `slice()` to build the chunks.

### Starter code

```javascript
function solve(arr, size) {
  const chunks = [];
  for (let i = 0; i < arr.length; i += size) {
    chunks.push(arr.slice(i, i + size));
  }
  return chunks;
}

function main() {
  const lines = require('fs').readFileSync(0, 'utf-8').trim().split('\\n');
  if (!lines[0]) return;
  const arr = JSON.parse(lines[0]);
  const size = Number(lines[1]);
  console.log(JSON.stringify(solve(arr, size)));
}

if (require.main === module) main();
```

Good luck!""",
        starter_code="""function solve(arr, size) {
  const chunks = [];
  for (let i = 0; i < arr.length; i += size) {
    chunks.push(arr.slice(i, i + size));
  }
  return chunks;
}

function main() {
  const lines = require('fs').readFileSync(0, 'utf-8').trim().split('\\n');
  if (!lines[0]) return;
  const arr = JSON.parse(lines[0]);
  const size = Number(lines[1]);
  console.log(JSON.stringify(solve(arr, size)));
}

if (require.main === module) main();
""",
        test_cases=[
            {"input": "[1, 2, 3, 4, 5]\n2", "expected_output": "[[1,2],[3,4],[5]]", "description": "Trailing partial chunk"},
            {"input": "[1, 2, 3, 4]\n2", "expected_output": "[[1,2],[3,4]]", "description": "Exact division"},
            {"input": "[1, 2, 3]\n1", "expected_output": "[[1],[2],[3]]", "description": "Size one"},
            {"input": "[]\n3", "expected_output": "[]", "description": "Empty array"},
        ],
    ),
    L(
        id="js-dom-exercise-event-practice",
        course_id="javascript-and-web-development",
        module_id="js-dom",
        title="Practice: Event Counter",
        type="practice",
        order=6,
        content="""## Practice: Event Counter

This is a **practice-only** exercise — it runs in the browser, so it has no automated test cases. Build it in your own HTML file and verify by clicking.

### The task

Create a page with a button and a counter display. Every click increments the counter and updates the display.

### Starter HTML

```html
<button id="click-me">Click me</button>
<p id="count">0</p>
```

### Starter JavaScript

```javascript
let count = 0;
const button = document.querySelector("#click-me");
const display = document.querySelector("#count");

button.addEventListener("click", () => {
  count += 1;
  display.textContent = count;
});
```

### Extend it

1. Add a "Reset" button that sets the count back to `0`.
2. Change the display color to red when the count reaches 10 (`classList.toggle`).
3. Use **event delegation**: place both buttons in one container and read `event.target.id` to decide what to do.
4. Prevent double-counting on a double-click by disabling the button briefly.

### Check yourself

- Does the page reload when you click? If a `<form>` wraps the button, call `event.preventDefault()`.
- Does the count survive a refresh? It should not — persistence arrives with localStorage in the next module.

Event handling is the core of every interactive page. Once this feels natural, forms and browser APIs will slot right in.

---

**Next up:** Browser APIs — fetch, JSON, and localStorage."""
    ),
    L(
        id="js-dom-exercise-form-practice",
        course_id="javascript-and-web-development",
        module_id="js-dom",
        title="Practice: Form Validation",
        type="practice",
        order=7,
        content="""## Practice: Form Validation

This is a **practice-only** exercise — it runs in the browser with no automated tests. Build and test it yourself.

### The task

Create a signup form with email and password fields. On submit, validate both fields and show an error list without reloading the page.

### Starter HTML

```html
<form id="signup">
  <input type="email" id="email" placeholder="Email" />
  <input type="password" id="password" placeholder="Password" />
  <button type="submit">Sign up</button>
</form>
<ul id="errors"></ul>
```

### Starter JavaScript

```javascript
const form = document.querySelector("#signup");
const errors = document.querySelector("#errors");

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const email = document.querySelector("#email").value;
  const password = document.querySelector("#password").value;

  const messages = [];
  if (!email.includes("@")) messages.push("Email must contain @");
  if (password.length < 8) messages.push("Password must be at least 8 characters");

  errors.textContent = "";
  messages.forEach((m) => {
    const li = document.createElement("li");
    li.textContent = m;
    errors.appendChild(li);
  });
});
```

### Extend it

1. Live-validate the password `input` event as the user types (clear errors when fixed).
2. Add a "confirm password" field that must match.
3. Show a green success message when everything passes.
4. Style `.errors li` with red text via CSS.

### Check yourself

- Does the page reload on submit? You forgot `preventDefault()`.
- Are errors cleared before showing new ones? You must reset the list each submit.

This mirrors what a real registration form does — and the backend course will protect it with server-side checks.

---

**Next up:** Module 4 — the browser APIs that fetch and store data."""
    ),


    # ── Module 4: Browser APIs ─────────────────────────────────────────
    L(
        id="js-browser-fetch",
        course_id="javascript-and-web-development",
        module_id="js-browser-apis",
        title="The Fetch API",
        type="theory",
        order=1,
        content="""## The Fetch API

The **Fetch API** is the modern way to make HTTP requests from the browser. It returns a Promise, so it pairs naturally with `async`/`await`.

### A GET request

```javascript
async function loadUsers() {
  const res = await fetch("/api/users");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const users = await res.json();
  return users;
}
```

`fetch` sends the request and resolves to a **Response** object once headers arrive. The body is read separately with `res.json()` or `res.text()`.

### The Response object

| Property / method | Meaning                              |
|-------------------|--------------------------------------|
| `res.ok`          | `true` for status 200–299            |
| `res.status`      | Numeric status code                  |
| `res.statusText`  | Status text like `"OK"`              |
| `res.json()`      | Parse body as JSON (returns Promise) |
| `res.text()`      | Parse body as text (returns Promise) |
| `res.headers`     | Response headers                     |

### A POST request

```javascript
async function createUser(user) {
  const res = await fetch("/api/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(user),
  });
  return res.json();
}
```

### Request options

| Option        | Purpose                          |
|---------------|----------------------------------|
| `method`      | `"GET"`, `"POST"`, `"PUT"`, `"DELETE"`, ... |
| `headers`     | Request headers object           |
| `body`        | Request body (string)            |
| `credentials` | `"same-origin"` to send cookies  |

### Two failure modes

`fetch` only rejects on **network failures**. An HTTP 404 is a normal response — check `res.ok` or `res.status` yourself:

```javascript
try {
  const res = await fetch("/api/users");
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return await res.json();
} catch (err) {
  console.error("Fetch failed:", err);
}
```

Fetch is the data transport behind almost every interactive page. The project module builds a small app on top of it.

---

**Next up:** JSON — the wire format fetch sends and receives."""
    ),
    L(
        id="js-browser-json",
        course_id="javascript-and-web-development",
        module_id="js-browser-apis",
        title="Working with JSON",
        type="theory",
        order=2,
        content="""## Working with JSON

**JSON** (JavaScript Object Notation) is the standard text format for data over HTTP. It looks like JavaScript object literals — because it was designed by a JavaScript programmer.

### Example

```json
{
  "name": "Ada",
  "age": 36,
  "skills": ["JavaScript", "Python"],
  "active": true
}
```

### The two conversion functions

```javascript
JSON.stringify(value);   // object → JSON string
JSON.parse(string);      // JSON string → object
```

```javascript
const user = { name: "Ada", age: 36 };
const text = JSON.stringify(user);      // '{"name":"Ada","age":36}'
const parsed = JSON.parse(text);        // { name: "Ada", age: 36 }
```

### JSON rules

| Rule                 | Example                         |
|----------------------|---------------------------------|
| Keys are double-quoted | `"name"` not `name`            |
| Strings use double quotes | `"hi"` not `'hi'`          |
| Supported values     | object, array, string, number, boolean, null |
| No comments, no `undefined`, no functions | — |

`undefined`, functions, and `NaN` **disappear** when stringified:

```javascript
JSON.stringify({ a: undefined, b: NaN });
// '{"b":null}'
```

### Parsing failures

Malformed JSON throws a `SyntaxError`:

```javascript
try {
  JSON.parse("{ bad json ");
} catch (err) {
  console.error("Invalid JSON");
}
```

### JSON and fetch

They are inseparable:

```javascript
const res = await fetch("/api/users");
const users = await res.json();             // parse incoming

await fetch("/api/users", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(newUser),            // serialize outgoing
});
```

### Deep clone gotcha

`JSON.parse(JSON.stringify(data))` is a common quick clone, but it drops functions, converts `undefined` to nothing, and turns `Date` into a string. Use it only for plain data.

---

**Next up:** localStorage — persisting data in the browser."""
    ),
    L(
        id="js-browser-storage",
        course_id="javascript-and-web-development",
        module_id="js-browser-apis",
        title="localStorage",
        type="theory",
        order=3,
        content="""## localStorage

**localStorage** is a small persistent key/value store built into every browser. Data survives page reloads and browser restarts — perfect for settings, draft text, and small app state.

### Basic API

```javascript
localStorage.setItem("theme", "dark");
localStorage.getItem("theme");    // "dark"
localStorage.removeItem("theme");
localStorage.clear();
```

Keys and values are **always strings**.

### Storing structured data

Because values are strings, objects must be serialized with JSON:

```javascript
const user = { name: "Ada", score: 92 };

// save
localStorage.setItem("user", JSON.stringify(user));

// load
const raw = localStorage.getItem("user");
const parsed = raw ? JSON.parse(raw) : null;
parsed.name;   // "Ada"
```

### The JSON round-trip

1. `JSON.stringify(value)` — serialize.
2. `localStorage.setItem(key, serialized)` — store.
3. `localStorage.getItem(key)` — retrieve.
4. `JSON.parse(...)` — deserialize.

This pattern is exactly what the storage exercise in this module simulates with pure logic.

### sessionStorage

`sessionStorage` works identically but clears when the tab closes — useful for temporary form state.

### Pitfalls

- **Limit:** roughly 5 MB per origin. Large blobs will throw.
- **`getItem` returns `null`** for missing keys — always handle it.
- **Corrupt JSON crashes `parse`** — wrap in `try/catch` and fall back to a default.
- **Not for secrets:** any script on the page can read localStorage. Never store passwords or tokens here long-term (the backend course returns to this).

### Where it fits

localStorage powers "remember me" lists, themes, and offline drafts. In the project module it keeps a todo list alive between visits.

---

**Next up:** error handling — failing gracefully."""
    ),
    L(
        id="js-browser-error-handling",
        course_id="javascript-and-web-development",
        module_id="js-browser-apis",
        title="Error Handling",
        type="theory",
        order=4,
        content="""## Error Handling

Real apps hit failures: servers return 500s, JSON is malformed, storage is full. **Error handling** is how code survives those moments instead of crashing.

### try / catch / finally

```javascript
try {
  const data = JSON.parse(raw);
  console.log(data.name);
} catch (err) {
  console.error("Parse failed:", err.message);
} finally {
  console.log("Always runs");
}
```

- `try` — the risky code.
- `catch (err)` — runs only if something in `try` throws.
- `finally` — always runs, for cleanup.

### Throwing errors

Create failures deliberately with `throw`:

```javascript
function divide(a, b) {
  if (b === 0) throw new Error("Cannot divide by zero");
  return a / b;
}
```

The thrown value lands in whatever `catch` is above it.

### Custom error types

```javascript
class ValidationError extends Error {}
throw new ValidationError("Email is required");
```

### Async errors

Promises reject instead of throwing — handle with `.catch` or `try/catch` around `await`:

```javascript
try {
  const res = await fetch("/api/users");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const users = await res.json();
  return users;
} catch (err) {
  return [];   // degrade gracefully
}
```

### Error objects

`err.message` is the human-readable string; `err.stack` is a call trace. Log both in development.

### Principles

- **Fail fast:** validate inputs early and throw clear errors.
- **Degrade gracefully:** return a safe default (`[]`, `null`) instead of letting the UI crash.
- **Never swallow silently:** `catch` with an empty body hides bugs.
- **Re-throw when you cannot handle it:** sometimes the caller needs to know.

Solid error handling is what separates a demo from a dependable app.

---

**Next up:** exercises — object flattening, debounce logic, and a JSON round-trip."""
    ),
    L(
        id="js-browser-exercise-object-flatten",
        course_id="javascript-and-web-development",
        module_id="js-browser-apis",
        title="Exercise: Flatten a Nested Object",
        type="exercise",
        order=5,
        content="""## Exercise: Flatten a Nested Object

Write a function `solve(obj)` that returns a **flattened** version of a nested object — nested keys become dot-separated keys. Flattening is common when preparing API data for tables or storage.

### Sample

Input:

```text
{"a": {"b": 1, "c": {"d": 2}}, "e": 3}
```

Output:

```text
{"a.b":1,"a.c.d":2,"e":3}
```

### How your code runs

The runner calls `solve(obj)` with one JSON object. Walk the object recursively, building flattened keys with a prefix, and return the flat object.

### Starter code

```javascript
function solve(obj) {
  const flat = {};
  function walk(node, prefix) {
    for (const key in node) {
      const path = prefix ? prefix + "." + key : key;
      if (node[key] !== null && typeof node[key] === "object" && !Array.isArray(node[key])) {
        walk(node[key], path);
      } else {
        flat[path] = node[key];
      }
    }
  }
  walk(obj, "");
  return flat;
}

function main() {
  const input = require('fs').readFileSync(0, 'utf-8').trim();
  if (!input) return;
  console.log(JSON.stringify(solve(JSON.parse(input))));
}

if (require.main === module) main();
```

Good luck!""",
        starter_code="""function solve(obj) {
  const flat = {};
  function walk(node, prefix) {
    for (const key in node) {
      const path = prefix ? prefix + "." + key : key;
      if (node[key] !== null && typeof node[key] === "object" && !Array.isArray(node[key])) {
        walk(node[key], path);
      } else {
        flat[path] = node[key];
      }
    }
  }
  walk(obj, "");
  return flat;
}

function main() {
  const input = require('fs').readFileSync(0, 'utf-8').trim();
  if (!input) return;
  console.log(JSON.stringify(solve(JSON.parse(input))));
}

if (require.main === module) main();
""",
        test_cases=[
            {"input": '{"a": {"b": 1, "c": {"d": 2}}, "e": 3}', "expected_output": '{"a.b":1,"a.c.d":2,"e":3}', "description": "Two levels deep"},
            {"input": '{"x": 1}', "expected_output": '{"x":1}', "description": "Already flat"},
            {"input": '{"a": {"b": {"c": {"d": 4}}}}', "expected_output": '{"a.b.c.d":4}', "description": "Deeply nested"},
            {"input": '{"a": [1, {"b": 2}]}', "expected_output": '{"a":[1,{"b":2}]}', "description": "Arrays stay intact"},
        ],
    ),
    L(
        id="js-browser-exercise-debounce",
        course_id="javascript-and-web-development",
        module_id="js-browser-apis",
        title="Exercise: Debounce Logic",
        type="exercise",
        order=6,
        content="""## Exercise: Debounce Logic

Write a function `solve(events, delay)` that simulates **debouncing** — the technique that delays a handler until the user stops typing.

`events` is an array of `[time, value]` pairs sorted by time. A value **fires** when no later event arrives within `delay` units of time. Return the array of values that fire, in order.

### Sample

Input:

```text
[[0, "a"], [5, "b"], [20, "c"]]
10
```

`"a"` at time 0 is followed by `"b"` at 5 (within 10) so it is cancelled. `"b"` is followed by `"c"` at 20 — a gap of 15 — so `"b"` fires. `"c"` has nothing after it, so it fires too:

Output:

```text
["b","c"]
```

### How your code runs

The runner calls `solve(events, delay)` with a JSON array of pairs and a number. Compare each event's time with the next event's time.

### Starter code

```javascript
function solve(events, delay) {
  const fired = [];
  for (let i = 0; i < events.length; i++) {
    const [time, value] = events[i];
    const nextTime = i + 1 < events.length ? events[i + 1][0] : Infinity;
    if (nextTime - time >= delay) fired.push(value);
  }
  return fired;
}

function main() {
  const lines = require('fs').readFileSync(0, 'utf-8').trim().split('\\n');
  if (!lines[0]) return;
  const events = JSON.parse(lines[0]);
  const delay = Number(lines[1]);
  console.log(JSON.stringify(solve(events, delay)));
}

if (require.main === module) main();
```

Good luck!""",
        starter_code="""function solve(events, delay) {
  const fired = [];
  for (let i = 0; i < events.length; i++) {
    const [time, value] = events[i];
    const nextTime = i + 1 < events.length ? events[i + 1][0] : Infinity;
    if (nextTime - time >= delay) fired.push(value);
  }
  return fired;
}

function main() {
  const lines = require('fs').readFileSync(0, 'utf-8').trim().split('\\n');
  if (!lines[0]) return;
  const events = JSON.parse(lines[0]);
  const delay = Number(lines[1]);
  console.log(JSON.stringify(solve(events, delay)));
}

if (require.main === module) main();
""",
        test_cases=[
            {"input": '[[0, "a"], [5, "b"], [20, "c"]]\n10', "expected_output": '["b","c"]', "description": "b fires after a gap of 15"},
            {"input": '[[0, "a"], [10, "b"]]\n10', "expected_output": '["a","b"]', "description": "Exact gap of 10 fires both"},
            {"input": '[[0, "a"], [1, "b"], [2, "c"]]\n5', "expected_output": '["c"]', "description": "Only the last of a burst fires"},
            {"input": '[[0, "only"]]\n10', "expected_output": '["only"]', "description": "Single event always fires"},
        ],
    ),
    L(
        id="js-browser-exercise-json-roundtrip",
        course_id="javascript-and-web-development",
        module_id="js-browser-apis",
        title="Exercise: localStorage JSON Round-Trip",
        type="exercise",
        order=7,
        content="""## Exercise: localStorage JSON Round-Trip

Write a function `solve(data)` that simulates saving data to localStorage and reading it back — **without a browser**. The runner passes an object; your function must return the JSON string that a save would produce.

### Sample

Input:

```text
{"name": "Ada", "skills": ["JS", "Python"]}
```

Output:

```text
{"name":"Ada","skills":["JS","Python"]}
```

### How your code runs

The runner calls `solve(data)` with one JSON object. Serialize it with `JSON.stringify` and return the string.

### Starter code

```javascript
function solve(data) {
  return JSON.stringify(data);
}

function main() {
  const input = require('fs').readFileSync(0, 'utf-8').trim();
  if (!input) return;
  console.log(solve(JSON.parse(input)));
}

if (require.main === module) main();
```

Good luck!""",
        starter_code="""function solve(data) {
  return JSON.stringify(data);
}

function main() {
  const input = require('fs').readFileSync(0, 'utf-8').trim();
  if (!input) return;
  console.log(solve(JSON.parse(input)));
}

if (require.main === module) main();
""",
        test_cases=[
            {"input": '{"name": "Ada", "skills": ["JS", "Python"]}', "expected_output": '{"name":"Ada","skills":["JS","Python"]}', "description": "Object with array"},
            {"input": '{"a": {"b": 1}}', "expected_output": '{"a":{"b":1}}', "description": "Nested object"},
            {"input": '[1, 2, 3]', "expected_output": "[1,2,3]", "description": "Array input"},
            {"input": '{"flag": true, "none": null}', "expected_output": '{"flag":true,"none":null}', "description": "Booleans and null"},
        ],
    ),
    # ── Module 5: Frontend Project ─────────────────────────────────────
    L(
        id="js-project-planning",
        course_id="javascript-and-web-development",
        module_id="js-project",
        title="Planning the Application",
        type="theory",
        order=1,
        content="""## Planning the Application

The final module builds an interactive browser application. Before writing UI code, plan it the way a real team would.

### 1. Choose the app

Pick something small but real — a **todo list** is the classic choice: it needs input, state, rendering, filtering, and persistence. You will build the pieces across this module.

### 2. Define requirements

Write down what it must do:

- Add a todo item.
- Mark an item complete.
- Filter items (all / active / completed).
- Persist items between reloads.

### 3. Sketch the layout

Draw the regions: an input row, filter buttons, and a list. Knowing where things live before styling saves a lot of rework.

### 4. Design the state

Decide the single data shape the app manages:

```javascript
const state = {
  todos: [
    { id: 1, title: "Learn JS", done: false },
  ],
  filter: "all",
};
```

All UI renders from this one object.

### 5. Plan the files

Keep concerns separate:

```text
index.html     structure
styles.css     styling
app.js         logic and rendering
```

### 6. List the functions

Before coding, name the core functions and what they return — these become the runnable and practice exercises in this module:

- `filterTodos(todos, filter)` — pure filtering logic.
- `render()` — draw state into the DOM.
- `addTodo(title)` — update state then render.
- `save()` / `load()` — localStorage persistence.

### A small project beats a big one

A tiny app you finish beats an ambitious one you abandon. This module's exercises build the todo app in pieces so each part is small and testable.

---

**Next up:** building the HTML and CSS structure."""
    ),
    L(
        id="js-project-html-css",
        course_id="javascript-and-web-development",
        module_id="js-project",
        title="HTML and CSS Structure",
        type="theory",
        order=2,
        content="""## HTML and CSS Structure

With a plan, build the static shell: the page structure and its styling, before any behavior exists.

### The HTML skeleton

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>My Todos</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <main class="app">
      <h1>My Todos</h1>

      <form id="add-form">
        <input type="text" id="new-todo" placeholder="What needs doing?" />
        <button type="submit">Add</button>
      </form>

      <nav class="filters">
        <button data-filter="all" class="active">All</button>
        <button data-filter="active">Active</button>
        <button data-filter="completed">Completed</button>
      </nav>

      <ul id="todo-list"></ul>
    </main>
    <script type="module" src="app.js"></script>
  </body>
</html>
```

### The CSS shell

```css
body { font-family: system-ui; max-width: 480px; margin: 2rem auto; }
.filters button.active { background: #1e90ff; color: #fff; }
li.done { text-decoration: line-through; color: #888; }
```

### Design the hooks

JavaScript will need stable selectors. Note the `id`s (`add-form`, `new-todo`, `todo-list`) and the `data-filter` attributes — they are the contract between HTML and JS.

### Build static first

Put a few hard-coded `<li>` items in the list and style them. When it looks right, delete them and let JavaScript take over. This "static-first" approach catches CSS problems early.

---

**Next up:** managing state and rendering from it."""
    ),
    L(
        id="js-project-state-rendering",
        course_id="javascript-and-web-development",
        module_id="js-project",
        title="State and Rendering",
        type="theory",
        order=3,
        content="""## State and Rendering

The heart of a frontend app is the **render cycle**: change state, then redraw the UI from it. Keep the DOM a pure function of state and bugs become rare.

### The core loop

```javascript
function render() {
  const list = document.querySelector("#todo-list");
  list.textContent = "";

  for (const todo of state.todos) {
    const li = document.createElement("li");
    li.textContent = todo.title;
    if (todo.done) li.classList.add("done");
    list.appendChild(li);
  }
}
```

### Mutating state then re-rendering

```javascript
function addTodo(title) {
  state.todos.push({ id: Date.now(), title, done: false });
  render();
}
```

### Wiring events

```javascript
const form = document.querySelector("#add-form");
form.addEventListener("submit", (event) => {
  event.preventDefault();
  const input = document.querySelector("#new-todo");
  const title = input.value.trim();
  if (!title) return;
  addTodo(title);
  input.value = "";
});
```

### Event delegation for dynamic lists

Each `<li>` created at render time cannot be wired once — attach one listener to the list instead:

```javascript
document.querySelector("#todo-list").addEventListener("click", (event) => {
  if (event.target.tagName !== "LI") return;
  // toggle done for the matching todo, then render()
});
```

### Toggling completion

```javascript
function toggleTodo(id) {
  const todo = state.todos.find((t) => t.id === id);
  if (todo) todo.done = !todo.done;
  render();
}
```

### Key ideas

- **One source of truth** — the `state` object.
- **Re-render on every change** — small pages can afford it; clarity wins.
- **Read from state, never from the DOM** — no `textContent` sniffing.

Rendering is pure and predictable, which makes the next step — persistence — trivial.

---

**Next up:** persisting state and finishing the app."""
    ),
    L(
        id="js-project-persistence-finish",
        course_id="javascript-and-web-development",
        module_id="js-project",
        title="Persistence and Finishing",
        type="theory",
        order=4,
        content="""## Persistence and Finishing

The last pieces: save state between visits, then review and polish.

### Saving with localStorage

```javascript
function save() {
  localStorage.setItem("todos", JSON.stringify(state.todos));
}
```

Call `save()` after every mutation — inside `addTodo`, `toggleTodo`, and any delete.

### Loading on startup

```javascript
function load() {
  try {
    const raw = localStorage.getItem("todos");
    state.todos = raw ? JSON.parse(raw) : [];
  } catch {
    state.todos = [];
  }
}

load();
render();
```

The `try/catch` guards against corrupt saved data — a real-world failure mode.

### Delete support

```javascript
function removeTodo(id) {
  state.todos = state.todos.filter((t) => t.id !== id);
  save();
  render();
}
```

### The filter trio

```javascript
function filterTodos(todos, filter) {
  if (filter === "active") return todos.filter((t) => !t.done);
  if (filter === "completed") return todos.filter((t) => t.done);
  return todos;
}
```

Buttons update `state.filter`, then `render()` re-filters.

### Review checklist

- [ ] Empty input is rejected
- [ ] Add, toggle, and delete all work
- [ ] Filters show the right subset
- [ ] State survives a page reload
- [ ] Corrupt localStorage does not crash
- [ ] The page degrades gracefully on errors

### Celebrate the milestone

You now know enough to build and ship simple web apps: structure (HTML), style (CSS), behavior (JS), data transport (fetch), and persistence (localStorage). From here, the backend course shows you how to add a real server.

---

**Next up:** exercises — todo filtering logic, then practice building the app."""
    ),
    L(
        id="js-project-exercise-todo-filter",
        course_id="javascript-and-web-development",
        module_id="js-project",
        title="Exercise: Todo Filter Logic",
        type="exercise",
        order=5,
        content="""## Exercise: Todo Filter Logic

Write a function `solve(todos, filter)` that returns the filtered list of todos.

Each todo is an object like `{"id": 1, "title": "Learn JS", "done": false}`. The filter is one of:

- `"all"` — return everything
- `"active"` — only `done: false`
- `"completed"` — only `done: true`

### Sample

Input:

```text
[{"id": 1, "title": "Learn JS", "done": false}, {"id": 2, "title": "Build app", "done": true}]
active
```

Output:

```text
[{"id":1,"title":"Learn JS","done":false}]
```

### How your code runs

The runner calls `solve(todos, filter)` with a JSON array and a plain string. Return the filtered array.

### Starter code

```javascript
function solve(todos, filter) {
  if (filter === "active") return todos.filter((t) => !t.done);
  if (filter === "completed") return todos.filter((t) => t.done);
  return todos;
}

function main() {
  const lines = require('fs').readFileSync(0, 'utf-8').trim().split('\\n');
  if (!lines[0]) return;
  const todos = JSON.parse(lines[0]);
  const filter = lines[1].trim();
  console.log(JSON.stringify(solve(todos, filter)));
}

if (require.main === module) main();
```

Good luck!""",
        starter_code="""function solve(todos, filter) {
  if (filter === "active") return todos.filter((t) => !t.done);
  if (filter === "completed") return todos.filter((t) => t.done);
  return todos;
}

function main() {
  const lines = require('fs').readFileSync(0, 'utf-8').trim().split('\\n');
  if (!lines[0]) return;
  const todos = JSON.parse(lines[0]);
  const filter = lines[1].trim();
  console.log(JSON.stringify(solve(todos, filter)));
}

if (require.main === module) main();
""",
        test_cases=[
            {"input": '[{"id": 1, "title": "Learn JS", "done": false}, {"id": 2, "title": "Build app", "done": true}]\nactive', "expected_output": '[{"id":1,"title":"Learn JS","done":false}]', "description": "Active filter"},
            {"input": '[{"id": 1, "title": "Learn JS", "done": false}, {"id": 2, "title": "Build app", "done": true}]\ncompleted', "expected_output": '[{"id":2,"title":"Build app","done":true}]', "description": "Completed filter"},
            {"input": '[{"id": 1, "title": "Learn JS", "done": false}]\nall', "expected_output": '[{"id":1,"title":"Learn JS","done":false}]', "description": "All filter"},
            {"input": '[]\nactive', "expected_output": "[]", "description": "Empty list"},
        ],
    ),
    L(
        id="js-project-exercise-render-practice",
        course_id="javascript-and-web-development",
        module_id="js-project",
        title="Practice: Render Function",
        type="practice",
        order=6,
        content="""## Practice: Render Function

This is a **practice-only** exercise — it needs the browser's DOM, so it has no automated tests. Run it in a local HTML page.

### The task

Write a `render(todos)` function that draws an array of todos into `<ul id="todo-list">`, marking completed items with a `done` class.

### Starter HTML

```html
<ul id="todo-list"></ul>
```

### Starter JavaScript

```javascript
function render(todos) {
  const list = document.querySelector("#todo-list");
  list.textContent = "";

  for (const todo of todos) {
    const li = document.createElement("li");
    li.textContent = todo.title;
    if (todo.done) li.classList.add("done");
    list.appendChild(li);
  }
}

const todos = [
  { id: 1, title: "Learn JS", done: true },
  { id: 2, title: "Build the app", done: false },
];
render(todos);
```

### Extend it

1. Add a delete button to each row and handle its click via **event delegation**.
2. Show an empty-state message like "Nothing here" when the list is empty.
3. Add a counter `<p id="count">` that shows the number of active items.
4. Toggle a todo when its row is clicked.

### Check yourself

- Does the list clear before re-rendering? Otherwise items duplicate.
- Is a completed item visually distinct? Check the `.done` class applies.

Rendering from state is the same idea whether the app has 10 lines or 10,000 — once it feels natural, you have the frontend mindset.

---

**Next up:** practice — assembling the complete app."""
    ),
    L(
        id="js-project-exercise-full-app",
        course_id="javascript-and-web-development",
        module_id="js-project",
        title="Practice: The Complete App",
        type="practice",
        order=7,
        content="""## Practice: The Complete App

This is the **practice capstone** of the course — a browser-only exercise with no automated tests. Build the whole app and make it yours.

### The task

Assemble the todo app from every piece of the course: HTML structure, CSS styling, state, rendering, events, filtering, and localStorage persistence.

### Starter structure

```html
<main class="app">
  <h1>My Todos</h1>
  <form id="add-form">
    <input type="text" id="new-todo" placeholder="What needs doing?" />
    <button type="submit">Add</button>
  </form>
  <nav class="filters">
    <button data-filter="all" class="active">All</button>
    <button data-filter="active">Active</button>
    <button data-filter="completed">Completed</button>
  </nav>
  <ul id="todo-list"></ul>
</main>
```

### Starter JavaScript

```javascript
const state = {
  todos: [],
  filter: "all",
};

function load() {
  try {
    const raw = localStorage.getItem("todos");
    state.todos = raw ? JSON.parse(raw) : [];
  } catch {
    state.todos = [];
  }
}

function save() {
  localStorage.setItem("todos", JSON.stringify(state.todos));
}

function filterTodos(todos, filter) {
  if (filter === "active") return todos.filter((t) => !t.done);
  if (filter === "completed") return todos.filter((t) => t.done);
  return todos;
}

function render() {
  const list = document.querySelector("#todo-list");
  const visible = filterTodos(state.todos, state.filter);
  list.textContent = "";
  for (const todo of visible) {
    const li = document.createElement("li");
    li.textContent = todo.title;
    if (todo.done) li.classList.add("done");
    list.appendChild(li);
  }
}

// add event listeners here, then:
load();
render();
```

### Finish the wiring

Add the missing pieces:

- `submit` listener on `#add-form` that adds a todo and re-renders.
- `click` listener on `.filters` that sets `state.filter` and re-renders.
- A way to toggle and delete todos (delegation on `#todo-list`).
- Call `save()` after every change.

### Stretch goals

- Store the active filter too, and restore it on load.
- Show a count of remaining items.
- Add a "Clear completed" button.

### Ship it

When it works, you have built a complete frontend application — the skills behind countless real products.

---

**Next up:** the Backend Web Development course — adding a server to this frontend."""
    ),
]
