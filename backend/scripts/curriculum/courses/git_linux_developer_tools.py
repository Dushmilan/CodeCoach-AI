"""Git and Linux Developer Tools — curriculum content module."""

COURSE = {
    "id": "git-linux-developer-tools",
    "title": "Git and Linux Developer Tools",
    "description": (
        "Command-line fundamentals, shell automation, version control with Git, "
        "debugging and system tooling, and a team collaboration workflow. Every "
        "concept is paired with hands-on bash exercises you can run right here "
        "using only shell built-ins and coreutils."
    ),
    "language": "bash",
    "icon": "terminal",
    "order": 12,
}

MODULES = [
    {
        "id": "tools-cli",
        "course_id": "git-linux-developer-tools",
        "title": "Command Line Fundamentals",
        "description": "Get comfortable in the terminal: the shell, navigating the filesystem, working with files, and chaining commands with pipes.",
        "order": 1,
    },
    {
        "id": "tools-shell",
        "course_id": "git-linux-developer-tools",
        "title": "Shell Automation",
        "description": "Turn one-off commands into repeatable scripts with variables, conditionals, and loops.",
        "order": 2,
    },
    {
        "id": "tools-git",
        "course_id": "git-linux-developer-tools",
        "title": "Git Fundamentals",
        "description": "Track every change: initialize repositories, commit snapshots, branch, merge, and work with remote repositories.",
        "order": 3,
    },
    {
        "id": "tools-debugging",
        "course_id": "git-linux-developer-tools",
        "title": "Debugging and Tooling",
        "description": "Read errors and exit codes, search logs with grep, inspect running processes, and debug your own scripts.",
        "order": 4,
    },
    {
        "id": "tools-collab",
        "course_id": "git-linux-developer-tools",
        "title": "Collaboration Project",
        "description": "Bring it all together in a team workflow: branches, pull requests, review, conflict resolution, and releases.",
        "order": 5,
    },
]

_BASH = "bash"


def L(**kw):
    kw.setdefault("language", _BASH)
    return kw


LESSONS = [
    # ── Module 1: Command Line Fundamentals ─────────────────────────────
    L(
        id="tools-cli-what-is",
        course_id="git-linux-developer-tools",
        module_id="tools-cli",
        title="What Is the Command Line?",
        type="theory",
        order=1,
        content="""## What Is the Command Line?

The **command line** (also called the terminal or shell) is a text-based interface for controlling your computer. Instead of clicking buttons, you type commands and the shell executes them. It is the foundation of a developer's toolkit because it is fast, scriptable, and identical on every machine.

### The shell

The shell is the program that reads your commands. The most common one on Linux is **Bash** (the Bourne Again SHell). Your prompt usually ends with `$` and waits for input:

```bash
dushmilan@devbox:~$
```

Type a command and press Enter to run it. Here are your first three:

```bash
pwd       # print working directory — where am I?
ls        # list files in the current directory
echo hi   # print text back to you
```

### Anatomy of a command

Commands have three parts:

| Part      | Example          | Meaning                          |
|-----------|------------------|----------------------------------|
| command   | `ls`             | the program to run               |
| options   | `-l`, `-a`       | flags that change behavior       |
| arguments | `src`            | what the command operates on     |

```bash
ls -l src
```

- `ls` lists directory contents.
- `-l` gives a long, detailed listing.
- `src` is the directory to list.

### Getting help

Every command usually has manual pages:

```bash
man ls
```

Press `q` to quit the manual. If you forget the exact syntax, `ls --help` usually prints a short summary.

### The command line is a program

Everything in the terminal is a program with **standard input** (stdin, where data comes from), **standard output** (stdout, where results go), and **standard error** (stderr). You will use these three streams constantly.

---

**Next up:** navigating the filesystem with `pwd`, `ls`, and `cd`."""
    ),
    L(
        id="tools-cli-navigation",
        course_id="git-linux-developer-tools",
        module_id="tools-cli",
        title="Navigating the Filesystem",
        type="theory",
        order=2,
        content="""## Navigating the Filesystem

Your files live in a tree of directories. The shell keeps you in exactly one directory at a time, called the **current working directory**.

### Where am I?

```bash
pwd          # prints, e.g., /home/dushmilan/projects
```

### Listing contents

```bash
ls           # names only
ls -l        # long format: permissions, owner, size, date
ls -a        # include hidden files (start with a dot)
ls -la       # combine both
```

### Moving around

```bash
cd projects   # enter the projects directory
cd ..         # go up one level
cd ~          # go to your home directory
cd -          # go back to the previous directory
```

The special entries are `.` (the current directory) and `..` (its parent).

### Absolute vs relative paths

A **relative path** is resolved from where you are right now:

```bash
cd projects/website/src
```

An **absolute path** starts with `/` and means the same thing no matter where you are:

```bash
cd /home/dushmilan/projects/website/src
```

### Tab completion

The terminal's best friend: press **Tab** to auto-complete a file or directory name. Press Tab twice to see all matches. This saves you from typing long paths and from typos.

### The home directory shortcut

`~` always expands to your home directory:

```bash
ls ~/Downloads
```

Navigating well is the difference between a fluent terminal user and someone who fights the filesystem. Practice moving around until `cd`, `pwd`, and `ls` feel automatic.

---

**Next up:** creating and manipulating files and directories."""
    ),
    L(
        id="tools-cli-files",
        course_id="git-linux-developer-tools",
        module_id="tools-cli",
        title="Working with Files",
        type="theory",
        order=3,
        content="""## Working with Files

Files and directories are the raw material of every project. Here are the commands you will use every single day.

### Creating things

```bash
mkdir my_project        # make a directory
touch notes.md          # create an empty file (or update its timestamp)
```

### Copying, moving, renaming, deleting

```bash
cp notes.md backup.md   # copy
mv notes.md notes.txt   # rename / move
rm notes.txt            # delete (no recycle bin — be careful!)
rm -r my_project        # delete a directory and everything inside
```

- `cp -r` copies directories recursively.
- `mv` is also how you rename a file.
- `rm -rf` is famously dangerous: it deletes recursively and never asks twice.

### Inspecting files

```bash
file notes.md           # what kind of file is it?
ls -l notes.md          # size, permissions, modification time
stat notes.md           # detailed metadata
```

### Wildcards

The shell expands **globs** before running the command:

```bash
ls *.py                 # every .py file
cp src/*.py backup/     # all Python files into backup/
rm *.tmp                # delete every .tmp file
```

`*` matches anything, `?` matches a single character, and `[abc]` matches one of the listed characters.

### Hidden files

Files that start with a dot are hidden from plain `ls`. Many tools keep their configuration here:

```bash
ls -a        # now you see .git, .env, .config and friends
```

### Text files are everywhere

Configuration files, source code, logs, and build scripts are all text. `cat` prints a file to the screen, and `wc` counts its lines, words, and characters:

```bash
cat README.md
wc README.md
```

Getting comfortable creating, moving, and deleting files is a prerequisite for everything that follows in this course.

---

**Next up:** reading file content and connecting commands with pipes."""
    ),
    L(
        id="tools-cli-pipes",
        course_id="git-linux-developer-tools",
        module_id="tools-cli",
        title="Input, Output, and Pipes",
        type="theory",
        order=4,
        content="""## Input, Output, and Pipes

The real power of the command line is that every program reads from **standard input** and writes to **standard output**. You can connect programs so one command's output becomes the next command's input.

### Viewing files without reading everything

```bash
cat file.txt        # dump the whole file
head -5 file.txt    # first 5 lines
tail -10 file.txt   # last 10 lines
less file.txt       # scroll through a big file (press q to quit)
```

### The pipe operator

The pipe `|` sends the left command's stdout to the right command's stdin:

```bash
ls | wc -l          # how many files are here?
cat log.txt | grep error   # only the error lines
history | tail -20  # your most recent commands
```

This is a **pipeline**: a chain of small tools, each doing one job well.

### Redirecting output

Instead of printing to the screen, you can send output into a file:

```bash
ls > files.txt              # overwrite files.txt with the listing
echo "v1.0" >> version.txt  # append instead of overwrite
```

- `>` overwrites.
- `>>` appends.
- `<` reads a file as the command's input: `sort < names.txt`.

### A classic debugging pipeline

```bash
cat server.log | grep ERROR | sort | uniq -c | sort -nr
```

This reads a log, keeps only `ERROR` lines, sorts them, counts duplicates, and orders the counts from largest to smallest. One line, five tools, real insight.

### Think in streams

Any command that reads stdin and writes stdout can be plugged into a pipeline. When you write your own scripts later, keeping this "stream in, stream out" design makes them instantly composable.

---

**Next up:** variables, quoting, and your first automation in Shell Automation."""
    ),
    L(
        id="tools-cli-exercise-greet",
        course_id="git-linux-developer-tools",
        module_id="tools-cli",
        title="Exercise: Greet from the Shell",
        type="exercise",
        order=5,
        content="""## Exercise: Greet from the Shell

Write a bash script that reads a name from standard input and prints a greeting.

### Worked sample

Input:

```text
Ada
```

Output:

```text
Hello, Ada!
```

### How your code runs

Your script is run with the test input piped to its stdin. Use `read` to grab the name and `printf` to print the greeting. `printf "Hello, %s!\\n" "$name"` lets you embed the variable safely.

### Starter code

```bash
read name
printf "Hello, %s!\n" "$name"
```

Adjust the starter if needed, then submit to run the tests.

Good luck!""",
        starter_code='''read name
printf "Hello, %s!\\n" "$name"
''',
        test_cases=[
            {"input": "Ada\n", "expected_output": "Hello, Ada!", "description": "Simple name"},
            {"input": "Linus\n", "expected_output": "Hello, Linus!", "description": "Another name"},
            {"input": "Grace\n", "expected_output": "Hello, Grace!", "description": "Third name"},
        ],
    ),
    L(
        id="tools-cli-exercise-sum",
        course_id="git-linux-developer-tools",
        module_id="tools-cli",
        title="Exercise: Shell Arithmetic",
        type="exercise",
        order=6,
        content="""## Exercise: Shell Arithmetic

Write a bash script that reads two integers, one per line, and prints their sum.

### Worked sample

Input:

```text
3
5
```

Output:

```text
8
```

### How your code runs

Use `read` to grab each number. Bash arithmetic lives inside double parentheses: `$((a + b))`. `echo $((a + b))` prints the result.

### Starter code

```bash
read a
read b
echo $((a + b))
```

Good luck!""",
        starter_code='''read a
read b
echo $((a + b))
''',
        test_cases=[
            {"input": "3\n5\n", "expected_output": "8", "description": "Small numbers"},
            {"input": "10\n20\n", "expected_output": "30", "description": "Larger numbers"},
            {"input": "-4\n9\n", "expected_output": "5", "description": "Negative operand"},
        ],
    ),
    L(
        id="tools-cli-exercise-wordcount",
        course_id="git-linux-developer-tools",
        module_id="tools-cli",
        title="Exercise: Count Words",
        type="exercise",
        order=7,
        content="""## Exercise: Count Words

Write a bash script that reads text from standard input and prints the total number of words it contains.

### Worked sample

Input:

```text
hello world
foo bar baz
```

Output:

```text
5
```

### How your code runs

`awk` processes input line by line. Each record has a field count stored in `NF`. Accumulate it across all lines, then print the total in the `END` block:

```bash
awk '{ total += NF } END { print total }'
```

### Starter code

```bash
awk '{ total += NF } END { print total }'
```

Good luck!""",
        starter_code='''awk '{ total += NF } END { print total }'
''',
        test_cases=[
            {"input": "hello world\nfoo bar baz\n", "expected_output": "5", "description": "Two lines"},
            {"input": "one two\n", "expected_output": "2", "description": "Single line"},
            {"input": "alpha beta gamma delta\n", "expected_output": "4", "description": "One long line"},
        ],
    ),
    # ── Module 2: Shell Automation ──────────────────────────────────────
    L(
        id="tools-shell-variables",
        course_id="git-linux-developer-tools",
        module_id="tools-shell",
        title="Variables and Quoting",
        type="theory",
        order=1,
        content="""## Variables and Quoting

A **variable** stores a value under a name. In bash, variables hold text — numbers become numbers only when you use arithmetic.

### Assigning and reading

```bash
name="Ada"
echo "$name"     # Ada
```

Notice there are **no spaces** around the `=` when assigning. To *read* a variable, prefix it with `$` or use `${name}` inside a string:

```bash
echo "Hello, ${name}!"   # Hello, Ada!
```

The `{}` form is useful when the variable name runs into other characters.

### Single vs double quotes

This is one of the most important distinctions in bash:

```bash
echo "value: $name"   # value: Ada      (expands the variable)
echo 'value: $name'   # value: $name    (literal text)
```

- **Double quotes**: `$`, backticks, and `\\` are interpreted.
- **Single quotes**: everything is literal — nothing expands.
- **No quotes at all**: expansion happens, and the result is split into words.

### Command substitution

You can capture a command's output into a variable:

```bash
today=$(date +%F)
files=$(ls)
echo "$today"
```

The `$(...)` form is the modern syntax; the older backticks `` `...` `` still work but are harder to nest.

### Arithmetic

Numbers are text until you ask bash to compute:

```bash
a=3
b=5
echo $((a + b))   # 8
echo $((a * b))   # 15
```

Arithmetic lives inside `$(( ))`, and inside those parentheses you don't need the `$` on variable names.

### Environment vs shell variables

- A plain `name="Ada"` is local to your shell.
- `export name="Ada"` makes it an **environment variable** that child processes inherit, like `PATH` or `HOME`.

Use quoting every time you touch a variable — unquoted expansions are the number-one source of subtle shell bugs.

---

**Next up:** conditionals for making decisions in scripts."""
    ),
    L(
        id="tools-shell-conditionals",
        course_id="git-linux-developer-tools",
        module_id="tools-shell",
        title="Conditionals and Branching",
        type="theory",
        order=2,
        content="""## Conditionals and Branching

Scripts make decisions with `if`, `elif`, and `else`, using the `test` command (usually written as `[ ... ]`) to evaluate conditions.

### The basic if

```bash
score=75
if [ "$score" -ge 60 ]; then
  echo "pass"
fi
```

- `[` is actually the `test` command with a `]` for readability.
- Notice the spaces inside the brackets — they are required.
- The `; then` marks the start of the body.

### If / else / elif

```bash
if [ "$score" -ge 90 ]; then
  echo "A"
elif [ "$score" -ge 60 ]; then
  echo "B"
else
  echo "F"
fi
```

### Numeric comparisons

| Operator | Meaning                 |
|----------|-------------------------|
| `-eq`    | equal                   |
| `-ne`    | not equal               |
| `-gt`    | greater than            |
| `-ge`    | greater than or equal   |
| `-lt`    | less than               |
| `-le`    | less than or equal      |

### String comparisons

```bash
if [ "$name" = "Ada" ]; then ...     # equality
if [ "$name" != "Ada" ]; then ...    # inequality
if [ -z "$name" ]; then ...          # is empty
if [ -n "$name" ]; then ...          # is not empty
```

### File tests

```bash
if [ -f "notes.md" ]; then ...   # is a regular file
if [ -d "src" ]; then ...        # is a directory
if [ -e "path" ]; then ...       # exists
```

### Combining conditions

```bash
if [ "$age" -ge 18 ] && [ "$has_id" = "yes" ]; then
  echo "welcome"
fi
```

`&&` means "and", `||` means "or", `!` negates.

Always quote variables inside `[ ]` — an empty variable otherwise breaks the test into a syntax error.

---

**Next up:** loops for repeating work."""
    ),
    L(
        id="tools-shell-loops",
        course_id="git-linux-developer-tools",
        module_id="tools-shell",
        title="Loops for Repetition",
        type="theory",
        order=3,
        content="""## Loops for Repetition

Loops let a script repeat work. Bash has two main loop styles: `for` over a list and arithmetic `for`, plus the flexible `while`.

### for over a list

```bash
for name in Ada Linus Grace; do
  echo "Hello, $name"
done
```

This runs the body once per item, with `name` set to each value in turn.

### Arithmetic for

The C-style loop counts with an index:

```bash
for ((i = 1; i <= 5; i++)); do
  echo "number $i"
done
```

- `i = 1` is the start.
- `i <= 5` is the condition to keep going.
- `i++` increments after each pass.

### while loop

`while` repeats as long as its condition stays true:

```bash
count=1
while [ "$count" -le 3 ]; do
  echo "attempt $count"
  count=$((count + 1))
done
```

### Accumulating results

A common pattern: build a string across a loop, then print it once.

```bash
out=""
for ((i = 1; i <= 3; i++)); do
  out="$out $i"
done
echo "$out"      # " 1 2 3"
```

### Reading stdin line by line

```bash
while read -r line; do
  echo "got: $line"
done
```

This loop runs once per line of standard input — ideal for processing log files or lists.

### Break and continue

- `break` exits the loop immediately.
- `continue` skips to the next iteration.

```bash
for ((i = 1; i <= 10; i++)); do
  [ $((i % 2)) -eq 0 ] && continue
  [ "$i" -gt 7 ] && break
  echo "$i"
done
```

Loops turn a single command into a whole automation, which is exactly what scripts are for.

---

**Next up:** writing your first script file with arguments."""
    ),
    L(
        id="tools-shell-scripts",
        course_id="git-linux-developer-tools",
        module_id="tools-shell",
        title="Writing Your First Script",
        type="theory",
        order=4,
        content="""## Writing Your First Script

A **script** is a text file of commands that bash runs top to bottom. Any sequence of commands you type at the prompt can be saved as a script.

### The shebang

The first line tells the system which interpreter to use:

```bash
#!/bin/bash
```

The `#!` is called the *shebang*. Without it, your file may still run with `bash file.sh`, but the shebang makes it executable directly.

### A minimal script

```bash
#!/bin/bash
# greet.sh
name="Ada"
echo "Hello, $name"
```

### Making it executable

```bash
chmod +x greet.sh
./greet.sh
```

The `chmod +x` grants execute permission, and `./greet.sh` runs it from the current directory (the `./` is required).

### Script arguments

Inside the script, arguments are available as `$1`, `$2`, etc. `$0` is the script name and `$#` is the argument count:

```bash
#!/bin/bash
echo "script: $0"
echo "first arg: $1"
echo "arg count: $#"
```

```bash
./greet.sh world
# script: ./greet.sh
# first arg: world
# arg count: 1
```

### Exit codes

Every command finishes with an exit status: `0` means success, anything else means failure. Your script can set its own:

```bash
if [ -f "$1" ]; then
  echo "found"
  exit 0
else
  echo "missing" >&2
  exit 1
fi
```

You can check the last command's status with `$?`.

### Good habits

- Add a shebang, even for tiny scripts.
- Use `set -e` to stop on the first error in critical scripts.
- Comment *why*, not *what*.
- Keep scripts small and composed from pipes.

A script turns a fragile manual procedure into a reliable, repeatable tool — the whole point of shell automation.

---

**Next up:** exercises — largest of two, FizzBuzz, and sums."""
    ),
    L(
        id="tools-shell-exercise-largest",
        course_id="git-linux-developer-tools",
        module_id="tools-shell",
        title="Exercise: Largest of Two",
        type="exercise",
        order=5,
        content="""## Exercise: Largest of Two

Write a bash script that reads two integers and prints the larger one.

### Worked sample

Input:

```text
3
5
```

Output:

```text
5
```

### How your code runs

Read both numbers, then use an `if` with `-gt` to decide which to print. If they are equal, either value is correct.

### Starter code

```bash
read a
read b
if [ "$a" -gt "$b" ]; then
  echo "$a"
else
  echo "$b"
fi
```

Good luck!""",
        starter_code='''read a
read b
if [ "$a" -gt "$b" ]; then
  echo "$a"
else
  echo "$b"
fi
''',
        test_cases=[
            {"input": "3\n5\n", "expected_output": "5", "description": "Second is larger"},
            {"input": "7\n2\n", "expected_output": "7", "description": "First is larger"},
            {"input": "4\n4\n", "expected_output": "4", "description": "Equal values"},
        ],
    ),
    L(
        id="tools-shell-exercise-fizzbuzz",
        course_id="git-linux-developer-tools",
        module_id="tools-shell",
        title="Exercise: Shell FizzBuzz",
        type="exercise",
        order=6,
        content="""## Exercise: Shell FizzBuzz

Write a bash script that reads a number `n` and prints the FizzBuzz sequence from **1 to n**, space-separated on one line.

Rules:

- divisible by 3 → `Fizz`
- divisible by 5 → `Buzz`
- divisible by both → `FizzBuzz`
- otherwise → the number itself

### Worked sample

Input:

```text
5
```

Output:

```text
1 2 Fizz 4 Buzz
```

### How your code runs

Use an arithmetic `for` loop from 1 to n. Check divisibility with `$((i % 15))`, `$((i % 3))`, and `$((i % 5))`. Build the output string by appending, then strip the leading space with `${out# }`.

### Starter code

```bash
read n
out=""
for ((i = 1; i <= n; i++)); do
  if [ $((i % 15)) -eq 0 ]; then
    out="$out FizzBuzz"
  elif [ $((i % 3)) -eq 0 ]; then
    out="$out Fizz"
  elif [ $((i % 5)) -eq 0 ]; then
    out="$out Buzz"
  else
    out="$out $i"
  fi
done
echo "${out# }"
```

Good luck!""",
        starter_code='''read n
out=""
for ((i = 1; i <= n; i++)); do
  if [ $((i % 15)) -eq 0 ]; then
    out="$out FizzBuzz"
  elif [ $((i % 3)) -eq 0 ]; then
    out="$out Fizz"
  elif [ $((i % 5)) -eq 0 ]; then
    out="$out Buzz"
  else
    out="$out $i"
  fi
done
echo "${out# }"
''',
        test_cases=[
            {"input": "5\n", "expected_output": "1 2 Fizz 4 Buzz", "description": "Up to five"},
            {"input": "15\n", "expected_output": "1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz", "description": "Full sequence"},
            {"input": "3\n", "expected_output": "1 2 Fizz", "description": "Short sequence"},
        ],
    ),
    L(
        id="tools-shell-exercise-squares",
        course_id="git-linux-developer-tools",
        module_id="tools-shell",
        title="Exercise: Sum of Squares",
        type="exercise",
        order=7,
        content="""## Exercise: Sum of Squares

Write a bash script that reads an integer `n` and prints the sum of the squares from **1² up to n²**.

### Worked sample

Input:

```text
3
```

Output:

```text
14
```

Because `1² + 2² + 3² = 1 + 4 + 9 = 14`.

### How your code runs

Loop from 1 to n with an accumulator variable. Bash arithmetic supports `i * i` inside `$(( ))`.

### Starter code

```bash
read n
sum=0
for ((i = 1; i <= n; i++)); do
  sum=$((sum + i * i))
done
echo "$sum"
```

Good luck!""",
        starter_code='''read n
sum=0
for ((i = 1; i <= n; i++)); do
  sum=$((sum + i * i))
done
echo "$sum"
''',
        test_cases=[
            {"input": "3\n", "expected_output": "14", "description": "Up to three"},
            {"input": "5\n", "expected_output": "55", "description": "Up to five"},
            {"input": "1\n", "expected_output": "1", "description": "Single square"},
        ],
    ),
    # ── Module 3: Git Fundamentals ──────────────────────────────────────
    L(
        id="tools-git-version-control",
        course_id="git-linux-developer-tools",
        module_id="tools-git",
        title="Why Version Control?",
        type="theory",
        order=1,
        content="""## Why Version Control?

**Version control** tracks every change to your files over time. Git is the most widely used version control system in the world, and understanding it is non-negotiable for a working developer.

### The problem it solves

Without version control:

- You make a change, it breaks, and you cannot remember what you altered.
- You save copies: `report_final_v2_actual_3.doc`.
- Two people edit the same file and one overwrites the other.

Git fixes all three.

### Snapshots, not copies

Git records a **snapshot** of your project at each commit. Because snapshots are tiny deltas, you get full history without duplicating every file:

```text
commit c3f9a2e  "Fix login bug"
commit 8b1d04c  "Add user dashboard"
commit e2a51b7  "Initial project"
```

You can jump to any snapshot, see exactly what changed, and revert mistakes.

### The three states of Git

| State      | Meaning                                        |
|------------|------------------------------------------------|
| working dir| files you are editing                           |
| staging    | changes you have marked with `git add`          |
| committed  | a snapshot saved to the repository with `git commit` |

The flow is always the same:

```bash
git add file.py
git commit -m "message"
```

### Why developers love it

- **History**: every change is attributed to an author with a timestamp.
- **Experimentation**: branches let you try ideas without risk.
- **Collaboration**: many people work in parallel and merge cleanly.
- **Accountability**: blame shows who changed each line and why.

### Git is distributed

Unlike older systems, every clone has the **entire** history. You can work offline, commit locally, and push later. There is no single point of failure.

The exercises in this module simulate working with Git data — commit logs, status output, and changed files — so you can practice the skills without a repository.

---

**Next up:** making your first commit with `init`, `add`, and `commit`."""
    ),
    L(
        id="tools-git-first-commit",
        course_id="git-linux-developer-tools",
        module_id="tools-git",
        title="Your First Commit",
        type="theory",
        order=2,
        content="""## Your First Commit

A Git repository is born with `git init`, grows with `git add` and `git commit`, and reports its state with `git status`.

### Initialize

```bash
mkdir myapp
cd myapp
git init
```

This creates a hidden `.git` directory holding all of Git's bookkeeping. The project now has a **working directory** but no commits yet.

### Stage and commit

```bash
echo "# My App" > README.md
git add README.md
git commit -m "Add project readme"
```

- `git add` moves files into the **staging area**.
- `git commit` takes a snapshot of the staged changes with a message.
- `-m "..."` supplies the message; without it Git opens an editor.

### Inspecting state

```bash
git status     # what is staged, modified, or untracked?
git log        # commit history, newest first
git diff       # unstaged changes to files
```

`git status` is the command you will run dozens of times a day. It tells you exactly what Git thinks is going on.

### Worked example of status output

```text
Changes to be committed:
  modified:   src/app.py
Untracked files:
  README.md
```

`M` in a short status means modified, `A` means added, `??` means untracked.

### Commit messages matter

Write messages that describe the *why*, in the present tense imperative:

```bash
git commit -m "Add input validation to login form"
git commit -m "Fix off-by-one error in pagination"
```

Future you (and your team) will read these messages to understand history.

### One commit at a time

Small, focused commits make it easy to find regressions, revert individual changes, and review work. Commit when a unit of work is complete — not once a day.

---

**Next up:** branches and merging."""
    ),
    L(
        id="tools-git-branches",
        course_id="git-linux-developer-tools",
        module_id="tools-git",
        title="Branches and Merging",
        type="theory",
        order=3,
        content="""## Branches and Merging

A **branch** is a movable pointer to a commit. Branching lets you develop features in parallel without disturbing the main line of work.

### The default branch

New repositories start on `main` (or legacy `master`). Think of it as the stable, always-shippable line.

### Creating and switching

```bash
git branch feature-nav     # create a branch
git checkout feature-nav   # switch to it
git switch feature-nav     # newer, clearer syntax
```

Or create and switch in one step:

```bash
git switch -c feature-nav
```

### See where you are

```bash
git branch        # list branches, * marks the current one
git log --oneline # recent commits on the current branch
```

### Merging

When the feature is done, switch back to the target branch and merge:

```bash
git switch main
git merge feature-nav
```

If the two branches changed different files, Git combines them automatically with a **merge commit**. If they touched the same lines, you get a **conflict** to resolve by hand.

### The branch model

```text
main:     A ── B ───────────── D (merge)
feature:       └── C ─────────┘
```

- `A`, `B` are commits on main.
- `C` is the feature work.
- `D` merges the feature back in.

### Branch safety

- Branches are cheap — create one for any experiment.
- Never commit directly to `main` on a shared team unless you are the one doing releases.
- Delete merged branches with `git branch -d feature-nav` to keep the list tidy.

Branching is what makes Git collaboration possible: many lines of work advance simultaneously and converge cleanly.

---

**Next up:** remotes, GitHub, and sharing work."""
    ),
    L(
        id="tools-git-remotes",
        course_id="git-linux-developer-tools",
        module_id="tools-git",
        title="Working with Remotes",
        type="theory",
        order=4,
        content="""## Working with Remotes

So far everything has been local. A **remote** is another copy of your repository — usually on a hosting service like GitHub, GitLab, or Bitbucket. The remote lets your team share history.

### Cloning a repository

```bash
git clone https://github.com/org/repo.git
cd repo
```

`git clone` downloads the entire history into a new directory and sets up the remote automatically.

### The origin remote

The default remote is named `origin`. See your remotes and the state of your branch:

```bash
git remote -v
git status
```

### Push and pull

```bash
git push origin main      # upload your commits to the remote
git pull origin main      # download new commits from the remote
```

- `git fetch` downloads without merging; `git pull` = `fetch` + `merge`.
- `git push` uploads commits that exist locally but not remotely.

### The daily rhythm

```bash
git pull                      # get today's changes first
# ... work, commit ...
git add .
git commit -m "Implement feature X"
git push
```

Pull before you start, commit small units of work, push when a unit is complete.

### Handshake and token setup

Modern hosting services no longer accept plain passwords. You authenticate with an SSH key or a personal access token. Git prints a helpful URL when a push is rejected — follow it to configure your credentials.

### Branch protection

On shared repositories, `main` is usually **protected**: you cannot push to it directly. Instead you:

1. Push a feature branch.
2. Open a **pull request**.
3. Get it reviewed.
4. Merge it into main.

This is the standard team workflow, covered in detail in the Collaboration module.

---

**Next up:** debugging — exit codes, grep, and process tools."""
    ),
    L(
        id="tools-git-exercise-log",
        course_id="git-linux-developer-tools",
        module_id="tools-git",
        title="Exercise: Count Commits in a Log",
        type="exercise",
        order=5,
        content="""## Exercise: Count Commits in a Log

Write a bash script that reads a Git log and prints the number of commits it contains. Each commit starts with a line beginning with `commit `.

### Worked sample

Input:

```text
commit a1b2c3
Author: Ada
Add greeting

commit d4e5f6
Author: Linus
Fix bug
```

Output:

```text
2
```

### How your code runs

`grep -c '^commit '` counts lines that start with the literal text `commit ` — exactly one per commit in a real Git log.

### Starter code

```bash
grep -c '^commit '
```

Good luck!""",
        starter_code='''grep -c '^commit '
''',
        test_cases=[
            {"input": "commit a1b2c3\nAuthor: Ada\nAdd greeting\n\ncommit d4e5f6\nAuthor: Linus\nFix bug\n", "expected_output": "2", "description": "Two commits"},
            {"input": "commit abc123\nCommit message\n", "expected_output": "1", "description": "Single commit"},
            {"input": "Author: Ada\nAuthor: Linus\n", "expected_output": "0", "description": "No commits"},
        ],
    ),
    L(
        id="tools-git-exercise-status",
        course_id="git-linux-developer-tools",
        module_id="tools-git",
        title="Exercise: Count Modified Files",
        type="exercise",
        order=6,
        content="""## Exercise: Count Modified Files

Write a bash script that reads a short `git status` output and prints how many files are **modified**. Modified files start with `M `.

### Worked sample

Input:

```text
M src/app.py
M src/utils.py
A new.txt
```

Output:

```text
2
```

### How your code runs

`grep -c '^M '` counts lines whose first two characters are exactly `M` and a space — the standard marker for modified files.

### Starter code

```bash
grep -c '^M '
```

Good luck!""",
        starter_code='''grep -c '^M '
''',
        test_cases=[
            {"input": "M src/app.py\nM src/utils.py\nA new.txt\n", "expected_output": "2", "description": "Two modified, one added"},
            {"input": "A new.txt\n?? untracked.md\n", "expected_output": "0", "description": "None modified"},
            {"input": "M README.md\n", "expected_output": "1", "description": "Single modified"},
        ],
    ),
    L(
        id="tools-git-exercise-files",
        course_id="git-linux-developer-tools",
        module_id="tools-git",
        title="Exercise: List Changed Files",
        type="exercise",
        order=7,
        content="""## Exercise: List Changed Files

Write a bash script that reads lines of the form `STATUS filename` (like Git status output) and prints just the filenames, in sorted order, one per line.

### Worked sample

Input:

```text
M zeta.py
M alpha.py
M middle.py
```

Output:

```text
alpha.py
middle.py
zeta.py
```

### How your code runs

`cut -d' ' -f2` extracts the second space-separated field (the filename), and `sort` orders the lines alphabetically.

### Starter code

```bash
cut -d' ' -f2 | sort
```

Good luck!""",
        starter_code='''cut -d' ' -f2 | sort
''',
        test_cases=[
            {"input": "M zeta.py\nM alpha.py\nM middle.py\n", "expected_output": "alpha.py\nmiddle.py\nzeta.py", "description": "Sorts alphabetically"},
            {"input": "M b.py\nM a.py\n", "expected_output": "a.py\nb.py", "description": "Two files"},
            {"input": "M solo.py\n", "expected_output": "solo.py", "description": "Single file"},
        ],
    ),
    # ── Module 4: Debugging and Tooling ─────────────────────────────────
    L(
        id="tools-debugging-errors",
        course_id="git-linux-developer-tools",
        module_id="tools-debugging",
        title="Reading Errors and Exit Codes",
        type="theory",
        order=1,
        content="""## Reading Errors and Exit Codes

Every command you run reports success or failure through an **exit code**. Learning to read these codes — and where errors go — is the first debugging skill.

### Where errors go

Errors do **not** go to normal output. They go to **standard error** (stderr):

```bash
ls /no/such/dir
# ls: cannot access '/no/such/dir': No such file or directory
```

This separation matters in pipelines: `ls | wc -l` still counts only real output, while the error appears on the terminal.

### Checking the exit code

After a command finishes, its exit status is stored in `$?`:

```bash
ls /tmp
echo $?    # 0 — success
ls /no/such/dir
echo $?    # 2 — error
```

Convention:

| Code | Meaning                    |
|------|----------------------------|
| 0    | success                    |
| 1    | generic failure            |
| 2    | usage / syntax error       |
| 127  | command not found          |
| 126  | found but not executable   |

### Handling errors in scripts

```bash
if ! mkdir deploy; then
  echo "deploy dir exists — continuing" >&2
fi
```

`>&2` explicitly redirects a message to stderr.

### Common error patterns

- **command not found** — the tool is not installed or not on `PATH`.
- **Permission denied** — you lack execute permission; check with `ls -l` and fix with `chmod +x`.
- **No such file or directory** — typo in the path; `pwd` and `ls` will ground you.
- **unexpected operator** — usually a missing space or an unquoted variable inside `[ ]`.

### The golden habit

Read the first error message line fully before changing anything. It usually names the file and the line. Then fix the *cause*, not the symptom.

---

**Next up:** searching logs and files with grep."""
    ),
    L(
        id="tools-debugging-grep",
        course_id="git-linux-developer-tools",
        module_id="tools-debugging",
        title="Searching Logs with grep",
        type="theory",
        order=2,
        content="""## Searching Logs with grep

`grep` searches text for patterns. It is the single most useful command for debugging — whenever something breaks, you *grep* the logs.

### Basic usage

```bash
grep error server.log        # lines containing "error"
grep -i error server.log     # case-insensitive
grep -c error server.log     # count of matching lines
grep -n error server.log     # show line numbers
```

### The pipeline that catches bugs

```bash
tail -f server.log | grep -i "error\\|exception"
```

`tail -f` follows the log as it grows, and grep filters it live. This one-liner is a real monitoring tool.

### More useful flags

| Flag | Meaning                                      |
|------|----------------------------------------------|
| `-i` | ignore case                                  |
| `-v` | invert — print lines that do NOT match       |
| `-c` | count matches instead of printing lines      |
| `-n` | prefix each line with its line number        |
| `-w` | match whole words only                       |
| `-r` | search recursively through a directory       |
| `-l` | list only filenames that contain a match     |

### Regular expressions

grep supports regex by default with `-E` (extended) or `-e`:

```bash
grep -E "^ERROR|timeout" server.log   # starts with ERROR, or contains timeout
grep -w "panic" *.go                  # whole word across Go files
grep "port=[0-9]+" config.conf -E     # any digit run after port=
```

### Combined with other tools

```bash
grep ERROR server.log | sort | uniq -c | sort -nr
```

Count each distinct error message, most frequent first — a quick error report.

### Search your shell history

```bash
history | grep git
```

You probably typed that exact command before — grep finds it.

When something is wrong, the first question is always: *what does the log say?* And the answer comes from grep.

---

**Next up:** processes and system tools."""
    ),
    L(
        id="tools-debugging-processes",
        course_id="git-linux-developer-tools",
        module_id="tools-debugging",
        title="Processes and System Tools",
        type="theory",
        order=3,
        content="""## Processes and System Tools

Every running program is a **process**. When your machine misbehaves, you inspect processes and system resources to find out what is consuming them.

### Listing processes

```bash
ps               # processes in the current terminal
ps aux           # every process on the system, detailed
ps aux | grep python
```

`ps aux` is the classic full listing: user, PID, CPU, memory, and the command line. Pipe it through `grep` to find a specific program.

### Killing a process

```bash
kill 4321            # send SIGTERM (ask politely)
kill -9 4321         # SIGKILL (force, last resort)
pkill -f "node app"  # kill by name pattern
```

Always prefer `kill` without flags first so the program can clean up.

### Top: live resource usage

```bash
top
```

`top` refreshes continuously, sorting by CPU usage. Press `q` to quit. `htop` is a prettier, interactive alternative if installed.

### Disk and memory

```bash
df -h     # free disk space, human readable
free -h   # memory usage, human readable
du -sh *  # size of each item in the current directory
```

Full disk is a classic production incident. `df -h` catches it in one second.

### Listening ports

```bash
ss -tlnp   # sockets listening on TCP ports
```

If a service "won't start because the port is in use", `ss -tlnp` shows you exactly which PID owns it.

### Logs: the system's memory

```bash
journalctl -u myservice --since "1 hour ago"   # systemd service logs
tail -n 100 /var/log/syslog                    # classic log tail
```

Combining `ps`, `df`, `free`, and log tails covers the majority of real-world debugging: find the process, check resources, read the logs.

---

**Next up:** debugging your own shell scripts."""
    ),
    L(
        id="tools-debugging-scripting",
        course_id="git-linux-developer-tools",
        module_id="tools-debugging",
        title="Debugging Your Own Scripts",
        type="theory",
        order=4,
        content="""## Debugging Your Own Scripts

Your scripts will misbehave. The good news: bash ships with debugging tools that show you exactly what is happening.

### Syntax check first

```bash
bash -n script.sh
```

`-n` parses the script and reports syntax errors without running it. Run this before anything else.

### Trace every command

```bash
bash -x script.sh
```

`-x` prints each command as it runs, with variables expanded, prefixed by `+`. This is the single most effective way to see where a script goes wrong:

```text
+ score=75
+ '[' 75 -ge 60 ']'
+ echo pass
pass
```

You see the real values being compared — invaluable for quoting and logic bugs.

### The same inside a running script

```bash
#!/bin/bash
set -x          # trace from here on
...
set +x          # stop tracing
```

Or enable tracing only around the suspicious section.

### Stop on errors

```bash
set -e
```

With `set -e`, the script aborts on the first failing command instead of limping on with wrong state.

### The classic echo debugger

When you are not sure what a variable holds:

```bash
echo "DEBUG: out=[$out]" >&2
```

Sending debug output to **stderr** keeps it out of pipelines and real results.

### Common bash bugs

- **Unquoted variables**: `[ $name = Ada ]` breaks when `name` is empty.
- **Spaces in `[ ]`**: `[$a -eq $b]` is missing required spaces.
- **Forgetting `$`**: `echo score` prints the word, not the value.
- **`=` vs `==`**: `=` is the test operator; `==` works in `[[ ]]` but not everywhere.
- **Arithmetic vs strings**: `$((a + b))` computes; `"$a + $b"` is text.

### The debugging loop

1. `bash -n` to catch syntax.
2. `bash -x` to watch execution.
3. Add targeted `echo ... >&2` for variables.
4. Fix one thing, re-run, repeat.

Methodical tracing beats random tinkering every time.

---

**Next up:** the collaboration project — branching, pull requests, and review."""
    ),
    L(
        id="tools-debugging-exercise-exit",
        course_id="git-linux-developer-tools",
        module_id="tools-debugging",
        title="Exercise: Classify Exit Codes",
        type="exercise",
        order=5,
        content="""## Exercise: Classify Exit Codes

Write a bash script that reads an exit code and prints `success` if it is `0`, otherwise `failure`.

### Worked sample

Input:

```text
0
```

Output:

```text
success
```

### How your code runs

Read the code, then test it with `-eq 0` in an `if`. This mirrors how real scripts check command status.

### Starter code

```bash
read code
if [ "$code" -eq 0 ]; then
  echo "success"
else
  echo "failure"
fi
```

Good luck!""",
        starter_code='''read code
if [ "$code" -eq 0 ]; then
  echo "success"
else
  echo "failure"
fi
''',
        test_cases=[
            {"input": "0\n", "expected_output": "success", "description": "Exit code 0"},
            {"input": "1\n", "expected_output": "failure", "description": "Generic error"},
            {"input": "127\n", "expected_output": "failure", "description": "Command not found"},
        ],
    ),
    L(
        id="tools-debugging-exercise-error",
        course_id="git-linux-developer-tools",
        module_id="tools-debugging",
        title="Exercise: Find Error Lines",
        type="exercise",
        order=6,
        content="""## Exercise: Find Error Lines

Write a bash script that reads log lines and prints every line that contains `error` (case-insensitive).

### Worked sample

Input:

```text
INFO started
ERROR db timeout
INFO retrying
```

Output:

```text
ERROR db timeout
```

### How your code runs

`grep -i error` reads stdin and prints matching lines. The `-i` flag matches `error`, `Error`, and `ERROR` alike — just like grepping a real log.

### Starter code

```bash
grep -i error
```

Good luck!""",
        starter_code='''grep -i error
''',
        test_cases=[
            {"input": "INFO started\nERROR db timeout\nINFO retrying\n", "expected_output": "ERROR db timeout", "description": "One match"},
            {"input": "ERROR auth failed\nERROR db timeout\nINFO ok\n", "expected_output": "ERROR auth failed\nERROR db timeout", "description": "Multiple matches"},
            {"input": "all good\nstill fine\n", "expected_output": "", "description": "No matches"},
        ],
    ),
    L(
        id="tools-debugging-exercise-parse",
        course_id="git-linux-developer-tools",
        module_id="tools-debugging",
        title="Exercise: Extract Log Messages",
        type="exercise",
        order=7,
        content="""## Exercise: Extract Log Messages

Write a bash script that reads log lines of the form `LEVEL message` and prints just the message part (everything after the first space).

### Worked sample

Input:

```text
INFO starting service
ERROR failed to connect
```

Output:

```text
starting service
failed to connect
```

### How your code runs

`cut -d' ' -f2-` splits each line on spaces and keeps field 2 to the end, discarding the level prefix.

### Starter code

```bash
cut -d' ' -f2-
```

Good luck!""",
        starter_code='''cut -d' ' -f2-
''',
        test_cases=[
            {"input": "INFO starting service\nERROR failed to connect\n", "expected_output": "starting service\nfailed to connect", "description": "Two levels"},
            {"input": "WARN low disk\n", "expected_output": "low disk", "description": "Single line"},
            {"input": "INFO ok\nERROR boom\n", "expected_output": "ok\nboom", "description": "Short messages"},
        ],
    ),
    # ── Module 5: Collaboration Project ─────────────────────────────────
    L(
        id="tools-collab-workflow",
        course_id="git-linux-developer-tools",
        module_id="tools-collab",
        title="A Collaborative Workflow",
        type="theory",
        order=1,
        content="""## A Collaborative Workflow

Real teams follow a repeatable **workflow** built on branches and pull requests. It protects `main` and makes every change reviewable.

### The golden rule: main stays green

`main` is always deployable. Nobody pushes to it directly. Every change arrives through a **feature branch** and a **pull request**.

### The feature-branch workflow

```bash
git switch main
git pull                          # up to date
git switch -c feature/payment     # new branch off main
```

Now you develop on `feature/payment`. Main never sees work in progress.

### A focused commit sequence

```bash
git add src/payment.js
git commit -m "Add payment form validation"
git add tests/payment.test.js
git commit -m "Test payment validation"
```

Small commits with clear messages make the review trivial.

### Push and open the request

```bash
git push origin feature/payment
```

On the hosting site you open a **pull request** (PR) comparing `feature/payment` against `main`. The PR is where discussion, review, and CI results live.

### Merge with discipline

Only merge when:

- Tests pass.
- A reviewer has approved.
- The branch is rebased or conflict-free.

### Keeping main shippable

- Run the test suite before every merge.
- Merge small changes often instead of one giant PR.
- If `main` moves while you work, update your branch:

```bash
git switch main
git pull
git switch feature/payment
git merge main
```

### The rhythm in one loop

```text
pull → branch → commit → push → pull request → review → merge
```

This loop is how thousands of teams ship software every day. In this module's exercises you will practice analyzing branch data, PRs, reviews, and changed-line summaries — the numbers behind the workflow.

---

**Next up:** pull requests and code review in depth."""
    ),
    L(
        id="tools-collab-pull-requests",
        course_id="git-linux-developer-tools",
        module_id="tools-collab",
        title="Pull Requests and Review",
        type="theory",
        order=2,
        content="""## Pull Requests and Review

A **pull request** (PR) is a request to merge one branch into another, bundled with discussion and review. It is where code review actually happens.

### Anatomy of a good PR

A good PR has:

- A descriptive title: `Add password reset flow`.
- A body explaining **what** and **why**.
- Small, focused scope — one feature or fix.
- Passing CI checks.

### The review cycle

1. Author opens the PR.
2. Reviewers read the diff and leave comments.
3. Author pushes follow-up commits.
4. Reviewers approve; the PR merges.

### Reviewers ask questions like

- Is this approach correct?
- Are there edge cases or security holes?
- Is the naming clear?
- Are tests covering the change?

### Requested changes

If a reviewer requests changes, the author pushes new commits to the same branch — the PR updates automatically. Git makes this iteration painless because commits build on each other.

### CI in the PR

Modern workflows run **CI** (continuous integration) on every PR: lint, tests, builds. A red check is a blocker:

```text
✓ tests passed      ✓ build passed
```

Merge only when everything is green.

### Merge strategies

| Strategy   | Result                                        |
|------------|-----------------------------------------------|
| merge      | adds a merge commit, preserves branch history |
| squash     | collapses commits into one on main            |
| rebase     | replays commits onto main, linear history     |

Squash and rebase produce a tidy `main` at the cost of some history detail.

### Reviewing someone else's code

Be specific, be kind, and separate must-fix from nice-to-have. Comment on the diff, not the person. Approve when the code is correct — don't let perfect be the enemy of good.

PRs are the team's quality gate. They catch bugs, spread knowledge, and keep everyone accountable for the codebase.

---

**Next up:** resolving merge conflicts."""
    ),
    L(
        id="tools-collab-conflicts",
        course_id="git-linux-developer-tools",
        module_id="tools-collab",
        title="Resolving Conflicts",
        type="theory",
        order=3,
        content="""## Resolving Conflicts

When two branches change the **same lines** of the same file, Git cannot merge automatically. You get a **merge conflict** — and resolving it is a normal part of collaborative work.

### What a conflict looks like

During a merge, Git marks the conflicting file with markers:

```text
<<<<<<< HEAD
total = price * 1.2;
=======
total = price * 1.3;
>>>>>>> feature/tax
```

- Everything above `=======` is the current branch (`HEAD`).
- Everything below is the incoming branch.
- Your job: pick the correct version — or write something entirely new — and remove the markers.

### The resolution steps

```bash
git status              # see which files conflict
git merge feature/tax   # merge fails, files marked
```

Edit the file, keeping the right logic:

```text
total = price * 1.25;
```

Then:

```bash
git add pricing.js
git commit
```

The merge commit records the resolution.

### Conflicts are not failures

A conflict simply means Git needs human judgment. It happens all the time on active teams. What matters is *how* you handle it:

- Resolve **locally** and test before pushing.
- Never blindly keep `HEAD` or the incoming side — read the surrounding code.
- If you are unsure, ask the author of the other branch.

### Reducing conflicts

- Merge `main` into your branch frequently so it never drifts far.
- Keep branches short-lived.
- Work in small files with clear ownership.

### Rebase conflicts

Rebasing replays your commits onto another branch and can also conflict. The markers look the same; you resolve and continue with `git rebase --continue`.

Resolving a conflict cleanly is a badge of honor for a collaborative developer — it means you understood both sides and chose correctly.

---

**Next up:** releases, tags, and shipping."""
    ),
    L(
        id="tools-collab-release",
        course_id="git-linux-developer-tools",
        module_id="tools-collab",
        title="Releases and Tags",
        type="theory",
        order=4,
        content="""## Releases and Tags

When `main` reaches a shippable state, teams mark the point with a **tag** — a named snapshot that never moves.

### Creating a tag

```bash
git tag v1.0.0
git tag -a v1.0.0 -m "Release 1.0.0"   # annotated with a message
```

Annotated tags store a message, author, and date — preferred for releases.

### Pushing tags

Tags do not ride along with a normal push:

```bash
git push origin v1.0.0
git push --tags   # push all tags at once
```

### Why tags matter

- **Reproducibility**: `v1.0.0` is an immutable pointer; you can always rebuild that exact state.
- **Rollbacks**: if a release breaks, check out the previous tag and redeploy.
- **Changelogs**: compare two tags to see everything that changed between releases.

```bash
git diff v1.0.0 v1.1.0
git log v1.0.0..v1.1.0 --oneline
```

### Semantic versioning

Teams commonly follow **SemVer**: `MAJOR.MINOR.PATCH`.

- `MAJOR` — breaking changes.
- `MINOR` — new features, backwards compatible.
- `PATCH` — bug fixes.

Bumping versions consistently tells users how safe an upgrade is.

### Releases on hosting platforms

GitHub and GitLab build on tags: a **release** bundles a tag with notes, binaries, and assets. `v1.0.0` becomes the release's version string.

### The release checklist

1. Run the full test suite.
2. Bump the version number.
3. Write release notes.
4. Tag and push.
5. Tag any hotfix commits on top and bump `PATCH`.

Tags close the loop: every merge history, every release is a named, findable snapshot. That is the payoff of the entire Git workflow.

---

**Next up:** the collaboration exercises — merged PRs, authors, and changed lines."""
    ),
    L(
        id="tools-collab-exercise-merged",
        course_id="git-linux-developer-tools",
        module_id="tools-collab",
        title="Exercise: Count Merged PRs",
        type="exercise",
        order=5,
        content="""## Exercise: Count Merged PRs

Write a bash script that reads a list of pull request lines and prints how many are **merged**. Each line contains the word `merged` or `open`.

### Worked sample

Input:

```text
PR 12 merged
PR 13 open
PR 14 merged
```

Output:

```text
2
```

### How your code runs

`grep -c merged` counts the lines containing the word `merged` — exactly the closed-and-merged PRs in the list.

### Starter code

```bash
grep -c merged
```

Good luck!""",
        starter_code='''grep -c merged
''',
        test_cases=[
            {"input": "PR 12 merged\nPR 13 open\nPR 14 merged\n", "expected_output": "2", "description": "Two merged, one open"},
            {"input": "PR 1 open\nPR 2 open\n", "expected_output": "0", "description": "None merged"},
            {"input": "PR 99 merged\n", "expected_output": "1", "description": "Single merged"},
        ],
    ),
    L(
        id="tools-collab-exercise-authors",
        course_id="git-linux-developer-tools",
        module_id="tools-collab",
        title="Exercise: List Unique Authors",
        type="exercise",
        order=6,
        content="""## Exercise: List Unique Authors

Write a bash script that reads commit lines of the form `HASH AUTHOR` and prints the distinct authors, sorted alphabetically, one per line.

### Worked sample

Input:

```text
a1 Ada
a2 Linus
b1 Ada
```

Output:

```text
Ada
Linus
```

### How your code runs

`cut -d' ' -f2` extracts the author (field 2), and `sort -u` sorts and removes duplicates. Pipelines like this are exactly how you analyze real Git history.

### Starter code

```bash
cut -d' ' -f2 | sort -u
```

Good luck!""",
        starter_code='''cut -d' ' -f2 | sort -u
''',
        test_cases=[
            {"input": "a1 Ada\na2 Linus\nb1 Ada\n", "expected_output": "Ada\nLinus", "description": "Duplicates removed"},
            {"input": "c1 Grace\nc2 Ada\nc3 Grace\n", "expected_output": "Ada\nGrace", "description": "Sorted unique"},
            {"input": "x1 Sam\n", "expected_output": "Sam", "description": "Single author"},
        ],
    ),
    L(
        id="tools-collab-exercise-lines",
        course_id="git-linux-developer-tools",
        module_id="tools-collab",
        title="Exercise: Sum Changed Lines",
        type="exercise",
        order=7,
        content="""## Exercise: Sum Changed Lines

Write a bash script that reads lines of the form `FILENAME COUNT` and prints the total number of changed lines across all files.

### Worked sample

Input:

```text
src/app.py 12
src/utils.py 5
README.md 2
```

Output:

```text
19
```

### How your code runs

`awk` reads each line and accumulates field 2 (`$2`). In the `END` block it prints the running total — a one-line summary of a whole diff.

### Starter code

```bash
awk '{ total += $2 } END { print total }'
```

Good luck!""",
        starter_code='''awk '{ total += $2 } END { print total }'
''',
        test_cases=[
            {"input": "src/app.py 12\nsrc/utils.py 5\nREADME.md 2\n", "expected_output": "19", "description": "Three files"},
            {"input": "a.py 3\nb.py 4\n", "expected_output": "7", "description": "Two files"},
            {"input": "big.py 100\n", "expected_output": "100", "description": "Single file"},
        ],
    ),
]
