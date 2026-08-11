# Curriculum Content Contract

Rules for every course content module in `backend/scripts/curriculum/courses/`.

## File structure

Each course is a Python module with three module-level names:

```python
COURSE = {...}        # dict matching Course schema
MODULES = [...]       # list of dicts matching Module schema
LESSONS = [...]       # list of dicts matching Lesson schema
```

Use the shared helper pattern from `intro_to_r.py`: a local `L(**kw)` helper that
defaults `language` and `order` fields, or set them explicitly on every dict.

IDs:

- Course id: kebab-case slug, **<= 36 chars**.
- Module ids: kebab-case slug, **<= 36 chars**.
- Lesson ids: kebab-case slug, **<= 36 chars**, unique within the course.
- Every module/lesson `course_id` must equal `COURSE["id"]`.
- Every lesson `module_id` must reference a module in `MODULES`.

Order:

- Modules: `order` 1..5.
- Lessons: `order` 1..7 within each module, laid out as **4 theory then 3 exercises**.

## Lesson fields

- `id`, `course_id`, `module_id`, `title`, `type` ("theory" | "exercise"), `order`, `language`.
- Theory: `content` = markdown, substantive (100-300 words), with `## Heading`, code
  fences, tables where helpful, and a `**Next up:** ...` footer line.
- Exercise: `content` = markdown explaining the task with at least one worked sample,
  plus `starter_code` (string) and `test_cases` (list of
  `{"input": ..., "expected_output": ..., "description": ...}`). **Every exercise
  must be runnable** with the language contract below and its starter code must pass
  its own test cases.

## Exercise contracts per language

### R (`language: "r"`)

- User writes functions with `<-`. The **last top-level function defined** is the entry
  point; it receives the raw standard-input text as a single string argument.
- Test `input` = raw text (may contain newlines, use `\n` in JSON), `expected_output`
  = exact output string.
- Starter pattern:

```r
solve <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  # parse lines, compute, return text
  return(as.character(result))
}
```

- Use only base R (no external packages). No `library()` calls.

### Python (`language: "python"`)

- The runner calls the **first `def`** function with positional args parsed from the
  input lines (JSON when possible, else raw text).
- Test `input` = one JSON-compatible value per line (e.g. `3\n5` or `[2,7,11,15]\n9`),
  `expected_output` = the printed result string.
- Starter pattern:

```python
def solve(a, b):
    return a + b

def main():
    a = int(input().strip())
    b = int(input().strip())
    print(solve(a, b))

if __name__ == "__main__":
    main()
```

- Multiple-line inputs map to multiple positional args. Keep it simple: 1-3 args.

### JavaScript (`language: "javascript"`)

- The runner calls the first declared function (`function name(` or
  `const name = (...) =>`) with args parsed from input lines as JSON.
- Test `input` = one JSON-compatible value per line, `expected_output` = printed result.
- Starter pattern:

```javascript
function solve(a, b) {
  return a + b;
}

function main() {
  const lines = require('fs').readFileSync(0, 'utf-8').trim().split('\n');
  const [a, b] = lines.map(Number);
  console.log(solve(a, b));
}

if (require.main === module) main();
```

- Do NOT redeclare `require('fs')` or add `const fs` yourself — the wrapper provides it.

### Bash (`language: "bash"`)

- The whole script is the solution: it reads standard input with `read` / `cat` and
  prints output with `echo` / `printf`.
- Test `input` = raw text, `expected_output` = exact stdout.
- Starter pattern:

```bash
read a
read b
echo $((a + b))
```

- Pure shell built-ins only (`read`, `echo`, `printf`, `if`, `for`, arithmetic, `grep`,
  `sort`, `cut`, `tr`, `awk`). No `git`, no network, no package installs.

## Build + verify

After writing the module, run:

```bash
cd backend
.venv/bin/python scripts/curriculum/build_all.py --course <course-id>
.venv/bin/python scripts/curriculum/verify_exercises.py --course <course-id>
```

`build_all.py` validates against the Pydantic schemas and writes the JSON files.
`verify_exercises.py` runs every runnable exercise's starter code through the live
Piston sandbox. Fix any FAIL until the course reports `0 failures`. Transient
piston timeouts can be retried once.
