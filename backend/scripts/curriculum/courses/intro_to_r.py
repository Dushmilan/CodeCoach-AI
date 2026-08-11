"""Introduction to R — curriculum content module."""

COURSE = {
    "id": "intro-to-r",
    "title": "Introduction to R",
    "description": (
        "Start your R journey from zero: the RStudio environment and base R syntax, "
        "vectors and data structures, control flow, functions and packages, data "
        "cleaning, and visualization with base R and ggplot2. Every concept is paired "
        "with hands-on exercises you can run right here."
    ),
    "language": "r",
    "icon": "r",
    "order": 6,
}

MODULES = [
    {
        "id": "r-intro",
        "course_id": "intro-to-r",
        "title": "R Environment and Basics",
        "description": "Set up your R workspace, learn how scripts run, and get comfortable with variables, vectors, and core data types.",
        "order": 1,
    },
    {
        "id": "r-structures",
        "course_id": "intro-to-r",
        "title": "Data Structures and Control Flow",
        "description": "Organize data with lists, matrices, and data frames, and control the flow of your scripts with conditions and loops.",
        "order": 2,
    },
    {
        "id": "r-functions",
        "course_id": "intro-to-r",
        "title": "Functions and Packages",
        "description": "Write reusable functions, understand arguments and scope, and extend R with packages.",
        "order": 3,
    },
    {
        "id": "r-cleaning",
        "course_id": "intro-to-r",
        "title": "Data Cleaning with R",
        "description": "Handle missing values, fix types, and filter and transform data into analysis-ready shape.",
        "order": 4,
    },
    {
        "id": "r-viz",
        "course_id": "intro-to-r",
        "title": "Visualization and Mini Project",
        "description": "Turn data into insight with base R plots and ggplot2, then tie everything together in a small analysis project.",
        "order": 5,
    },
]

_R = "r"


def L(**kw):
    kw.setdefault("language", _R)
    return kw


LESSONS = [
    # ── Module 1: R Environment and Basics ──────────────────────────────
    L(
        id="r-intro-what-is-r",
        course_id="intro-to-r",
        module_id="r-intro",
        title="What is R and How Does It Run?",
        type="theory",
        order=1,
        content="""## What is R and How Does It Run?

R is a programming language built by statisticians for data analysis, statistics, and visualization. It is an **interpreted** language: you write code in plain-text files (or directly in a console) and R executes it one statement at a time.

### The RStudio workflow

Most R users work in **RStudio**, which gives you four panes:

- **Source** — the script editor where you write and save `.R` files.
- **Console** — where R runs your code and prints output.
- **Environment** — shows the variables currently in memory.
- **Plots / Help / Files** — charts, documentation, and project files.

### Scripts vs the console

The console runs one line at a time. A **script** is a collection of lines saved to disk so you can re-run the whole analysis later:

```r
# analysis.R
x <- 5
print(x * 2)
```

Press **Ctrl+Enter** to run the current line from a script into the console.

### Expressions and output

The `print()` function displays values explicitly:

```r
print("Hello from R")
print(1 + 2)
```

Typing a value by itself in the console also prints it, but in a script you must call `print()` (or `cat()`) to see output.

### Comments

A `#` starts a comment — R ignores everything after it on that line:

```r
# This line explains the next one
price <- 9.99
```

### The assignment operator

R uses `<-` for assignment (a legacy from the language's early days), though `=` also works:

```r
name <- "Ada"     # preferred style
age = 36           # also valid
```

---

**Next up:** variables, data types, and the built-in operations R gives you for free."""
    ),
    L(
        id="r-intro-variables",
        course_id="intro-to-r",
        module_id="r-intro",
        title="Variables and Core Data Types",
        type="theory",
        order=2,
        content="""## Variables and Core Data Types

A **variable** is a name that refers to a value. Assign a value with `<-` and R stores it in your workspace:

```r
message <- "hello"
age <- 36
pi_approx <- 3.14159
```

### Atomic types

| Type      | Example           | Notes                              |
|-----------|-------------------|------------------------------------|
| `numeric` | `3.14`, `-2`, `1e6` | Double-precision numbers           |
| `integer` | `5L`              | The `L` suffix forces an integer   |
| `character` | `"hi"`          | Text — always in quotes            |
| `logical` | `TRUE` / `FALSE`  | Booleans (uppercase, not `true`)   |
| `factor`  | `factor("a")`     | Categorical values (more later)    |
| `NULL`    | `NULL`            | "No value"                         |
| `NA`      | `NA`              | Missing value marker               |

Check a value's type with `typeof()`:

```r
typeof(42)      # "double"
typeof(42L)     # "integer"
typeof("hi")    # "character"
typeof(TRUE)    # "logical"
```

### Arithmetic

The usual operators work on numbers:

```r
a <- 10
b <- 3
print(a + b)    # 13
print(a - b)    # 7
print(a * b)    # 30
print(a / b)    # 3.333333
print(a %% b)   # 1  (modulo / remainder)
print(a %/% b)  # 3  (integer division)
print(a ^ b)    # 1000 (power)
```

### Naming rules

- Names are case-sensitive (`Age` and `age` differ).
- Use lowercase words separated by dots or underscores: `user_name` or `user.name`.
- They must start with a letter (or a dot) and cannot contain spaces.

### Converting between types

```r
as.character(42)     # "42"
as.numeric("3.14")   # 3.14
as.integer(3.9)      # 3  (truncates, does not round)
as.logical(1)        # TRUE
```

Not every conversion is safe — `as.numeric("hello")` returns `NA` with a warning instead of crashing, which is a common R gotcha.

---

**Next up:** vectors — R's most important data structure."""
    ),
    L(
        id="r-intro-vectors",
        course_id="intro-to-r",
        module_id="r-intro",
        title="Vectors: R's Workhorse",
        type="theory",
        order=3,
        content="""## Vectors: R's Workhorse

A **vector** is an ordered collection of values, all of the **same type**. Vectors are everywhere in R — even a single number is a vector of length 1.

### Building vectors

Use the combine function `c()`:

```r
numbers <- c(1, 2, 3, 4)
words <- c("apple", "banana", "cherry")
logicals <- c(TRUE, FALSE, TRUE)
```

Sequences are built with `:` and `seq()`:

```r
1:5                # 1 2 3 4 5
seq(1, 10, by = 2) # 1 3 5 7 9
```

### Vectorized arithmetic

Operations apply to **every element** automatically. No loop required:

```r
scores <- c(70, 80, 90)
print(scores + 5)    # 75 85 95
print(scores * 2)    # 140 160 180
print(scores > 75)   # FALSE TRUE TRUE
```

This "vectorization" is why R code is so concise.

### Indexing

Use square brackets. R indices are **1-based** (unlike Python and most other languages):

```r
words <- c("apple", "banana", "cherry")
words[1]        # "apple"
words[2:3]      # "banana" "cherry"
words[-1]       # everything except the first  ("banana" "cherry")
words[c(1, 3)]  # "apple" "cherry"
```

### Useful functions

```r
length(c(1, 2, 3))    # 3
sum(c(1, 2, 3))       # 6
mean(c(1, 2, 3))      # 2
max(c(1, 2, 3))       # 3
min(c(1, 2, 3))       # 1
```

### Recycling

When vectors of different lengths meet, the shorter one is **recycled**:

```r
c(1, 2, 3) + c(10, 10, 10)   # 11 12 13
c(1, 2, 3) + 1               # 2 3 4   (1 is recycled)
```

---

**Next up:** a first exercise — working with strings and vectors."""
    ),
    L(
        id="r-intro-basic-io",
        course_id="intro-to-r",
        module_id="r-intro",
        title="Reading Input and Printing Output",
        type="theory",
        order=4,
        content="""## Reading Input and Printing Output

Interactive R programs need to accept data and produce results. R reads text from **standard input** and writes to **standard output**.

### Printing output

`print()` shows a value in the console with its structure. `cat()` writes plain text without quotes or indices — ideal for program output:

```r
cat("Hello, world!\\n")          # Hello, world!
cat(42, "degrees\\n")            # 42 degrees
cat(1:3, sep = ", ", "\\n")       # 1, 2, 3
```

### Reading standard input

Use `readLines()` with a connection to stdin. `n = 1` reads one line, `warn = FALSE` suppresses a harmless warning when input is empty:

```r
line <- readLines(file("stdin"), n = 1, warn = FALSE)
```

The result is a character string. Convert it with `as.numeric()` when you need a number.

### The "read input, compute, print" pattern

A complete script that adds two numbers read from input:

```r
input <- readLines(file("stdin"), warn = FALSE)
a <- as.numeric(input[1])
b <- as.numeric(input[2])
cat(a + b, "\\n")
```

### Character helpers

```r
nchar("hello")       # 5  (length of a string)
toupper("abc")       # "ABC"
tolower("ABC")       # "abc"
substr("hello", 1, 3) # "hel"
```

`nchar()` counts characters in a string, which is different from `length()` (which counts elements in a vector).

---

**Next up:** your first exercises — greeting a user and computing vector statistics."""
    ),
    L(
        id="r-intro-exercise-greeting",
        course_id="intro-to-r",
        module_id="r-intro",
        title="Exercise: Personal Greeting",
        type="exercise",
        order=5,
        content="""## Exercise: Personal Greeting

Write a function `greet(input)` that receives the full standard input as a **string** and returns a greeting.

The input contains a name and an age, one per line, like:

```text
Ada
36
```

Return the string:

```text
Hello, Ada! You are 36 years old.
```

### How your code runs

Your function is called once per test with the raw input text. Use `strsplit(input, "\\n")` to split it into lines, then build the result with `paste()`.

### Starter code

```r
greet <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  name <- lines[1]
  age <- lines[2]
  return(paste("Hello,", name, "! You are", age, "years old."))
}
```

Adjust the starter if needed, then submit to run the tests.

Good luck!""",
        starter_code='''greet <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  name <- lines[1]
  age <- lines[2]
  return(paste("Hello,", name, "! You are", age, "years old."))
}
''',
        test_cases=[
            {"input": "Ada\n36\n", "expected_output": "Hello, Ada ! You are 36 years old.", "description": "Standard greeting"},
            {"input": "Linus\n20\n", "expected_output": "Hello, Linus ! You are 20 years old.", "description": "Another name and age"},
        ],
    ),
    L(
        id="r-intro-exercise-vector-stats",
        course_id="intro-to-r",
        module_id="r-intro",
        title="Exercise: Vector Statistics",
        type="exercise",
        order=6,
        content="""## Exercise: Vector Statistics

Write a function `stats(input)` that receives a list of numbers, one per line, and returns the **sum** and the **mean** of those numbers.

The input looks like:

```text
4
8
15
16
23
42
```

Return a single line with the sum, then a space, then the mean rounded to 2 decimal places, for example:

```text
108 18
```

### How your code runs

Split the input into lines, convert to numbers with `as.numeric()`, then compute `sum()` and `mean()`. Use `round(x, 2)` for the mean and combine with `paste()`.

### Starter code

```r
stats <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  s <- sum(nums)
  m <- round(mean(nums), 2)
  return(paste(s, m))
}
```

Good luck!""",
        starter_code='''stats <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  s <- sum(nums)
  m <- round(mean(nums), 2)
  return(paste(s, m))
}
''',
        test_cases=[
            {"input": "4\n8\n15\n16\n23\n42\n", "expected_output": "108 18", "description": "Classic data set"},
            {"input": "1\n2\n3\n4\n5\n", "expected_output": "15 3", "description": "Small sequence"},
            {"input": "7\n7\n7\n", "expected_output": "21 7", "description": "All equal"},
        ],
    ),
    L(
        id="r-intro-exercise-typecast-sum",
        course_id="intro-to-r",
        module_id="r-intro",
        title="Exercise: Sum with Type Safety",
        type="exercise",
        order=7,
        content="""## Exercise: Sum with Type Safety

Write a function `add_two(input)` that receives two numbers, one per line, and returns their sum as a plain number string.

The input looks like:

```text
3
5
```

Return:

```text
8
```

### How your code runs

Convert each line with `as.numeric()`. Note that R reads text, so even whole numbers arrive as characters.

### Edge case

If either line cannot be converted to a number, return the string `"invalid"` (this mirrors how `NA` appears when a conversion fails — check with `is.na()`).

### Starter code

```r
add_two <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  a <- as.numeric(lines[1])
  b <- as.numeric(lines[2])
  if (is.na(a) || is.na(b)) {
    return("invalid")
  }
  return(as.character(a + b))
}
```

Good luck!""",
        starter_code='''add_two <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  a <- as.numeric(lines[1])
  b <- as.numeric(lines[2])
  if (is.na(a) || is.na(b)) {
    return("invalid")
  }
  return(as.character(a + b))
}
''',
        test_cases=[
            {"input": "3\n5\n", "expected_output": "8", "description": "Small numbers"},
            {"input": "10\n20\n", "expected_output": "30", "description": "Larger numbers"},
            {"input": "-4\n9\n", "expected_output": "5", "description": "Negative operand"},
            {"input": "x\n5\n", "expected_output": "invalid", "description": "Non-numeric input"},
        ],
    ),
    # ── Module 2: Data Structures and Control Flow ──────────────────────
    L(
        id="r-structures-lists",
        course_id="intro-to-r",
        module_id="r-structures",
        title="Lists: Heterogeneous Containers",
        type="theory",
        order=1,
        content="""## Lists: Heterogeneous Containers

Unlike vectors, **lists** can hold values of different types — numbers, text, other vectors, even other lists. They are R's flexible workhorse for grouping related things.

### Building lists

```r
person <- list(
  name = "Ada",
  age = 36,
  scores = c(90, 85, 92),
  active = TRUE
)
```

### Accessing list elements

There are three different bracket operators — each does something different:

```r
person[1]      # a LIST containing the first element
person$name    # the raw VALUE "Ada"
person[["name"]]  # the raw VALUE "Ada"
person$scores[2]  # 85 — a vector inside a list
```

The single-bracket `[ ]` always returns a list; `[[ ]]` and `$` reach into the value.

### Adding and removing elements

```r
person$email <- "ada@example.com"   # add a named element
person$age <- NULL                  # remove the age element
```

### Lists in data analysis

Lists appear constantly in real R code:

- The result of a model fit is a list of coefficients, residuals, and more.
- Reading messy files often produces a list before you tidy it into a data frame.
- `strsplit()` returns a **list** — one character vector per input element.

```r
strsplit(c("a,b", "c,d"), ",")   # list of two vectors
```

### Naming conventions

Names make lists self-documenting. Prefer `person$name` over `person[[1]]` — the name tells you what the value means.

---

**Next up:** data frames — the table structure that powers most R analysis."""
    ),
    L(
        id="r-structures-dataframes",
        course_id="intro-to-r",
        module_id="r-structures",
        title="Data Frames: Tables of Data",
        type="theory",
        order=2,
        content="""## Data Frames: Tables of Data

A **data frame** is R's table: rows are observations, columns are variables. It is a special kind of list where every column is a vector of the same length.

### Building a data frame

```r
students <- data.frame(
  name = c("Ada", "Linus", "Grace"),
  score = c(92, 87, 95),
  grade = c("A", "B", "A"),
  stringsAsFactors = FALSE
)
```

### Looking at a data frame

```r
head(students)       # first 6 rows
nrow(students)       # 3
ncol(students)       # 3
dim(students)        # 3 3
names(students)      # "name" "score" "grade"
str(students)        # structure of every column
```

### Accessing columns

Columns are like named vectors:

```r
students$name        # "Ada" "Linus" "Grace"
students[["score"]]  # 92 87 95
students[, "grade"]  # all rows of the grade column
```

### Accessing rows

Use `[rows, cols]` — rows first, then columns:

```r
students[1, ]          # first row (a data frame)
students$score[2]      # 87 — second score
students[c(1, 3), ]    # rows 1 and 3
```

### Logical indexing

The `[ ]` operator accepts a logical vector to select rows that match a condition:

```r
students[students$score >= 90, ]   # rows where score is at least 90
```

### The `$` and `[[ ]]` on data frames

- `df$col` returns a **vector**.
- `df[[col]]` returns a vector too (programmatic access).
- `df[col]` returns a **data frame** with one column.

Choosing the wrong one is a classic R mistake — when you `sum()` a column, make sure you have the vector, not a one-column data frame.

---

**Next up:** conditions and loops for controlling your analysis."""
    ),
    L(
        id="r-structures-conditionals",
        course_id="intro-to-r",
        module_id="r-structures",
        title="Conditionals: if, else if, else",
        type="theory",
        order=3,
        content="""## Conditionals: if, else if, else

Programs make decisions. In R, `if` runs a block only when a condition is `TRUE`.

### The basic form

```r
temperature <- 30

if (temperature > 25) {
  cat("It is hot today\\n")
}
```

### Adding branches

```r
score <- 72

if (score >= 90) {
  grade <- "A"
} else if (score >= 75) {
  grade <- "B"
} else if (score >= 60) {
  grade <- "C"
} else {
  grade <- "F"
}
cat(grade, "\\n")
```

- `else if` chains additional conditions.
- `else` catches everything that did not match.
- Conditions are checked top to bottom; the **first** `TRUE` wins.
- `ifelse()` is a vectorized cousin: `ifelse(x > 0, "pos", "neg")` applies to every element of a vector.

### Comparison operators

| Operator | Meaning          |
|----------|------------------|
| `==`     | equal to         |
| `!=`     | not equal to     |
| `<`      | less than        |
| `>`      | greater than     |
| `<=`     | less or equal    |
| `>=`     | greater or equal |

### Combining conditions

`&` means "and", `|` means "or", `!` means "not":

```r
age <- 20
has_id <- TRUE

if (age >= 18 & has_id) {
  cat("Welcome in\\n")
}
```

### Common R gotcha: single vs double

`&` and `|` are **vectorized** (element-wise). Use the short-circuit forms `&&` and `||` inside a plain `if` when you only care about a single logical value. Mixing them up is a frequent source of confusing errors.

### NA is not FALSE

In R, `NA` means "missing", not "false". `if (NA)` errors. Always test explicitly: `if (is.na(x) | x > 5)`.

---

**Next up:** loops for repeating work."""
    ),
    L(
        id="r-structures-loops",
        course_id="intro-to-r",
        module_id="r-structures",
        title="Loops: for and while",
        type="theory",
        order=4,
        content="""## Loops: for and while

R can repeat work with `for` and `while` loops — though vectorized code usually beats them for speed, loops remain essential for many tasks.

### for loops

Iterate over each element of a vector:

```r
names <- c("Ada", "Linus", "Grace")

for (n in names) {
  cat("Hello,", n, "\\n")
}
```

### Looping over a sequence of positions

```r
for (i in 1:5) {
  cat(i, "^2 =", i^2, "\\n")
}
```

### while loops

Repeat while a condition stays `TRUE`:

```r
count <- 0
total <- 0

while (total < 100) {
  count <- count + 1
  total <- total + count
}
cat("Took", count, "steps to reach", total, "\\n")
```

### Accumulator pattern

Build up a result step by step:

```r
total <- 0
for (x in c(4, 8, 15, 16, 23, 42)) {
  total <- total + x
}
cat(total, "\\n")   # 108
```

### Infinite loop safety

`while (TRUE)` runs forever unless you `break` out of it. Use `break` to stop early and `next` to skip to the next iteration:

```r
for (i in 1:10) {
  if (i %% 2 == 0) next       # skip even numbers
  if (i > 7) break            # stop after 7
  cat(i, " ")
}
# 1 3 5 7
```

### When to prefer vectorization

`for (i in 1:n) { total <- total + x[i] }` is much slower than `sum(x)`. For simple aggregations, use the built-in vectorized functions — they are clearer and faster. Use loops when the logic is genuinely sequential.

---

**Next up:** exercises that combine data frames and control flow."""
    ),
    L(
        id="r-structures-exercise-grades",
        course_id="intro-to-r",
        module_id="r-structures",
        title="Exercise: Grade Classifier",
        type="exercise",
        order=5,
        content="""## Exercise: Grade Classifier

Write a function `classify(input)` that receives a score on one line and returns its letter grade.

Rules:

- 90 or above → `A`
- 75–89 → `B`
- 60–74 → `C`
- below 60 → `F`

### Sample

Input: `72`

Output: `C`

### How your code runs

Convert the input line with `as.numeric()`, then use `if` / `else if` / `else`. Return exactly the letter.

### Starter code

```r
classify <- function(input) {
  score <- as.numeric(input)
  if (score >= 90) {
    return("A")
  } else if (score >= 75) {
    return("B")
  } else if (score >= 60) {
    return("C")
  } else {
    return("F")
  }
}
```

Good luck!""",
        starter_code='''classify <- function(input) {
  score <- as.numeric(input)
  if (score >= 90) {
    return("A")
  } else if (score >= 75) {
    return("B")
  } else if (score >= 60) {
    return("C")
  } else {
    return("F")
  }
}
''',
        test_cases=[
            {"input": "72\n", "expected_output": "C", "description": "Mid score"},
            {"input": "95\n", "expected_output": "A", "description": "Top score"},
            {"input": "50\n", "expected_output": "F", "description": "Failing score"},
            {"input": "80\n", "expected_output": "B", "description": "B boundary"},
            {"input": "60\n", "expected_output": "C", "description": "C boundary"},
        ],
    ),
    L(
        id="r-structures-exercise-fizzbuzz",
        course_id="intro-to-r",
        module_id="r-structures",
        title="Exercise: R FizzBuzz",
        type="exercise",
        order=6,
        content="""## Exercise: R FizzBuzz

Write a function `fizzbuzz(input)` that receives a single integer `n` and returns the FizzBuzz sequence from **1 to n**, joined by spaces.

For each number:

- divisible by 3 → `Fizz`
- divisible by 5 → `Buzz`
- divisible by both → `FizzBuzz`
- otherwise → the number itself

### Sample

Input: `5`

Output: `1 2 Fizz 4 Buzz`

### How your code runs

`n` arrives as a string — convert with `as.numeric()`. Build the sequence with a `for` loop and collect results with `c()`, then join with `paste(..., collapse = " ")`.

### Starter code

```r
fizzbuzz <- function(input) {
  n <- as.numeric(input)
  out <- c()
  for (i in 1:n) {
    if (i %% 15 == 0) {
      out <- c(out, "FizzBuzz")
    } else if (i %% 3 == 0) {
      out <- c(out, "Fizz")
    } else if (i %% 5 == 0) {
      out <- c(out, "Buzz")
    } else {
      out <- c(out, as.character(i))
    }
  }
  return(paste(out, collapse = " "))
}
```

Good luck!""",
        starter_code='''fizzbuzz <- function(input) {
  n <- as.numeric(input)
  out <- c()
  for (i in 1:n) {
    if (i %% 15 == 0) {
      out <- c(out, "FizzBuzz")
    } else if (i %% 3 == 0) {
      out <- c(out, "Fizz")
    } else if (i %% 5 == 0) {
      out <- c(out, "Buzz")
    } else {
      out <- c(out, as.character(i))
    }
  }
  return(paste(out, collapse = " "))
}
''',
        test_cases=[
            {"input": "5\n", "expected_output": "1 2 Fizz 4 Buzz", "description": "Up to five"},
            {"input": "15\n", "expected_output": "1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz", "description": "Full sequence"},
            {"input": "3\n", "expected_output": "1 2 Fizz", "description": "Short sequence"},
        ],
    ),
    L(
        id="r-structures-exercise-passing",
        course_id="intro-to-r",
        module_id="r-structures",
        title="Exercise: Passing Students",
        type="exercise",
        order=7,
        content="""## Exercise: Passing Students

Write a function `passing(input)` that reads rows of `name,score` (one per line) and returns the names of students with a score of **60 or above**, in input order, joined by spaces.

### Sample

Input:

```text
Ada,92
Linus,57
Grace,88
```

Output:

```text
Ada Grace
```

### How your code runs

Split the whole input into lines, split each line on the comma with `strsplit(line, ",")`, convert the score with `as.numeric()`, and keep names where the score passes. Join the result with `paste(..., collapse = " ")`.

### Starter code

```r
passing <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  passed <- c()
  for (line in lines) {
    parts <- strsplit(line, ",")[[1]]
    name <- parts[1]
    score <- as.numeric(parts[2])
    if (!is.na(score) && score >= 60) {
      passed <- c(passed, name)
    }
  }
  return(paste(passed, collapse = " "))
}
```

Good luck!""",
        starter_code='''passing <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  passed <- c()
  for (line in lines) {
    parts <- strsplit(line, ",")[[1]]
    name <- parts[1]
    score <- as.numeric(parts[2])
    if (!is.na(score) && score >= 60) {
      passed <- c(passed, name)
    }
  }
  return(paste(passed, collapse = " "))
}
''',
        test_cases=[
            {"input": "Ada,92\nLinus,57\nGrace,88\n", "expected_output": "Ada Grace", "description": "Mixed results"},
            {"input": "Pat,60\nSam,59\n", "expected_output": "Pat", "description": "Boundary at 60"},
            {"input": "Kim,30\nLee,20\n", "expected_output": "", "description": "Nobody passes"},
        ],
    ),
    # ── Module 3: Functions and Packages ────────────────────────────────
    L(
        id="r-functions-writing",
        course_id="intro-to-r",
        module_id="r-functions",
        title="Writing Functions",
        type="theory",
        order=1,
        content="""## Writing Functions

Functions are reusable blocks of code with a name, optional inputs (arguments), and a result. They stop you repeating yourself and make analyses readable.

### Defining a function

```r
square <- function(x) {
  return(x * x)
}

print(square(5))   # 25
```

### Using the result

The value of the last evaluated expression is returned automatically, but explicit `return()` is clearer for beginners:

```r
add <- function(a, b) {
  return(a + b)
}

total <- add(3, 4)
cat(total, "\\n")   # 7
```

### Functions are values

In R a function is stored in a variable like any other value. You can reassign it, pass it to other functions, and check it:

```r
square
# function(x) { return(x * x) }
```

### Why functions matter

- **Reuse:** write once, call many times.
- **Clarity:** a well-named function reads like a sentence.
- **Testing:** small functions are easy to check in isolation.
- **Consistency:** one code path handles every call.

### Functions in this course's exercises

The exercises here ask you to write a function that takes the raw standard-input text as a single argument and returns the answer as text:

```r
count_vowels <- function(input) {
  # input is a character string
  return("the answer")
}
```

The test harness calls your function with each test's input string and compares your returned text with the expected output.

---

**Next up:** arguments, defaults, and the `...` dot-dot-dot."""
    ),
    L(
        id="r-functions-arguments",
        course_id="intro-to-r",
        module_id="r-functions",
        title="Arguments, Defaults, and ...",
        type="theory",
        order=2,
        content="""## Arguments, Defaults, and ...

Arguments let functions adapt to different inputs.

### Positional and named arguments

```r
describe <- function(name, age) {
  return(paste(name, "is", age, "years old"))
}

describe("Ada", 36)          # positional
describe(age = 36, name = "Ada")   # named — order does not matter
```

### Default values

An argument without a default must be supplied. One with a default can be omitted:

```r
greet <- function(name, punctuation = "!") {
  return(paste0("Hello, ", name, punctuation))
}

greet("Ada")          # "Hello, Ada!"
greet("Ada", "?")     # "Hello, Ada?"
```

### paste vs paste0

`paste(a, b)` joins with a space by default; `paste0(a, b)` joins with no separator:

```r
paste0("x", 1)        # "x1"
paste("x", 1)         # "x 1"
paste(c("a","b"), collapse = "")   # "ab"
```

### The ... argument

`...` captures any extra arguments and forwards them to another function — common in plotting wrappers:

```r
my_plot <- function(x, y, ...) {
  plot(x, y, main = "My Plot", ...)
}
```

### Returning early

`return()` can be used more than once to exit early:

```r
classify <- function(score) {
  if (score >= 90) return("A")
  if (score >= 75) return("B")
  return("C")
}
```

### Validating inputs

Check assumptions at the top of the function and fail fast:

```r
mean_positive <- function(x) {
  if (any(x < 0)) {
    stop("x must be non-negative")
  }
  return(mean(x))
}
```

---

**Next up:** how R finds names — environments and scope."""
    ),
    L(
        id="r-functions-scope",
        course_id="intro-to-r",
        module_id="r-functions",
        title="Scope: Where Variables Live",
        type="theory",
        order=3,
        content="""## Scope: Where Variables Live

Every variable lives in an **environment**. When a function runs, R creates a fresh environment for its local variables, separate from the global workspace.

### Local vs global

```r
message <- "global"       # global environment

shout <- function() {
  message <- "local"      # a NEW variable inside the function
  return(message)
}

shout()                   # "local"
message                   # "global"  (unchanged)
```

The assignment inside the function created a **local** variable that disappeared when the function finished.

### Reading is allowed, writing is not

A function can *read* a global variable, but assigning to the same name creates a local copy — it does not modify the global:

```r
factor <- 10

scale <- function(x) {
  factor <- factor + 1    # reads global factor (10), then makes a local
  return(x * factor)      # local factor is 11
}

print(scale(2))           # 22
print(factor)             # 10  (global untouched)
```

### The super-assignment operator <<-

`<<-` assigns to the enclosing environment instead of the current one. Use it sparingly — it makes code harder to reason about:

```r
counter <- 0

increment <- function() {
  counter <<- counter + 1   # modifies the global counter
}

increment()
print(counter)   # 1
```

### Lexical scoping

R uses **lexical scoping**: a function sees the environment where it was *defined*, not where it was called. This is what makes closures possible:

```r
make_adder <- function(n) {
  function(x) {
    return(x + n)
  }
}

add_five <- make_adder(5)
add_five(10)     # 15
```

### Tips

- Keep functions self-contained — pass data in as arguments.
- Avoid `<<-` and `assign()` in scripts; they hide data flow.
- Prefer returning values over mutating global state.

---

**Next up:** installing and using packages."""
    ),
    L(
        id="r-functions-packages",
        course_id="intro-to-r",
        module_id="r-functions",
        title="Packages: Extending R",
        type="theory",
        order=4,
        content="""## Packages: Extending R

R ships with a solid base, but its real power comes from **packages** — collections of functions, data, and documentation written by the community. The central hub is **CRAN** (the Comprehensive R Archive Network).

### Installing a package

```r
install.packages("dplyr")
```

This downloads the package and its dependencies from CRAN and installs it on your machine.

### Loading a package

Installing is a one-time step; loading happens in **every script** that uses the package:

```r
library(dplyr)
```

or, if you only need a couple of functions:

```r
dplyr::select(data, name)
```

The `package::function` syntax calls the function without loading the whole package.

### The tidyverse

The **tidyverse** is a family of packages that work together for data science: `dplyr` (data wrangling), `tidyr` (tidying), `ggplot2` (plotting), `readr` (reading files), and more. Load the family with a single call:

```r
library(tidyverse)
```

### Built-in datasets

Base R ships with datasets for practice — useful when learning:

```r
data(mtcars)
data(iris)
head(iris)
```

### Finding help

```r
?mean            # documentation for mean
help("sum")      # same thing
example(mean)    # run the built-in examples
```

`args(function_name)` shows the argument list:

```r
args(mean)   # function (x, ...)
```

### Reproducible scripts

A reproducible analysis script begins by loading every package it uses:

```r
library(dplyr)
library(ggplot2)

# ... analysis ...
```

The exercises in this course use only **base R**, so they run in the sandbox without external packages. The Data Analytics with R course introduces `dplyr` workflows conceptually.

---

**Next up:** exercises — building and combining functions."""
    ),
    L(
        id="r-functions-exercise-bmi",
        course_id="intro-to-r",
        module_id="r-functions",
        title="Exercise: BMI Calculator",
        type="exercise",
        order=5,
        content="""## Exercise: BMI Calculator

Write a function `bmi(input)` that receives a weight in kg and a height in meters, one per line, and returns the BMI rounded to **1 decimal place**.

Input:

```text
70
1.75
```

Formula: `weight / height^2` → `70 / 1.75^2 = 22.857...` → rounded to `22.9`.

### How your code runs

Convert both lines with `as.numeric()`, compute the formula, and return `as.character(round(bmi, 1))`.

### Starter code

```r
bmi <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  weight <- as.numeric(lines[1])
  height <- as.numeric(lines[2])
  value <- round(weight / height^2, 1)
  return(as.character(value))
}
```

Good luck!""",
        starter_code='''bmi <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  weight <- as.numeric(lines[1])
  height <- as.numeric(lines[2])
  value <- round(weight / height^2, 1)
  return(as.character(value))
}
''',
        test_cases=[
            {"input": "70\n1.75\n", "expected_output": "22.9", "description": "Healthy range"},
            {"input": "95\n1.80\n", "expected_output": "29.3", "description": "Higher BMI"},
            {"input": "50\n1.60\n", "expected_output": "19.5", "description": "Lower BMI"},
        ],
    ),
    L(
        id="r-functions-exercise-compose",
        course_id="intro-to-r",
        module_id="r-functions",
        title="Exercise: Composing Functions",
        type="exercise",
        order=6,
        content="""## Exercise: Composing Functions

Write two helper functions and one main function, `report(input)`:

- `square(x)` returns `x * x`
- `cube(x)` returns `x^3`
- `report(input)` reads two numbers (a and b, one per line) and returns a single line: `square(a)` and `cube(b)` joined by a space.

### Sample

Input:

```text
3
2
```

Output:

```text
9 8
```

### How your code runs

The harness calls `report` with the raw input text. Inside `report`, call your `square` and `cube` helpers — a small taste of building larger programs from smaller functions.

### Starter code

```r
square <- function(x) {
  return(x * x)
}

cube <- function(x) {
  return(x^3)
}

report <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  a <- as.numeric(lines[1])
  b <- as.numeric(lines[2])
  return(paste(square(a), cube(b)))
}
```

Good luck!""",
        starter_code='''square <- function(x) {
  return(x * x)
}

cube <- function(x) {
  return(x^3)
}

report <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  a <- as.numeric(lines[1])
  b <- as.numeric(lines[2])
  return(paste(square(a), cube(b)))
}
''',
        test_cases=[
            {"input": "3\n2\n", "expected_output": "9 8", "description": "Basic compose"},
            {"input": "0\n5\n", "expected_output": "0 125", "description": "Zero and larger"},
            {"input": "-2\n4\n", "expected_output": "4 64", "description": "Negative input"},
        ],
    ),
    L(
        id="r-functions-exercise-default-args",
        course_id="intro-to-r",
        module_id="r-functions",
        title="Exercise: Exponent with Default",
        type="exercise",
        order=7,
        content="""## Exercise: Exponent with Default

Write a function `power(input)` that receives a base and an exponent, one per line, and returns `base^exponent`.

Input:

```text
2
10
```

Output:

```text
1024
```

### How your code runs

The exponent line may be **empty** (a blank line). In that case use the default exponent of `2`. Use `nchar()` to detect the blank line before converting.

### Starter code

```r
power <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  base <- as.numeric(lines[1])
  exponent_text <- lines[2]
  if (is.na(exponent_text) || nchar(trimws(exponent_text)) == 0) {
    exponent <- 2
  } else {
    exponent <- as.numeric(exponent_text)
  }
  return(as.character(base^exponent))
}
```

Good luck!""",
        starter_code='''power <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  base <- as.numeric(lines[1])
  exponent_text <- lines[2]
  if (is.na(exponent_text) || nchar(trimws(exponent_text)) == 0) {
    exponent <- 2
  } else {
    exponent <- as.numeric(exponent_text)
  }
  return(as.character(base^exponent))
}
''',
        test_cases=[
            {"input": "2\n10\n", "expected_output": "1024", "description": "Explicit exponent"},
            {"input": "3\n\n", "expected_output": "9", "description": "Default exponent of 2"},
            {"input": "5\n0\n", "expected_output": "1", "description": "Zero exponent"},
        ],
    ),
    # ── Module 4: Data Cleaning with R ──────────────────────────────────
    L(
        id="r-cleaning-missing",
        course_id="intro-to-r",
        module_id="r-cleaning",
        title="Handling Missing Values",
        type="theory",
        order=1,
        content="""## Handling Missing Values

Real data is messy — and the most common mess is **missing values**. In R, missing values are represented by `NA` (not available).

### Where NA comes from

- Empty cells in a CSV.
- Failed conversions (`as.numeric("abc")` → `NA`).
- Calculations that have no sensible answer.

### Detecting NA

```r
x <- c(1, 2, NA, 4)
is.na(x)          # FALSE FALSE TRUE FALSE
anyNA(x)          # TRUE
sum(is.na(x))     # 1
```

### The trap: NA spreads

Most functions return `NA` if any input is `NA`:

```r
mean(c(1, 2, NA))        # NA
sum(c(1, 2, NA))         # NA
```

### Removing NA

Use `na.rm = TRUE` where the function supports it:

```r
mean(c(1, 2, NA), na.rm = TRUE)   # 1.5
```

Or drop missing elements entirely:

```r
x <- c(1, 2, NA, 4)
na.omit(x)        # 1 2 4
```

### Checking for NA in conditions

`NA` is not `FALSE`, so `if (x == NA)` never works — you must use `is.na()`:

```r
if (is.na(value)) {
  value <- 0
}
```

### Imputation strategies

Replacing missing values with a reasonable guess is called **imputation**:

```r
x[is.na(x)] <- 0            # fill with zero
x[is.na(x)] <- mean(x, na.rm = TRUE)   # fill with the mean
```

### Empty strings vs NA

An empty cell in a CSV often arrives as an empty string `""`, not `NA`. Treat them both as missing when cleaning:

```r
cleaned <- ifelse(x == "" | is.na(x), NA, x)
```

---

**Next up:** fixing types and inconsistent values."""
    ),
    L(
        id="r-cleaning-types",
        course_id="intro-to-r",
        module_id="r-cleaning",
        title="Fixing Types and Inconsistent Values",
        type="theory",
        order=2,
        content="""## Fixing Types and Inconsistent Values

Columns often arrive as text when you need numbers, or with stray characters that break parsing. Cleaning means making the data **typed and consistent**.

### Numbers stored as text

```r
prices <- c("9.99", "12.50", "8")
as.numeric(prices)     # 9.99 12.50 8.00
```

### The problem of unexpected text

`as.numeric("9.99")` works, but `as.numeric("$9.99")` returns `NA`. Strip junk before converting:

```r
clean_num <- function(x) {
  x <- gsub("$", "", x, fixed = TRUE)   # remove dollar signs
  x <- gsub(",", "", x, fixed = TRUE)   # remove thousands separators
  return(as.numeric(x))
}
```

### Whitespace

Trailing spaces are invisible but break comparisons. Trim them:

```r
trimws("  hello  ")     # "hello"
trimws(c(" a ", "b "))  # "a" "b"
```

### Case consistency

Names like `"ada"`, `"Ada"`, and `"ADA"` are different strings. Normalize to one case:

```r
tolower(c("Ada", "ADA", "ada"))    # "ada" "ada" "ada"
```

### Factors vs characters

`read.csv()` may turn text columns into factors. Modern R defaults to characters with `stringsAsFactors = FALSE`; convert either way when you need plain text:

```r
as.character(factor("a", levels = c("a", "b")))   # "a"
```

### Dates

Dates need explicit conversion — R stores them as `Date` objects, not strings:

```r
as.Date("2024-01-15")            # 2024-01-15
as.Date("15/01/2024", format = "%d/%m/%Y")
```

### A cleaning checklist

1. Trim whitespace with `trimws()`.
2. Normalize case with `tolower()` / `toupper()`.
3. Remove currency/thousand separators.
4. Convert with `as.numeric()` / `as.Date()`.
5. Detect stragglers with `is.na()` after conversion — they reveal format problems.

---

**Next up:** filtering rows that matter."""
    ),
    L(
        id="r-cleaning-filter",
        course_id="intro-to-r",
        module_id="r-cleaning",
        title="Filtering and Selecting Data",
        type="theory",
        order=3,
        content="""## Filtering and Selecting Data

Cleaning often means keeping only the rows and columns you need. R's subsetting operators make this a one-liner.

### Filtering rows with a condition

```r
df[df$age >= 18, ]
df[df$status == "active", ]
df[df$score > 50 & df$group == "A", ]
```

The comma inside `[ ]` separates rows (before) from columns (after). Leaving the column slot empty keeps all columns.

### Combining conditions

```r
# Active adults
df[df$status == "active" & df$age >= 18, ]

# Either condition
df[df$score > 90 | df$category == "bonus", ]
```

### Selecting columns

```r
df[, "name"]          # one column as a vector
df[, c("name", "score")]   # a data frame with two columns
df[, -c(1, 3)]        # drop columns 1 and 3
```

### Avoiding the NA trap in filters

A row with a missing score fails every comparison, including `df$score < 50` (the result is `NA`, which is treated as not selected). Decide what missing should mean and make it explicit:

```r
df[is.na(df$score) | df$score < 50, ]   # include missing as failures
```

### The subset() helper

`subset()` reads a little more naturally and drops `NA` rows automatically:

```r
subset(df, score >= 60)
```

### Comparing with %in%

`%in%` tests membership in a set — handy for filtering to a shortlist:

```r
df[df$name %in% c("Ada", "Grace"), ]
```

### Order matters

Filter first, then compute. Aggregating a column before removing bad rows gives wrong answers, so always clean before you summarize.

---

**Next up:** transforming values across a column."""
    ),
    L(
        id="r-cleaning-transform",
        course_id="intro-to-r",
        module_id="r-cleaning",
        title="Transforming Values",
        type="theory",
        order=4,
        content="""## Transforming Values

Filtering removes bad rows; **transforming** changes the values themselves. R makes vectorized transformations concise.

### Arithmetic on columns

```r
df$price_per_unit <- df$price / df$quantity
df$doubled <- df$score * 2
```

### ifelse for conditional transformation

`ifelse()` applies a choice element-wise:

```r
df$grade <- ifelse(df$score >= 60, "pass", "fail")
df$category <- ifelse(df$score > 90, "excellent", "ok")
```

### Categorizing with cut()

`cut()` slices a numeric vector into ranges:

```r
cut(df$score, breaks = c(0, 60, 75, 90, 100),
    labels = c("F", "C", "B", "A"))
```

### Replacing values

```r
df$status[df$status == "actve"] <- "active"   # fix a typo
df$status[df$status == ""] <- "unknown"
```

### Normalizing with scaling

Bring different scales onto a common range (0–1):

```r
scaled <- (df$score - min(df$score)) / (max(df$score) - min(df$score))
```

And the z-score standardizes by the mean and standard deviation:

```r
z <- (df$score - mean(df$score)) / sd(df$score)
```

### Working with character columns

```r
df$name_upper <- toupper(df$name)
df$short <- substr(df$name, 1, 3)
```

### The mutate mindset

Think of transformation as producing **new columns** from existing ones while keeping the original data intact. That way you can always trace where a value came from.

---

**Next up:** exercises — missing values, typecasting, and outliers."""
    ),
    L(
        id="r-cleaning-exercise-missing",
        course_id="intro-to-r",
        module_id="r-cleaning",
        title="Exercise: Missing Value Report",
        type="exercise",
        order=5,
        content="""## Exercise: Missing Value Report

Write a function `missing_report(input)` that reads a single column of numbers (one per line, where some lines may be blank or contain `NA`) and returns the number of missing values and the mean of the **valid** values, rounded to 2 decimal places, joined by a space.

### Sample

Input:

```text
4
NA
8

15
```

Output:

```text
2 9
```

Here two values are missing (`NA` and the blank line), and the valid values `4, 8, 15` have mean `9`.

### How your code runs

Convert every line with `as.numeric()`. Lines that fail produce `NA`. Count them with `sum(is.na(...))`. Compute the mean of the valid values with `na.rm = TRUE`.

### Starter code

```r
missing_report <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  missing <- sum(is.na(nums))
  m <- round(mean(nums, na.rm = TRUE), 2)
  return(paste(missing, m))
}
```

Good luck!""",
        starter_code='''missing_report <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  missing <- sum(is.na(nums))
  m <- round(mean(nums, na.rm = TRUE), 2)
  return(paste(missing, m))
}
''',
        test_cases=[
            {"input": "4\nNA\n8\n\n15\n", "expected_output": "2 9", "description": "NA and blank"},
            {"input": "1\n2\n3\n", "expected_output": "0 2", "description": "No missing"},
            {"input": "NA\nNA\n10\n", "expected_output": "2 10", "description": "Two missing"},
        ],
    ),
    L(
        id="r-cleaning-exercise-clean-prices",
        course_id="intro-to-r",
        module_id="r-cleaning",
        title="Exercise: Cleaning Price Strings",
        type="exercise",
        order=6,
        content="""## Exercise: Cleaning Price Strings

Write a function `total_prices(input)` that reads a list of price strings (one per line) like `$9.99` or `12,50` and returns their **sum** rounded to 2 decimal places.

### Sample

Input:

```text
$9.99
12.50
$8
```

Output:

```text
30.49
```

### How your code runs

For each line, remove `$` and `,` characters with `gsub()`, convert with `as.numeric()`, and sum. Skip lines that fail to convert (`is.na()`). Round the total to 2 decimal places.

### Starter code

```r
total_prices <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  total <- 0
  for (line in lines) {
    clean <- gsub("[$ ,]", "", line)
    value <- as.numeric(clean)
    if (!is.na(value)) {
      total <- total + value
    }
  }
  return(as.character(round(total, 2)))
}
```

Good luck!""",
        starter_code='''total_prices <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  total <- 0
  for (line in lines) {
    clean <- gsub("[$ ,]", "", line)
    value <- as.numeric(clean)
    if (!is.na(value)) {
      total <- total + value
    }
  }
  return(as.character(round(total, 2)))
}
''',
        test_cases=[
            {"input": "$9.99\n12.50\n$8\n", "expected_output": "30.49", "description": "Mixed formats"},
            {"input": "1,000\n2,000\n", "expected_output": "3000", "description": "Thousands separators"},
            {"input": "n/a\n5.5\n", "expected_output": "5.5", "description": "Skipping invalid"},
        ],
    ),
    L(
        id="r-cleaning-exercise-outlier",
        course_id="intro-to-r",
        module_id="r-cleaning",
        title="Exercise: Outlier Filter",
        type="exercise",
        order=7,
        content="""## Exercise: Outlier Filter

Write a function `outlier_filter(input)` that reads a column of numbers and returns the count of values that are **not** outliers, where an outlier is any value below `q1 - 1.5 * iqr` or above `q3 + 1.5 * iqr`.

Compute `q1 = quantile(nums, 0.25)`, `q3 = quantile(nums, 0.75)`, and `iqr = q3 - q1`. Exclude any `NA` values first.

### Sample

Input:

```text
1
2
3
4
5
100
```

Output:

```text
5
```

The value `100` is far above the rest and is flagged as an outlier, leaving 5 non-outliers.

### How your code runs

Drop `NA`s, compute the quartiles with `quantile(..., na.rm = TRUE)`, then count values inside the fences with `sum(value >= lower & value <= upper)`.

### Starter code

```r
outlier_filter <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  q1 <- quantile(nums, 0.25)
  q3 <- quantile(nums, 0.75)
  iqr <- q3 - q1
  lower <- q1 - 1.5 * iqr
  upper <- q3 + 1.5 * iqr
  return(as.character(sum(nums >= lower & nums <= upper)))
}
```

Good luck!""",
        starter_code='''outlier_filter <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  q1 <- quantile(nums, 0.25)
  q3 <- quantile(nums, 0.75)
  iqr <- q3 - q1
  lower <- q1 - 1.5 * iqr
  upper <- q3 + 1.5 * iqr
  return(as.character(sum(nums >= lower & nums <= upper)))
}
''',
        test_cases=[
            {"input": "1\n2\n3\n4\n5\n100\n", "expected_output": "5", "description": "Single outlier"},
            {"input": "1\n1\n1\n1\n1\n", "expected_output": "5", "description": "No outliers"},
            {"input": "1\n2\n3\n4\n5\n6\n7\n8\n100\n200\n", "expected_output": "8", "description": "Two outliers"},
        ],
    ),
    # ── Module 5: Visualization and Mini Project ────────────────────────
    L(
        id="r-viz-base-plots",
        course_id="intro-to-r",
        module_id="r-viz",
        title="Base R Plots",
        type="theory",
        order=1,
        content="""## Base R Plots

R was built to visualize data. Base R provides fast, no-frills plotting functions that work with zero setup.

### Scatter plots with plot()

```r
plot(x = iris$Sepal.Length, y = iris$Petal.Length)
```

### Line charts

```r
sales <- c(120, 180, 150, 220, 260)
plot(sales, type = "l", col = "steelblue", lwd = 2)
```

`type = "l"` draws a line; `type = "b"` draws both points and lines.

### Bar charts with barplot()

```r
barplot(c(40, 30, 20), names.arg = c("A", "B", "C"))
```

### Histograms with hist()

A histogram shows the distribution of one numeric variable:

```r
hist(iris$Sepal.Length, breaks = 12, col = "lightblue",
     main = "Distribution of Sepal Length")
```

### Box plots with boxplot()

A box plot summarizes the median, quartiles, and outliers:

```r
boxplot(Petal.Length ~ Species, data = iris)
```

### Labels matter

```r
plot(x, y,
     main = "Title",
     xlab = "Horizontal label",
     ylab = "Vertical label")
```

### Customizing

Common arguments: `col` (color), `pch` (point shape), `cex` (size), `lwd` (line width), `ylim`/`xlim` (axis ranges).

### Which chart for which question?

| Goal                         | Chart                          |
|------------------------------|--------------------------------|
| Relationship between two vars | scatter plot (`plot`)           |
| Change over time             | line chart (`type = "l"`)      |
| Compare categories           | bar chart (`barplot`)          |
| Distribution of one variable | histogram (`hist`)             |
| Median/quartiles by group    | box plot (`boxplot`)           |

---

**Next up:** ggplot2 — the grammar of graphics."""
    ),
    L(
        id="r-viz-ggplot",
        course_id="intro-to-r",
        module_id="r-viz",
        title="ggplot2: The Grammar of Graphics",
        type="theory",
        order=2,
        content="""## ggplot2: The Grammar of Graphics

**ggplot2** is the most popular R plotting package. Its philosophy — the *grammar of graphics* — builds every chart from the same pieces: data, aesthetic mappings, and geometric layers.

### The building blocks

```r
library(ggplot2)

ggplot(iris, aes(x = Sepal.Length, y = Petal.Length)) +
  geom_point()
```

- `ggplot(data, aes(...))` — the data and which columns map to which aesthetics (`x`, `y`, `color`, `size`).
- `+` layers — each `geom_*()` adds a visual representation.

### Common geometries

```r
geom_point()     # scatter
geom_line()      # line
geom_bar()       # bars (counts)
geom_histogram() # histograms
geom_boxplot()   # box plots
```

### Mapping data to aesthetics

```r
ggplot(iris, aes(x = Sepal.Length, y = Petal.Length, color = Species)) +
  geom_point(size = 3)
```

### Adding labels and themes

```r
ggplot(iris, aes(x = Sepal.Length, y = Petal.Length, color = Species)) +
  geom_point() +
  labs(title = "Iris Dimensions",
       x = "Sepal Length (cm)",
       y = "Petal Length (cm)") +
  theme_minimal()
```

### A bar chart of counts

```r
ggplot(mtcars, aes(x = factor(cyl))) +
  geom_bar() +
  labs(x = "Cylinders", y = "Count")
```

### The %>% pipe

The pipe `|>` (base R 4.1+) and `%>%` (magrittr) feed a value into the first argument of the next call, making data pipelines readable:

```r
iris |>
  subset(Species == "setosa") |>
  summary()
```

### Why ggplot2 wins for real projects

- Layering makes complex charts modular.
- Consistent syntax across every chart type.
- Themes and scales are highly customizable.
- It composes perfectly with tidyverse wrangling.

> The sandbox for these exercises uses base R only, so your runnable exercises use `barplot`/`plot`/`cat` — but the concepts carry directly into ggplot2.

---

**Next up:** reading data into R from files."""
    ),
    L(
        id="r-viz-reading-data",
        course_id="intro-to-r",
        module_id="r-viz",
        title="Reading Data into R",
        type="theory",
        order=3,
        content="""## Reading Data into R

Analysis starts with getting data into R. The classic function is `read.csv()`.

### Reading a CSV

```r
sales <- read.csv("sales.csv")
head(sales)          # preview the first 6 rows
str(sales)           # check the column types
```

### Reading from a text string

For quick experiments you can read directly from a character vector:

```r
text <- "name,score
Ada,92
Linus,57
Grace,88
"
df <- read.csv(text = text, stringsAsFactors = FALSE)
```

### Tidyverse alternative

`readr`'s `read_csv()` is faster and usually guesses types better:

```r
library(readr)
sales <- read_csv("sales.csv")
```

### Checking what you loaded

```r
dim(df)          # rows, columns
names(df)        # column names
summary(df)      # min/max/mean per column
```

### Writing data out

```r
write.csv(df, "cleaned.csv", row.names = FALSE)
```

### Working directories

`read.csv("sales.csv")` looks in the current working directory. Check and set it with:

```r
getwd()
setwd("/path/to/project")
```

Better still, use RStudio **projects**, which anchor every path to the project root.

### A note on separators

- `read.csv()` assumes commas.
- `read.csv2()` assumes semicolons (common in European files).
- `read.delim()` lets you pass any separator via `sep =`.

### The golden rule

Always inspect data **immediately** after loading — `head()`, `str()`, `summary()` — before running any analysis. Most bugs in analysis come from wrong assumptions about the loaded data.

---

**Next up:** interpreting charts and communicating findings."""
    ),
    L(
        id="r-viz-interpreting",
        course_id="intro-to-r",
        module_id="r-viz",
        title="Interpreting Charts and Telling the Story",
        type="theory",
        order=4,
        content="""## Interpreting Charts and Telling the Story

A chart's real job is communication. Reading it correctly — and explaining what it means — is a core data skill.

### Reading a histogram

A histogram shows where values concentrate. Ask:

- Where is the **center** (the typical value)?
- How **spread out** are the values?
- Is the shape **symmetric** or **skewed**?
- Are there **gaps** or separate peaks?

```r
hist(iris$Sepal.Width, breaks = 12)
```

### Reading a box plot

The box spans the interquartile range (IQR, the middle 50% of data); the line inside is the **median**; the whiskers reach to the last values within `1.5 × IQR`; dots beyond are **outliers**.

### Reading a scatter plot

Look for a **relationship**: does `y` tend to rise (positive) or fall (negative) as `x` grows? Is the pattern strong or noisy?

### Correlation vs causation

Two variables can move together without one causing the other. A chart showing ice-cream sales rising with drowning incidents does *not* prove a link — the shared cause is summer. Always be careful claiming causation from association.

### Summarizing what you see

Good chart commentary follows a pattern:

1. **Claim** — the main takeaway.
2. **Evidence** — what in the chart supports it.
3. **Caveat** — data limitations or alternative explanations.

> Example: *"Scores cluster between 60 and 80 (evidence: histogram peak), though a few students scored below 40, suggesting the material was harder for a subgroup (caveat: small sample)."*

### The five-second rule

A reader should grasp the message within five seconds. If they cannot, the chart is doing the wrong job — title, labels, and a clean axis range matter as much as the data itself.

---

**Next up:** two interpretation exercises and the course mini project."""
    ),
    L(
        id="r-viz-exercise-bar-summary",
        course_id="intro-to-r",
        module_id="r-viz",
        title="Exercise: Category Summary",
        type="exercise",
        order=5,
        content="""## Exercise: Category Summary

Write a function `category_summary(input)` that reads rows of `category,value` and returns, for each **distinct** category, the mean of its values as `category:mean` — one per line, in first-appearance order, means rounded to 2 decimal places.

### Sample

Input:

```text
A,10
B,20
A,30
B,40
```

Output:

```text
A:20
B:30
```

### How your code runs

Split into lines, then split each line on the comma. Track category means with a small loop, counting values per category. Round each mean with `round(x, 2)` and join lines with `"\\n"`.

### Starter code

```r
category_summary <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  categories <- c()
  sums <- c()
  counts <- c()
  for (line in lines) {
    parts <- strsplit(line, ",")[[1]]
    cat_name <- parts[1]
    value <- as.numeric(parts[2])
    idx <- match(cat_name, categories)
    if (is.na(idx)) {
      categories <- c(categories, cat_name)
      sums <- c(sums, value)
      counts <- c(counts, 1)
    } else {
      sums[idx] <- sums[idx] + value
      counts[idx] <- counts[idx] + 1
    }
  }
  out <- c()
  for (i in seq_along(categories)) {
    out <- c(out, paste0(categories[i], ":", round(sums[i] / counts[i], 2)))
  }
  return(paste(out, collapse = "\\n"))
}
```

Good luck!""",
        starter_code='''category_summary <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  categories <- c()
  sums <- c()
  counts <- c()
  for (line in lines) {
    parts <- strsplit(line, ",")[[1]]
    cat_name <- parts[1]
    value <- as.numeric(parts[2])
    idx <- match(cat_name, categories)
    if (is.na(idx)) {
      categories <- c(categories, cat_name)
      sums <- c(sums, value)
      counts <- c(counts, 1)
    } else {
      sums[idx] <- sums[idx] + value
      counts[idx] <- counts[idx] + 1
    }
  }
  out <- c()
  for (i in seq_along(categories)) {
    out <- c(out, paste0(categories[i], ":", round(sums[i] / counts[i], 2)))
  }
  return(paste(out, collapse = "\\n"))
}
''',
        test_cases=[
            {"input": "A,10\nB,20\nA,30\nB,40\n", "expected_output": "A:20\nB:30", "description": "Two categories"},
            {"input": "X,5\nX,5\nX,5\n", "expected_output": "X:5", "description": "Single category"},
            {"input": "a,1\nb,2\nc,3\n", "expected_output": "a:1\nb:2\nc:3", "description": "Three categories"},
        ],
    ),
    L(
        id="r-viz-exercise-reading-plot",
        course_id="intro-to-r",
        module_id="r-viz",
        title="Exercise: Interpreting a Distribution",
        type="exercise",
        order=6,
        content="""## Exercise: Interpreting a Distribution

Write a function `distribution(input)` that reads a column of numbers and returns three statistics that summarize its distribution: the **minimum**, the **median**, and the **maximum**, joined by spaces, each rounded to 2 decimal places.

### Sample

Input:

```text
1
2
3
4
5
```

Output:

```text
1 3 5
```

### How your code runs

Convert the lines with `as.numeric()`, drop `NA`s, and use `min()`, `median()`, and `max()`. These are exactly the numbers a box plot's whiskers and median line would show.

### Starter code

```r
distribution <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  lo <- round(min(nums), 2)
  mid <- round(median(nums), 2)
  hi <- round(max(nums), 2)
  return(paste(lo, mid, hi))
}
```

Good luck!""",
        starter_code='''distribution <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  lo <- round(min(nums), 2)
  mid <- round(median(nums), 2)
  hi <- round(max(nums), 2)
  return(paste(lo, mid, hi))
}
''',
        test_cases=[
            {"input": "1\n2\n3\n4\n5\n", "expected_output": "1 3 5", "description": "Sequential"},
            {"input": "10\n20\n30\n", "expected_output": "10 20 30", "description": "Simple"},
            {"input": "5\n5\n5\n5\n", "expected_output": "5 5 5", "description": "All equal"},
        ],
    ),
    L(
        id="r-viz-project",
        course_id="intro-to-r",
        module_id="r-viz",
        title="Mini Project: Sales Analysis",
        type="exercise",
        order=7,
        content="""## Mini Project: Sales Analysis

You run a small shop and record daily sales by product category. Write a function `sales_analysis(input)` that reads rows of `category,sales` and returns the category with the **highest total sales**, plus its total, in the format `category:total`.

### Sample

Input:

```text
books,120
toys,90
books,80
toys,150
food,60
```

Output:

```text
toys:240
```

### Requirements

- Totals are integer sums, so no rounding is needed.
- If two categories tie for the highest total, return the one that appears **first** in the input.

### How your code runs

Accumulate totals per category (like the earlier `category_summary` exercise), then find the maximum with `max()` and locate its index with `which.max()` (which returns the first match — perfect for the tie-break rule).

### Starter code

```r
sales_analysis <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  categories <- c()
  totals <- c()
  for (line in lines) {
    parts <- strsplit(line, ",")[[1]]
    cat_name <- parts[1]
    value <- as.numeric(parts[2])
    idx <- match(cat_name, categories)
    if (is.na(idx)) {
      categories <- c(categories, cat_name)
      totals <- c(totals, value)
    } else {
      totals[idx] <- totals[idx] + value
    }
  }
  best <- which.max(totals)
  return(paste0(categories[best], ":", totals[best]))
}
```

This project ties together string splitting, accumulation, indexing, and a decision rule — the whole course in one function.

Good luck!""",
        starter_code='''sales_analysis <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  categories <- c()
  totals <- c()
  for (line in lines) {
    parts <- strsplit(line, ",")[[1]]
    cat_name <- parts[1]
    value <- as.numeric(parts[2])
    idx <- match(cat_name, categories)
    if (is.na(idx)) {
      categories <- c(categories, cat_name)
      totals <- c(totals, value)
    } else {
      totals[idx] <- totals[idx] + value
    }
  }
  best <- which.max(totals)
  return(paste0(categories[best], ":", totals[best]))
}
''',
        test_cases=[
            {"input": "books,120\ntoys,90\nbooks,80\ntoys,150\nfood,60\n", "expected_output": "toys:240", "description": "Clear winner"},
            {"input": "a,10\nb,10\nc,5\n", "expected_output": "a:10", "description": "Tie broken by first appearance"},
            {"input": "solo,42\n", "expected_output": "solo:42", "description": "Single category"},
        ],
    ),
]
