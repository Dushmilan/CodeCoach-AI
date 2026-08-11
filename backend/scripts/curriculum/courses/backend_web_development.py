"""Backend Web Development — curriculum content module."""

COURSE = {
    "id": "backend-web-development",
    "title": "Backend Web Development",
    "description": (
        "Go server-side: HTTP and the web, REST API design, persistence and "
        "databases, authentication and security, and finally a complete "
        "authenticated API in the style of FastAPI. Every concept is paired with "
        "runnable exercises in a Python sandbox plus a conceptual design capstone."
    ),
    "language": "python",
    "icon": "server",
    "order": 11,
}

MODULES = [
    {
        "id": "backend-http",
        "course_id": "backend-web-development",
        "title": "Web and HTTP Fundamentals",
        "description": "Requests and responses, methods, status codes, and JSON — the language every web client and server speaks.",
        "order": 1,
    },
    {
        "id": "backend-api",
        "course_id": "backend-web-development",
        "title": "API Development",
        "description": "Routing, validation, serialization, and REST conventions — the craft of designing endpoints people actually enjoy using.",
        "order": 2,
    },
    {
        "id": "backend-persistence",
        "course_id": "backend-web-development",
        "title": "Persistence",
        "description": "Relational data concepts, the repository pattern, migrations, and transactions — storing data safely and reliably.",
        "order": 3,
    },
    {
        "id": "backend-auth",
        "course_id": "backend-web-development",
        "title": "Authentication and Security",
        "description": "Password hashing, tokens, authorization, and input validation — keeping data and users safe.",
        "order": 4,
    },
    {
        "id": "backend-project",
        "course_id": "backend-web-development",
        "title": "Backend Project",
        "description": "Design and build a complete authenticated API — models, endpoints, auth wiring, and deployment.",
        "order": 5,
    },
]

_PY = "python"


def L(**kw):
    kw.setdefault("language", _PY)
    return kw


LESSONS = [
    # ── Module 1: Web and HTTP Fundamentals ────────────────────────────
    L(
        id="backend-http-requests",
        course_id="backend-web-development",
        module_id="backend-http",
        title="HTTP Requests",
        type="theory",
        order=1,
        content="""## HTTP Requests

The web runs on **HTTP** — a request/response protocol. A client (browser, app, or script) sends a **request**, and a server returns a **response**.

### The anatomy of a request

```text
GET /api/users/42?page=2 HTTP/1.1
Host: api.example.com
Accept: application/json
Authorization: Bearer abc123
```

| Piece        | Example               | Meaning                          |
|--------------|-----------------------|----------------------------------|
| Method       | `GET`                 | What to do                       |
| Path         | `/api/users/42`       | Which resource                   |
| Query string | `?page=2`             | Extra parameters                 |
| Headers      | `Accept: ...`         | Metadata about the request       |
| Body         | (POST/PUT only)       | Data being sent                  |

### Methods

| Method   | Meaning                         |
|----------|---------------------------------|
| `GET`    | Read a resource                 |
| `POST`   | Create a resource               |
| `PUT`    | Replace a resource              |
| `PATCH`  | Partially update a resource     |
| `DELETE` | Remove a resource               |

### URL parts

A full URL decomposes cleanly:

```text
https://api.example.com:443/api/users/42?page=2
|scheme| |---host---| |port| |--path--| |query--|
```

The **path** selects the resource; the **query string** carries optional parameters as `key=value` pairs joined by `&`.

### Headers

Headers carry metadata — content types, authentication, caching:

- `Content-Type` — format of the body (`application/json`).
- `Accept` — format the client wants back.
- `Authorization` — credentials (often a token).

### Request bodies

`GET` has no body. `POST` and `PUT` send one, typically JSON:

```json
{ "name": "Ada", "age": 36 }
```

---

**Next up:** HTTP responses — status codes and what the server sends back."""
    ),
    L(
        id="backend-http-responses",
        course_id="backend-web-development",
        module_id="backend-http",
        title="HTTP Responses and Status Codes",
        type="theory",
        order=2,
        content="""## HTTP Responses and Status Codes

Every request gets a **response**: a status line, headers, and usually a body.

### The anatomy of a response

```text
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 31

{ "name": "Ada", "age": 36 }
```

### Status code families

The first digit tells you the class:

| Code range | Class         | Meaning                          |
|------------|---------------|----------------------------------|
| 1xx        | Informational | Request received, processing     |
| 2xx        | Success       | It worked                        |
| 3xx        | Redirection   | Go somewhere else                |
| 4xx        | Client error  | The request was the problem      |
| 5xx        | Server error  | The server failed                |

### Status codes you will meet constantly

| Code  | Meaning                          | When to use                      |
|-------|----------------------------------|----------------------------------|
| 200   | OK                               | Successful `GET`                 |
| 201   | Created                          | Successful `POST`                |
| 204   | No Content                       | Successful delete                |
| 400   | Bad Request                      | Malformed or invalid input       |
| 401   | Unauthorized                     | Missing/invalid credentials      |
| 403   | Forbidden                        | Not allowed to act               |
| 404   | Not Found                        | Resource does not exist          |
| 409   | Conflict                         | Duplicate or state conflict      |
| 422   | Unprocessable Entity             | Valid JSON, invalid semantics    |
| 500   | Internal Server Error            | Unexpected server failure        |

### The golden rule

Pick the code that describes the *situation*, not the code you happen to produce. A missing resource is `404`, not `500`. A bad request is `400`, not `200` with an error string.

### Response bodies

Responses usually carry JSON. Errors are also JSON, with a consistent shape:

```json
{ "error": "not_found", "message": "User 42 not found" }
```

A predictable error shape makes API clients far easier to write.

---

**Next up:** HTTP methods and JSON — the working tools of every backend."""
    ),
    L(
        id="backend-http-methods-json",
        course_id="backend-web-development",
        module_id="backend-http",
        title="Methods, Semantics, and JSON",
        type="theory",
        order=3,
        content="""## Methods, Semantics, and JSON

Choosing the right method is about **semantics** — saying what you mean so clients and proxies can reason about your API.

### Method semantics

| Method   | Safe | Idempotent | Purpose            |
|----------|------|------------|--------------------|
| `GET`    | yes  | yes        | Read               |
| `POST`   | no   | no         | Create / act       |
| `PUT`    | no   | yes        | Replace            |
| `PATCH`  | no   | no         | Partial update     |
| `DELETE` | no   | yes        | Remove             |

- **Safe** methods never change server state — a client can call them repeatedly without side effects.
- **Idempotent** methods produce the same result no matter how many times they run. Sending `DELETE` twice is fine; sending `POST` twice may create two records.

### PUT vs PATCH

`PUT` replaces the whole resource with what you send. `PATCH` applies only the fields you send:

```text
PUT    /api/users/42   {"name":"Ada","age":37}   # replaces both
PATCH  /api/users/42   {"age":37}                 # changes only age
```

### JSON: the wire format

JSON is the de-facto API format. Python maps it directly:

```python
import json

data = json.loads('{"name": "Ada", "skills": ["py", "js"]}')
data["name"]             # "Ada"
json.dumps({"ok": True}) # '{"ok": true}'
```

| JSON        | Python   |
|-------------|----------|
| `{}`        | dict     |
| `[]`        | list     |
| `"str"`     | str      |
| `123`       | int      |
| `true`      | True     |
| `null`      | None     |

### Content-Type

Always set `Content-Type: application/json` when a body is JSON — both when sending and when responding. Clients and frameworks rely on it.

---

**Next up:** exercises — parsing URLs, query strings, and status codes."""
    ),
    L(
        id="backend-http-request-lifecycle",
        course_id="backend-web-development",
        module_id="backend-http",
        title="The Request Lifecycle",
        type="theory",
        order=4,
        content="""## The Request Lifecycle

A single API call travels through a pipeline. Understanding the pipeline explains where errors happen and where to look for them.

### The journey

```text
Client ──▶ DNS ──▶ TCP/TLS ──▶ Server ──▶ Router ──▶ Handler ──▶ Database
                                                                     │
Client ◀── response ◀── serialization ◀─── result ◀──────────────────┘
```

### 1. Resolution and transport

The client resolves the hostname (DNS) and opens a connection. HTTPS encrypts this leg with TLS. Most network errors — timeouts, refused connections — live here.

### 2. The router

The server's **router** matches the request method + path to a handler:

```python
# FastAPI-style
@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    return {"id": user_id}
```

### 3. Parsing and validation

The framework parses the body and query string, then validates them against the declared types. Bad input is rejected here with a `400`/`422` — before your handler code runs.

### 4. The handler and data layer

The handler runs the business logic and talks to the database (or repository). This is where real errors originate — missing rows, failed writes, bugs.

### 5. Serialization and response

The result is converted to JSON (serialization) and returned with a status code and headers. The framework's exception handling converts any uncaught error into a clean `500`.

### Where to look for bugs

- Client-side timeout or DNS error → step 1.
- `400`/`422` → your client sent something the schema rejects.
- `404` → routing or a missing record.
- `500` → server bug; check logs.

Knowing the lifecycle means you can diagnose an issue by its status code in seconds.

---

**Next up:** Module 2 — turning raw HTTP into a well-designed API."""
    ),
    L(
        id="backend-http-exercise-parse-url",
        course_id="backend-web-development",
        module_id="backend-http",
        title="Exercise: Parse a URL Path",
        type="exercise",
        order=5,
        content="""## Exercise: Parse a URL Path

Write a function `solve(url)` that returns the **path** part of a URL — everything before the query string.

### Sample

Input: `/api/users/42?page=2`

Output:

```text
/api/users/42
```

### How your code runs

The runner calls `solve(url)` with one argument: the URL string. Split on `"?"` and return the first part.

### Starter code

```python
def solve(url):
    return url.split("?")[0]


def main():
    import sys
    raw = sys.stdin.read().strip()
    print(solve(raw))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(url):
    return url.split("?")[0]


def main():
    import sys
    raw = sys.stdin.read().strip()
    print(solve(raw))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "/api/users/42?page=2", "expected_output": "/api/users/42", "description": "With a query string"},
            {"input": "/api/users", "expected_output": "/api/users", "description": "No query string"},
            {"input": "/search?q=js&lang=en", "expected_output": "/search", "description": "Multiple parameters"},
            {"input": "/", "expected_output": "/", "description": "Root path"},
        ],
    ),
    L(
        id="backend-http-exercise-query-parser",
        course_id="backend-web-development",
        module_id="backend-http",
        title="Exercise: Query-String Parser",
        type="exercise",
        order=6,
        content="""## Exercise: Query-String Parser

Write a function `solve(qs)` that parses a query string into a dictionary and returns it as a JSON string.

### Sample

Input: `search=python&page=2`

Output:

```text
{"search": "python", "page": "2"}
```

### How your code runs

The runner calls `solve(qs)` with one argument: the raw query string (no leading `?`). Split on `&`, then on `=`, build a dict, and return `json.dumps(result)`.

### Starter code

```python
import json


def solve(qs):
    params = {}
    if not qs:
        return json.dumps(params)
    for pair in qs.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            params[key] = value
    return json.dumps(params)


def main():
    import sys
    raw = sys.stdin.read().strip()
    print(solve(raw))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''import json


def solve(qs):
    params = {}
    if not qs:
        return json.dumps(params)
    for pair in qs.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            params[key] = value
    return json.dumps(params)


def main():
    import sys
    raw = sys.stdin.read().strip()
    print(solve(raw))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "search=python&page=2", "expected_output": '{"search": "python", "page": "2"}', "description": "Two parameters"},
            {"input": "page=2", "expected_output": '{"page": "2"}', "description": "Single parameter"},
            {"input": "", "expected_output": "{}", "description": "Empty query string"},
            {"input": "a=1&b=2&c=3", "expected_output": '{"a": "1", "b": "2", "c": "3"}', "description": "Three parameters"},
        ],
    ),
    L(
        id="backend-http-exercise-status-class",
        course_id="backend-web-development",
        module_id="backend-http",
        title="Exercise: Classify a Status Code",
        type="exercise",
        order=7,
        content="""## Exercise: Classify a Status Code

Write a function `solve(status)` that returns the **class name** for an HTTP status code:

- `100`–`199` → `informational`
- `200`–`299` → `success`
- `300`–`399` → `redirect`
- `400`–`499` → `client error`
- `500`–`599` → `server error`
- anything else → `unknown`

### Sample

Input: `404`

Output:

```text
client error
```

### How your code runs

The runner calls `solve(status)` with one integer. Return the class string.

### Starter code

```python
def solve(status):
    if 100 <= status <= 199:
        return "informational"
    if 200 <= status <= 299:
        return "success"
    if 300 <= status <= 399:
        return "redirect"
    if 400 <= status <= 499:
        return "client error"
    if 500 <= status <= 599:
        return "server error"
    return "unknown"


def main():
    import sys
    raw = sys.stdin.read().strip()
    if not raw:
        return
    print(solve(int(raw)))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(status):
    if 100 <= status <= 199:
        return "informational"
    if 200 <= status <= 299:
        return "success"
    if 300 <= status <= 399:
        return "redirect"
    if 400 <= status <= 499:
        return "client error"
    if 500 <= status <= 599:
        return "server error"
    return "unknown"


def main():
    import sys
    raw = sys.stdin.read().strip()
    if not raw:
        return
    print(solve(int(raw)))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "404", "expected_output": "client error", "description": "Not found"},
            {"input": "200", "expected_output": "success", "description": "OK"},
            {"input": "500", "expected_output": "server error", "description": "Server failure"},
            {"input": "301", "expected_output": "redirect", "description": "Moved"},
            {"input": "99", "expected_output": "unknown", "description": "Out of range"},
        ],
    ),
    # ── Module 2: API Development ──────────────────────────────────────
    L(
        id="backend-api-routing",
        course_id="backend-web-development",
        module_id="backend-api",
        title="Routing and Path Parameters",
        type="theory",
        order=1,
        content="""## Routing and Path Parameters

A **route** maps a method + path pattern to a handler function. Routing is the front door of every API.

### A basic router

```python
@app.get("/api/users")
def list_users():
    return {"users": [...]}
```

### Path parameters

Parts of the path can be **variables**:

```python
@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    return {"id": user_id}
```

A request to `/api/users/42` binds `user_id = 42`. Frameworks validate and convert types automatically — here `user_id` must be an integer.

### Query parameters

Optional parameters live in the query string:

```python
@app.get("/api/users")
def list_users(page: int = 1, per_page: int = 20):
    return {"page": page, "per_page": per_page}
```

`/api/users?page=2&per_page=10` → `page=2`, `per_page=10`. Omitted parameters fall back to their defaults.

### Route design rules

- **Nouns, not verbs**: `/api/users` not `/api/getUsers`.
- **Plural resources**: `/api/users` and `/api/users/{id}`.
- **Nested resources** for ownership: `/api/users/42/posts`.
- **Consistent casing**: lowercase with hyphens (`per-page`) or underscores — pick one and stay consistent.
- **Order matters** in some routers: static paths before parameterized ones (`/api/users/me` before `/api/users/{user_id}`).

### REST vs RPC

REST models resources and uses HTTP methods as the verbs. RPC exposes action endpoints like `/api/doLogin`. REST scales better for CRUD; RPC lingers for awkward actions — a pragmatic API mixes them.

---

**Next up:** validation — rejecting bad input before it reaches your logic."""
    ),
    L(
        id="backend-api-validation",
        course_id="backend-web-development",
        module_id="backend-api",
        title="Input Validation",
        type="theory",
        order=2,
        content="""## Input Validation

Never trust client input. **Validation** is the gate that rejects bad data before your logic or database ever sees it.

### Types of validation

| Kind          | Example                            |
|---------------|------------------------------------|
| Required      | `name` must be present             |
| Type          | `age` must be an integer           |
| Range         | `age` between 0 and 150            |
| Format        | email must contain `@`             |
| Membership    | status must be one of a set        |
| Uniqueness    | email not already registered       |

### Declarative schemas

FastAPI-style frameworks validate with schema models:

```python
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    age: int = Field(..., ge=0, le=150)
    email: EmailStr
```

The framework validates the incoming JSON against this schema automatically.

### What a validator does

1. Check required fields are present.
2. Convert types (`"36"` → `36`) or reject.
3. Apply constraints (ranges, lengths, formats).
4. Produce a **structured error** with a `400`/`422` status.

### Validation vs sanitization

- **Validation** — reject invalid input.
- **Sanitization** — clean valid-ish input (strip whitespace, trim).

Do both: validate the shape, then sanitize the values.

### Fail fast

Validate **at the boundary** — as soon as the request arrives — so downstream code can assume valid data. Sloppy input drifting into business logic is the source of most bugs and many security holes.

### Error responses

```json
{
  "error": "validation_failed",
  "details": [{"field": "age", "message": "age must be between 0 and 150"}]
}
```

---

**Next up:** serialization — turning models into the JSON clients receive."""
    ),
    L(
        id="backend-api-serialization",
        course_id="backend-web-development",
        module_id="backend-api",
        title="Serialization and Response Models",
        type="theory",
        order=3,
        content="""## Serialization and Response Models

**Serialization** turns internal objects into the JSON clients receive. It is the mirror image of validation — and just as important.

### The problem

Your database row has secrets and internal fields:

```python
user = {"id": 1, "name": "Ada", "password_hash": "...", "is_internal": True}
```

Clients should only ever see the public subset:

```json
{ "id": 1, "name": "Ada" }
```

### Response models

Frameworks declare the public shape explicitly:

```python
class UserOut(BaseModel):
    id: int
    name: str

@app.get("/api/users/{user_id}")
def get_user(user_id: int) -> UserOut:
    return user_row   # framework serializes only declared fields
```

### One schema in, one schema out

| Direction | Model name | Purpose                 |
|-----------|------------|-------------------------|
| In        | `UserCreate` | What clients may send |
| Out       | `UserOut`   | What clients may see  |
| Internal  | (dict/ORM)  | What the app works with |

Keeping **input** and **output** models separate means clients cannot inject fields (like `is_admin`) by adding them to the request.

### Field selection

When serializing by hand, select explicitly — never dump the whole object:

```python
def serialize(user):
    return {"id": user["id"], "name": user["name"]}
```

### Nested data

Relationships become nested JSON:

```json
{ "id": 1, "name": "Ada", "posts": [{ "id": 10, "title": "Hello" }] }
```

Watch for **N+1 queries** when building nested responses — fetch related rows in bulk, not per-parent.

### Consistent shapes

Every endpoint returns a predictable shape. Clients deserve to know what each response looks like — that predictability is what makes an API feel professional.

---

**Next up:** REST conventions — naming, methods, and status for every resource."""
    ),
    L(
        id="backend-api-rest-conventions",
        course_id="backend-web-development",
        module_id="backend-api",
        title="REST Conventions",
        type="theory",
        order=4,
        content="""## REST Conventions

**REST** (Representational State Transfer) is a set of conventions for building APIs around *resources*. Following the conventions makes your API predictable without a manual.

### The resource map

For a `users` resource, the standard surface is small and fixed:

| Method   | Path                 | Purpose                | Success code |
|----------|----------------------|------------------------|--------------|
| `GET`    | `/api/users`         | List / search          | 200          |
| `POST`   | `/api/users`         | Create                 | 201          |
| `GET`    | `/api/users/{id}`    | Read one               | 200          |
| `PUT`    | `/api/users/{id}`    | Replace                | 200          |
| `PATCH`  | `/api/users/{id}`    | Partial update         | 200          |
| `DELETE` | `/api/users/{id}`    | Delete                 | 204          |

Any user of your API can predict every endpoint because the pattern is universal.

### Collection vs item

- **Collection** endpoints: `/api/users`, `/api/posts` — work on the whole set.
- **Item** endpoints: `/api/users/{id}` — work on one member.

### Errors use the right status

- Invalid body → `400`/`422`.
- Missing auth → `401`.
- Wrong permissions → `403`.
- Unknown resource → `404`.
- Duplicate create → `409`.

### Filtering, sorting, pagination

Keep them in the query string:

```text
GET /api/users?filter=status:active&sort=-created_at&page=2&per_page=20
```

### Versioning

Changing a public API breaks clients. Version it:

```text
/api/v1/users
/api/v2/users
```

### Consistency beats cleverness

The REST conventions exist so that "what would this endpoint do?" has an obvious answer. When in doubt, match the standard pattern instead of inventing a new one — your future clients will thank you.

---

**Next up:** exercises — validation, pagination math, and serialization."""
    ),
    L(
        id="backend-api-exercise-validate",
        course_id="backend-web-development",
        module_id="backend-api",
        title="Exercise: JSON Field Validation",
        type="exercise",
        order=5,
        content="""## Exercise: JSON Field Validation

Write a function `solve(payload)` that validates a JSON object. The required fields are `name` and `email`.

- If both are present, return `ok`.
- Otherwise return `missing: ` followed by the missing field names joined by `, `.

### Sample

Input:

```text
{"name": "Ada"}
```

Output:

```text
missing: email
```

### How your code runs

The runner calls `solve(payload)` with one argument: a dictionary parsed from the JSON input. Check each required field with `in`.

### Starter code

```python
def solve(payload):
    required = ["name", "email"]
    missing = [field for field in required if field not in payload]
    if not missing:
        return "ok"
    return "missing: " + ", ".join(missing)


def main():
    import sys, json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    print(solve(json.loads(raw)))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(payload):
    required = ["name", "email"]
    missing = [field for field in required if field not in payload]
    if not missing:
        return "ok"
    return "missing: " + ", ".join(missing)


def main():
    import sys, json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    print(solve(json.loads(raw)))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '{"name": "Ada", "email": "ada@x.com"}', "expected_output": "ok", "description": "All fields present"},
            {"input": '{"name": "Ada"}', "expected_output": "missing: email", "description": "Email missing"},
            {"input": "{}", "expected_output": "missing: name, email", "description": "Everything missing"},
            {"input": '{"name": "Ada", "email": "ada@x.com", "age": 36}', "expected_output": "ok", "description": "Extra fields are fine"},
        ],
    ),
    L(
        id="backend-api-exercise-pagination",
        course_id="backend-web-development",
        module_id="backend-api",
        title="Exercise: Pagination Math",
        type="exercise",
        order=6,
        content="""## Exercise: Pagination Math

Write a function `solve(total, page, per_page)` that returns a JSON string describing a page of results:

- `total_pages` — the number of pages needed
- `page` — the requested page
- `offset` — the 0-based start index for this page: `(page - 1) * per_page`

Use `math.ceil` for the page count. An empty dataset has `0` total pages.

### Sample

Input:

```text
25
2
10
```

Output:

```text
{"total_pages": 3, "page": 2, "offset": 10}
```

### How your code runs

The runner calls `solve(total, page, per_page)` with three integers parsed from the three input lines. Return `json.dumps(result)`.

### Starter code

```python
import json
import math


def solve(total, page, per_page):
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return json.dumps({"total_pages": total_pages, "page": page, "offset": (page - 1) * per_page})


def main():
    import sys, json as _json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    lines = raw.split("\\n")
    total, page, per_page = [int(ln) for ln in lines]
    print(solve(total, page, per_page))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''import json
import math


def solve(total, page, per_page):
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return json.dumps({"total_pages": total_pages, "page": page, "offset": (page - 1) * per_page})


def main():
    import sys, json as _json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    lines = raw.split("\\n")
    total, page, per_page = [int(ln) for ln in lines]
    print(solve(total, page, per_page))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "25\n2\n10", "expected_output": '{"total_pages": 3, "page": 2, "offset": 10}', "description": "Second page"},
            {"input": "10\n1\n10", "expected_output": '{"total_pages": 1, "page": 1, "offset": 0}', "description": "Single page"},
            {"input": "95\n4\n20", "expected_output": '{"total_pages": 5, "page": 4, "offset": 60}', "description": "Rounded up page count"},
            {"input": "0\n1\n10", "expected_output": '{"total_pages": 0, "page": 1, "offset": 0}', "description": "Empty dataset"},
        ],
    ),
    L(
        id="backend-api-exercise-serialize",
        course_id="backend-web-development",
        module_id="backend-api",
        title="Exercise: Serialize a Resource",
        type="exercise",
        order=7,
        content="""## Exercise: Serialize a Resource

Write a function `solve(user)` that returns a JSON string containing only the **public fields** `id`, `name`, and `email` — never leaking internal fields.

### Sample

Input:

```text
{"id": 1, "name": "Ada", "email": "ada@x.com", "password_hash": "abc123"}
```

Output:

```text
{"id": 1, "name": "Ada", "email": "ada@x.com"}
```

### How your code runs

The runner calls `solve(user)` with one dictionary parsed from the JSON input. Build a new dict with only the public keys and return `json.dumps(result)`.

### Starter code

```python
import json


def solve(user):
    public = ["id", "name", "email"]
    result = {field: user[field] for field in public if field in user}
    return json.dumps(result)


def main():
    import sys, json as _json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    print(solve(_json.loads(raw)))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''import json


def solve(user):
    public = ["id", "name", "email"]
    result = {field: user[field] for field in public if field in user}
    return json.dumps(result)


def main():
    import sys, json as _json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    print(solve(_json.loads(raw)))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '{"id": 1, "name": "Ada", "email": "ada@x.com", "password_hash": "abc123"}', "expected_output": '{"id": 1, "name": "Ada", "email": "ada@x.com"}', "description": "Secrets excluded"},
            {"input": '{"name": "Bob"}', "expected_output": '{"name": "Bob"}', "description": "Partial fields"},
            {"input": '{"id": 5, "email": "e@x.com"}', "expected_output": '{"id": 5, "email": "e@x.com"}', "description": "Missing name is fine"},
        ],
    ),
    # ── Module 3: Persistence ──────────────────────────────────────────
    L(
        id="backend-persistence-relational",
        course_id="backend-web-development",
        module_id="backend-persistence",
        title="Relational Data Concepts",
        type="theory",
        order=1,
        content="""## Relational Data Concepts

Relational databases store data in **tables** with rows and columns, and connect them with **keys**. Most production backends sit on one.

### The table

A table is a grid: columns define the shape, rows are records.

```text
users
| id | name  | email          | created_at      |
|----|-------|----------------|-----------------|
| 1  | Ada   | ada@x.com      | 2025-01-01 10:00|
| 2  | Linus | linus@x.com    | 2025-01-02 09:30|
```

### Keys

| Key             | Purpose                                  |
|-----------------|------------------------------------------|
| Primary key     | Uniquely identifies each row (usually `id`) |
| Foreign key     | References a row in another table        |
| Unique          | No two rows share this value             |
| Index           | Speeds up lookups (not a constraint)     |

### Relationships

- **One-to-many**: one user → many posts (posts hold `user_id`).
- **Many-to-many**: users ↔ courses, joined by a link table.
- **One-to-one**: user ↔ profile (rarely needed).

### Normalization

**Normalization** removes duplicate data by splitting it into related tables. A phone number stored in three places is a bug waiting to happen — store it once and reference it.

### Constraints enforce integrity

```sql
CREATE TABLE users (
  id    INTEGER PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  age   INTEGER CHECK (age >= 0)
);
```

The database itself refuses bad rows — `NOT NULL`, `UNIQUE`, and `CHECK` are guard rails your app does not have to re-implement.

### SQL in one glance

```sql
SELECT id, name FROM users WHERE age >= 18 ORDER BY name LIMIT 10;
INSERT INTO users (name, email) VALUES ('Ada', 'ada@x.com');
UPDATE users SET age = 37 WHERE id = 1;
DELETE FROM users WHERE id = 2;
```

These four statements map directly onto the CRUD operations your API exposes.

---

**Next up:** the repository pattern — keeping SQL out of your endpoints."""
    ),
    L(
        id="backend-persistence-repository",
        course_id="backend-web-development",
        module_id="backend-persistence",
        title="The Repository Pattern",
        type="theory",
        order=2,
        content="""## The Repository Pattern

A **repository** is the layer between your application logic and the database. It presents a simple, business-shaped interface and hides all the SQL inside.

### Why a separate layer

Without repositories, endpoint handlers fill up with raw queries. Every query gets duplicated, and swapping storage means touching every handler.

### The shape of a repository

```python
class UserRepository:
    def list(self, filters=None): ...
    def get(self, user_id): ...
    def create(self, data): ...
    def update(self, user_id, data): ...
    def delete(self, user_id): ...
```

Handlers only see these method calls — never a SQL string.

### The payoff

| Concern        | Lives in repository   | Not in handler |
|----------------|-----------------------|----------------|
| SQL            | yes                   | no             |
| Connection handling | yes              | no             |
| Error mapping  | yes                   | no             |
| Business logic | no                    | yes            |

### Repository vs service

Keep the two layers separate:

- **Repository** — mechanical data access (fetch, save, delete).
- **Service** — business rules (authorization, workflows, validation).

```python
def create_post(user, post_data):          # service
    if not user.is_premium and post_data["size"] > 1_000_000:
        raise ForbiddenError("limit reached")
    return post_repo.create(user.id, post_data)   # repository
```

### Testing wins

Because the repository interface is small, you can swap a real database for an **in-memory implementation** in tests — exactly what the exercises in this module do with plain lists.

### Keep it honest

A repository is not a dump of every possible query. Keep methods named after **business intent** (`find_active`, not `select_where_flag_1`) and resist the urge to add a query per handler.

---

**Next up:** migrations — evolving the schema safely."""
    ),
    L(
        id="backend-persistence-migrations",
        course_id="backend-web-development",
        module_id="backend-persistence",
        title="Migrations",
        type="theory",
        order=3,
        content="""## Migrations

Schemas change: new columns, new tables, renamed fields. **Migrations** are versioned, ordered scripts that evolve the database safely.

### The idea

Each migration has a number and describes one change:

```text
001_create_users.sql        CREATE TABLE users (...);
002_add_bio_to_users.sql     ALTER TABLE users ADD COLUMN bio TEXT;
003_create_posts.sql         CREATE TABLE posts (...);
```

A table records which migrations have run:

```text
schema_migrations
| version | applied_at        |
|---------|-------------------|
| 1       | 2025-01-01 10:00  |
| 2       | 2025-01-01 10:05  |
```

### Forward and rollback

Each migration usually ships a forward and a rollback script:

```sql
-- 002_add_bio_to_users.sql
ALTER TABLE users ADD COLUMN bio TEXT;

-- 002_add_bio_to_users.down.sql
ALTER TABLE users DROP COLUMN bio;
```

Rollbacks let you undo a bad release cleanly.

### Why migrations beat manual SQL

- **Reproducible**: a new environment runs the whole history and gets the same schema.
- **Auditable**: every change is recorded with its intent.
- **Reviewable**: schema changes get code-reviewed like code.

### Migration discipline

- Never edit a migration that already ran — write a new one.
- Keep migrations **idempotent-ish**: they run once, in order.
- Test rollbacks in staging.
- Back up before destructive migrations (`DROP`, `RENAME`).

### In practice

Tools like Alembic (SQLAlchemy), Prisma, and Django's `makemigrations` generate and apply migrations. You still decide *what* changes — they handle *when* and *how*.

---

**Next up:** transactions — keeping writes atomic and consistent."""
    ),
    L(
        id="backend-persistence-transactions",
        course_id="backend-web-development",
        module_id="backend-persistence",
        title="Transactions",
        type="theory",
        order=4,
        content="""## Transactions

A **transaction** groups several operations so they succeed or fail **together**. If any step fails, the whole group rolls back — the database returns to its previous state.

### The classic example

Transferring money touches two rows:

```text
1. debit  user A  -100
2. credit user B  +100
```

If step 2 fails, step 1 must not stand alone — that would create money.

### ACID

| Property | Meaning                                             |
|----------|-----------------------------------------------------|
| Atomicity| All steps succeed or all are undone                 |
| Consistency | Data stays valid (constraints hold)            |
| Isolation | Concurrent transactions do not corrupt each other   |
| Durability| Committed data survives crashes                     |

### Transaction control

```python
with db.transaction():      # BEGIN
    account_repo.debit(a_id, 100)
    account_repo.credit(b_id, 100)
                            # COMMIT on success
                            # ROLLBACK on any exception
```

The context manager commits on success and rolls back on any raised error.

### When to use transactions

- Multi-row writes that must stay consistent (balances, orders, inventory).
- Writes plus a dependent write ("create user, then create their profile").
- Any operation where a partial result is worse than no result.

### When not to

Long transactions hold locks and hurt concurrency. Keep them **short and focused** — do slow work (network calls, heavy computation) outside the transaction.

### The read-your-own-write rule

If a handler writes then immediately reads, and the reads must see the write, do both inside one transaction or transaction-ish boundary. Otherwise a cached or uncommitted read can bite you.

---

**Next up:** exercises — a CRUD repository, a ledger, and migration versions."""
    ),
    L(
        id="backend-persistence-exercise-repo",
        course_id="backend-web-development",
        module_id="backend-persistence",
        title="Exercise: In-Memory Repository",
        type="exercise",
        order=5,
        content="""## Exercise: In-Memory Repository

Write a function `solve(request)` that simulates a **repository over a list passed as JSON**. The request is a dict:

- `records` — the current list of `{"id": ..., "name": ...}` rows
- `action` — `"create"` or `"delete"`
- `record` — for create, the row to add; for delete, an object with the `id` to remove

Return the resulting list as a **JSON string**.

### Sample

Input:

```text
{"records": [{"id": 1, "name": "Ada"}], "action": "create", "record": {"id": 2, "name": "Bob"}}
```

Output:

```text
[{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]
```

### How your code runs

The runner calls `solve(request)` with one dictionary. Mutate a copy of `records`, then return `json.dumps(result)`.

### Starter code

```python
import json


def solve(request):
    records = list(request["records"])
    action = request["action"]
    record = request["record"]
    if action == "create":
        records.append(record)
    elif action == "delete":
        records = [r for r in records if r["id"] != record["id"]]
    return json.dumps(records)


def main():
    import sys, json as _json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    print(solve(_json.loads(raw)))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''import json


def solve(request):
    records = list(request["records"])
    action = request["action"]
    record = request["record"]
    if action == "create":
        records.append(record)
    elif action == "delete":
        records = [r for r in records if r["id"] != record["id"]]
    return json.dumps(records)


def main():
    import sys, json as _json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    print(solve(_json.loads(raw)))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '{"records": [{"id": 1, "name": "Ada"}], "action": "create", "record": {"id": 2, "name": "Bob"}}', "expected_output": '[{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]', "description": "Create appends"},
            {"input": '{"records": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}], "action": "delete", "record": {"id": 1}}', "expected_output": '[{"id": 2, "name": "Bob"}]', "description": "Delete by id"},
            {"input": '{"records": [], "action": "create", "record": {"id": 9, "name": "Eve"}}', "expected_output": '[{"id": 9, "name": "Eve"}]', "description": "Create into empty list"},
            {"input": '{"records": [{"id": 1, "name": "Ada"}], "action": "delete", "record": {"id": 99}}', "expected_output": '[{"id": 1, "name": "Ada"}]', "description": "Delete missing id is a no-op"},
        ],
    ),
    L(
        id="backend-persistence-exercise-ledger",
        course_id="backend-web-development",
        module_id="backend-persistence",
        title="Exercise: Ledger Balance",
        type="exercise",
        order=6,
        content="""## Exercise: Ledger Balance

Write a function `solve(transactions, start)` that applies a list of transactions to a starting balance and returns the final balance.

Each transaction is `{"type": "credit" | "debit", "amount": n}`. Credits add, debits subtract. **A debit larger than the current balance is rejected** (the balance never goes negative — a simple consistency rule).

### Sample

Input:

```text
[{"type": "credit", "amount": 100}, {"type": "debit", "amount": 30}]
50
```

Output:

```text
120
```

### How your code runs

The runner calls `solve(transactions, start)` with a JSON list and an integer parsed from the two input lines. Return the final balance.

### Starter code

```python
def solve(transactions, start):
    balance = start
    for tx in transactions:
        if tx["type"] == "credit":
            balance += tx["amount"]
        elif tx["type"] == "debit":
            if tx["amount"] <= balance:
                balance -= tx["amount"]
    return balance


def main():
    import sys, json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    lines = raw.split("\\n")
    transactions = json.loads(lines[0])
    start = int(lines[1])
    print(solve(transactions, start))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(transactions, start):
    balance = start
    for tx in transactions:
        if tx["type"] == "credit":
            balance += tx["amount"]
        elif tx["type"] == "debit":
            if tx["amount"] <= balance:
                balance -= tx["amount"]
    return balance


def main():
    import sys, json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    lines = raw.split("\\n")
    transactions = json.loads(lines[0])
    start = int(lines[1])
    print(solve(transactions, start))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '[{"type": "credit", "amount": 100}, {"type": "debit", "amount": 30}]\n50', "expected_output": "120", "description": "Credit then debit"},
            {"input": '[{"type": "debit", "amount": 200}]\n50', "expected_output": "50", "description": "Overdraft rejected"},
            {"input": '[]\n100', "expected_output": "100", "description": "No transactions"},
            {"input": '[{"type": "credit", "amount": 5}, {"type": "credit", "amount": 5}]\n0', "expected_output": "10", "description": "Two credits"},
        ],
    ),
    L(
        id="backend-persistence-exercise-schema",
        course_id="backend-web-development",
        module_id="backend-persistence",
        title="Exercise: Pending Migrations",
        type="exercise",
        order=7,
        content="""## Exercise: Pending Migrations

Write a function `solve(applied, latest)` that returns the list of **migration versions that still need to run**: every version from `1` up to `latest` that is not already in `applied`.

### Sample

Input:

```text
[1, 2]
4
```

Versions `1` and `2` are applied; `3` and `4` are not. Output:

```text
[3,4]
```

### How your code runs

The runner calls `solve(applied, latest)` with a JSON list and an integer parsed from the two input lines. Return the list of pending versions.

### Starter code

```python
def solve(applied, latest):
    applied_set = set(applied)
    return [v for v in range(1, latest + 1) if v not in applied_set]


def main():
    import sys, json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    lines = raw.split("\\n")
    applied = json.loads(lines[0])
    latest = int(lines[1])
    print(json.dumps(solve(applied, latest), separators=(",", ":")))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(applied, latest):
    applied_set = set(applied)
    return [v for v in range(1, latest + 1) if v not in applied_set]


def main():
    import sys, json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    lines = raw.split("\\n")
    applied = json.loads(lines[0])
    latest = int(lines[1])
    print(json.dumps(solve(applied, latest), separators=(",", ":")))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "[1, 2]\n4", "expected_output": "[3,4]", "description": "Two pending"},
            {"input": "[1, 2, 3, 4]\n4", "expected_output": "[]", "description": "All applied"},
            {"input": "[]\n2", "expected_output": "[1,2]", "description": "Fresh database"},
            {"input": "[2]\n3", "expected_output": "[1,3]", "description": "Gap in the middle"},
        ],
    ),


    # ── Module 4: Authentication and Security ──────────────────────────
    L(
        id="backend-auth-passwords",
        course_id="backend-web-development",
        module_id="backend-auth",
        title="Password Hashing",
        type="theory",
        order=1,
        content="""## Password Hashing

Storing passwords in plain text is catastrophic — a single leaked database exposes every account. The correct approach is **hashing**.

### Hashing vs encryption

|           | Hashing                          | Encryption                       |
|-----------|----------------------------------|----------------------------------|
| Direction | One-way                          | Two-way                          |
| Reversible| No                               | Yes, with a key                 |
| Purpose   | Verify without storing           | Protect data you must read back |

Encryption is reversible by design — which means anyone with the key (or a stolen key) can decrypt. Hashes cannot be reversed, so a leaked hash database is far less useful.

### How it works

```python
stored = hash_function(password)      # store ONLY this
...later...
if hash_function(attempt) == stored:  # compare hashes
    allow()
```

### Salting

Two users with the same password get the same hash — attackers exploit that with **rainbow tables**. A **salt** is random data mixed into each hash:

```python
salt = os.urandom(16)
stored = hash_function(salt + password) + salt
```

Now identical passwords produce different hashes, and precomputed tables are useless.

### Slow is a feature

Fast hashes (MD5, SHA-256) let attackers try billions of guesses per second. Password hashes are designed to be **slow**:

| Algorithm | Purpose            |
|-----------|--------------------|
| bcrypt    | Password hashing   |
| argon2    | Password hashing   |
| PBKDF2    | Password hashing   |

Never roll your own — use a well-tested library with sensible defaults.

### The check

```python
from passlib.hash import bcrypt

stored = bcrypt.hash("s3cret")
bcrypt.verify("s3cret", stored)   # True
bcrypt.verify("wrong", stored)    # False
```

The exercise in this module simulates the *shape* of this check with a simple function so you can practice the logic in the sandbox.

---

**Next up:** tokens — how the server remembers who you are."""
    ),
    L(
        id="backend-auth-tokens",
        course_id="backend-web-development",
        module_id="backend-auth",
        title="Tokens and Sessions",
        type="theory",
        order=2,
        content="""## Tokens and Sessions

After login, the server needs to recognize the user on subsequent requests. The two main approaches are **sessions** and **tokens**.

### Sessions

The server stores session state and gives the client an opaque session id:

```text
login → server stores {session_id: user_id} → client gets cookie
request with cookie → server looks up session → knows the user
```

- Simple, revocable (delete the session row).
- State lives **server-side** — needs a store (memory, Redis, DB).
- Cookies sent automatically by the browser.

### Tokens (JWT)

A **JWT** (JSON Web Token) is a self-contained, signed string the client holds:

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MiIsImV4cCI6MTY...9.signature
      header (algorithm)          payload (claims)          signature
```

The server verifies the signature; it does **not** need to look anything up.

### JWT structure

| Part      | Contents                                  |
|-----------|-------------------------------------------|
| Header    | Signing algorithm, type                   |
| Payload   | Claims: `sub` (user), `exp` (expiry), `iat` (issued) |
| Signature | Header + payload signed with a secret     |

### Key properties

- **Stateless** — no server-side store; any instance can verify.
- **Expiry** — `exp` claim limits lifetime; short-lived tokens are safer.
- **Signed, not encrypted** — the payload is readable base64. Never put secrets in it.

### Where tokens live

Clients send tokens via the `Authorization` header:

```text
Authorization: Bearer eyJhbGciOi...
```

### The trade-off

| Approach | Server state | Revocation | Complexity |
|----------|--------------|------------|------------|
| Session  | yes          | easy       | low        |
| JWT      | no           | harder     | medium     |

Sessions are easier to invalidate; tokens scale horizontally with no shared store. Many systems use short-lived tokens plus a **refresh token** stored securely.

---

**Next up:** authorization — deciding what a user may do."""
    ),
    L(
        id="backend-auth-authorization",
        course_id="backend-web-development",
        module_id="backend-auth",
        title="Authorization and Roles",
        type="theory",
        order=3,
        content="""## Authorization and Roles

**Authentication** answers *"who are you?"* — **authorization** answers *"what are you allowed to do?"* Confusing them is the source of many security bugs.

### Authentication vs authorization

```text
request → authenticate (who) → authorize (may they?) → act
```

- Authenticate: verify the token / session / credentials.
- Authorize: check roles, permissions, or ownership before acting.

### Roles (RBAC)

**Role-Based Access Control** groups permissions into roles:

| Role   | Permissions                        |
|--------|------------------------------------|
| guest  | read public content                |
| user   | create/update/delete own posts     |
| admin  | everything, plus manage users      |

```python
@app.delete("/api/posts/{post_id}")
def delete_post(post_id: int, user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(403, "admin only")
    ...
```

### Ownership checks

Roles are not enough — a user may edit their own post but not yours. Check **ownership** explicitly:

```python
post = post_repo.get(post_id)
if post.author_id != user.id and user.role != "admin":
    raise HTTPException(403)
```

### Permission scopes

Fine-grained systems use **scopes** (specific capabilities) instead of coarse roles:

```text
posts:read   posts:write   users:manage   billing:read
```

A token can carry its scopes, and each endpoint declares what it needs.

### The golden rules

- **Deny by default** — new code is locked down until proven otherwise.
- **Check in one place** — a shared dependency, not scattered `if`s.
- **Never trust the client** — authorization comes from the token/role, never from a request field like `"is_admin": true`.
- **Fail closed** — on error, deny access.

### Common vulnerability

An endpoint that checks authentication but forgets authorization — e.g. any logged-in user can read or delete anyone's resource. Always ask: *is this user allowed to touch this specific resource?*

---

**Next up:** input validation and security — hardening the request boundary."""
    ),
    L(
        id="backend-auth-input-validation",
        course_id="backend-web-development",
        module_id="backend-auth",
        title="Input Validation and Security",
        type="theory",
        order=4,
        content="""## Input Validation and Security

Most web vulnerabilities trace back to trusting untrusted input. Hardening the input boundary is the cheapest security you can buy.

### Injection

**SQL injection**: user input becomes SQL.

```python
# DANGEROUS
query = f"SELECT * FROM users WHERE name = '{name}'"
# name = "'; DROP TABLE users; --"

# SAFE — parameters
query = "SELECT * FROM users WHERE name = ?"
```

Always use **parameterized queries**; never build SQL by string concatenation.

### Command injection

Same idea, operating systems. Never pass user input into `os.system` or `shell=True` without strict validation.

### XSS

**Cross-Site Scripting**: user content is rendered as HTML, running scripts in other users' browsers. Escape output on the way to the page, and use auto-escaping templates.

### Validation as a security control

Validate on the **server**, always — the client can be bypassed in one curl command:

```python
def validate_email(email: str):
    if "@" not in email or len(email) > 254:
        raise ValueError("invalid email")
```

### Rate limiting

Abusers hammer endpoints. **Rate limiting** caps requests per client per window:

```text
max 60 requests / minute / IP (or / token)
```

The exercise in this module simulates the counting logic behind a rate limiter.

### Security checklist

- [ ] Parameterized SQL everywhere
- [ ] Server-side validation of every input
- [ ] Escape / auto-escape all rendered user content
- [ ] Hashed passwords, never plain text
- [ ] Short-lived tokens, secrets rotated
- [ ] Rate limiting on login and write endpoints
- [ ] Least-privilege roles with ownership checks

Security is not a feature you add at the end — it is a habit applied at every layer.

---

**Next up:** exercises — password checks, token expiry, and rate limiting."""
    ),
    L(
        id="backend-auth-exercise-password-check",
        course_id="backend-web-development",
        module_id="backend-auth",
        title="Exercise: Password Hash Check",
        type="exercise",
        order=5,
        content="""## Exercise: Password Hash Check

Write a function `solve(password, stored_hash)` that checks a password against a stored hash using a **simple hash function simulation**: the hash of a string is the sum of the ASCII codes of its characters (`sum(ord(c) for c in s)`).

Return `match` if `hash(password) == stored_hash`, otherwise `mismatch`.

### Sample

Input:

```text
secret
646
```

`ord('s')+ord('e')+ord('c')+ord('r')+ord('e')+ord('t')` is 646, so:

Output:

```text
match
```

### How your code runs

The runner calls `solve(password, stored_hash)` with a string and a number parsed from the two input lines. Compare the computed hash to `int(stored_hash)`.

### Starter code

```python
def solve(password, stored_hash):
    if hash_string(password) == int(stored_hash):
        return "match"
    return "mismatch"


def hash_string(s):
    return sum(ord(c) for c in s)


def main():
    import sys
    raw = sys.stdin.read().strip()
    if not raw:
        return
    lines = raw.split("\\n")
    print(solve(lines[0], lines[1]))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(password, stored_hash):
    if hash_string(password) == int(stored_hash):
        return "match"
    return "mismatch"


def hash_string(s):
    return sum(ord(c) for c in s)


def main():
    import sys
    raw = sys.stdin.read().strip()
    if not raw:
        return
    lines = raw.split("\\n")
    print(solve(lines[0], lines[1]))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "secret\n646", "expected_output": "match", "description": "Correct password"},
            {"input": "secret\n000", "expected_output": "mismatch", "description": "Wrong hash"},
            {"input": "admin\n435", "expected_output": "mismatch", "description": "Hash for another password"},
            {"input": "admin\n521", "expected_output": "match", "description": "admin hashes to 521"},
        ],
    ),
    L(
        id="backend-auth-exercise-token-expiry",
        course_id="backend-web-development",
        module_id="backend-auth",
        title="Exercise: Token Expiry Check",
        type="exercise",
        order=6,
        content="""## Exercise: Token Expiry Check

Write a function `solve(issued, ttl, now)` that decides whether a token is still valid, using **numeric timestamps**.

A token issued at `issued` with a lifetime of `ttl` seconds is valid while `now <= issued + ttl`. Return `valid` or `expired`.

### Sample

Input:

```text
1000
500
1400
```

`1000 + 500 = 1500`, and `now` is `1400`, so the token is still live:

Output:

```text
valid
```

### How your code runs

The runner calls `solve(issued, ttl, now)` with three integers parsed from the three input lines. Return the status string.

### Starter code

```python
def solve(issued, ttl, now):
    if now <= issued + ttl:
        return "valid"
    return "expired"


def main():
    import sys
    raw = sys.stdin.read().strip()
    if not raw:
        return
    issued, ttl, now = (int(ln) for ln in raw.split("\\n"))
    print(solve(issued, ttl, now))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(issued, ttl, now):
    if now <= issued + ttl:
        return "valid"
    return "expired"


def main():
    import sys
    raw = sys.stdin.read().strip()
    if not raw:
        return
    issued, ttl, now = (int(ln) for ln in raw.split("\\n"))
    print(solve(issued, ttl, now))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "1000\n500\n1400", "expected_output": "valid", "description": "Still within lifetime"},
            {"input": "1000\n500\n1500", "expected_output": "valid", "description": "Exactly at expiry is valid"},
            {"input": "1000\n500\n1501", "expected_output": "expired", "description": "One second past expiry"},
            {"input": "0\n60\n59", "expected_output": "valid", "description": "Short-lived token"},
        ],
    ),
    L(
        id="backend-auth-exercise-rate-limit",
        course_id="backend-web-development",
        module_id="backend-auth",
        title="Exercise: Rate-Limit Counter",
        type="exercise",
        order=7,
        content="""## Exercise: Rate-Limit Counter

Write a function `solve(timestamps, window, limit)` that returns the number of requests **allowed** under a sliding-window rate limit.

Requests arrive at the given integer timestamps (in order). A request is allowed if fewer than `limit` requests arrived in the previous `window` time units. Allowed requests count toward the window.

### Sample

Input:

```text
[1, 2, 3, 4]
3
2
```

Walk through: `1` allowed, `2` allowed (two in window), `3` blocked (already two in the last 3 units), `4` allowed (by then `1` has fallen out). So:

Output:

```text
3
```

### How your code runs

The runner calls `solve(timestamps, window, limit)` with a JSON list and two integers parsed from the three input lines. Return the count.

### Starter code

```python
def solve(timestamps, window, limit):
    recent = []
    allowed = 0
    for t in timestamps:
        recent = [x for x in recent if x > t - window]
        if len(recent) < limit:
            recent.append(t)
            allowed += 1
    return allowed


def main():
    import sys, json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    lines = raw.split("\\n")
    timestamps = json.loads(lines[0])
    window = int(lines[1])
    limit = int(lines[2])
    print(solve(timestamps, window, limit))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(timestamps, window, limit):
    recent = []
    allowed = 0
    for t in timestamps:
        recent = [x for x in recent if x > t - window]
        if len(recent) < limit:
            recent.append(t)
            allowed += 1
    return allowed


def main():
    import sys, json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    lines = raw.split("\\n")
    timestamps = json.loads(lines[0])
    window = int(lines[1])
    limit = int(lines[2])
    print(solve(timestamps, window, limit))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "[1, 2, 3, 4]\n3\n2", "expected_output": "3", "description": "Sliding window allows 3 of 4"},
            {"input": "[1, 2, 3]\n10\n2", "expected_output": "2", "description": "All within one window"},
            {"input": "[10, 20, 30]\n5\n3", "expected_output": "3", "description": "Sparse requests all pass"},
            {"input": "[]\n10\n5", "expected_output": "0", "description": "No requests"},
        ],
    ),
    # ── Module 5: Backend Project ──────────────────────────────────────
    L(
        id="backend-project-architecture",
        course_id="backend-web-development",
        module_id="backend-project",
        title="Designing the API",
        type="theory",
        order=1,
        content="""## Designing the API

The project builds a complete authenticated API — a todo service. Start by designing the surface before writing code.

### The resource

Todos belong to a user. Keep them nested to make ownership explicit:

```text
GET    /api/todos          list my todos
POST   /api/todos          create a todo
GET    /api/todos/{id}     read one
PATCH  /api/todos/{id}     update
DELETE /api/todos/{id}     delete
```

### The models

```python
class TodoCreate(BaseModel):        # what clients send
    title: str = Field(..., min_length=1, max_length=200)

class TodoOut(BaseModel):           # what clients receive
    id: int
    title: str
    done: bool = False
    owner_id: int
```

### The layering

```text
routes (HTTP) → services (logic) → repositories (data)
```

| Layer        | Responsibility                    |
|--------------|-----------------------------------|
| Routes       | Parse/validate requests, serialize responses |
| Services     | Business rules, ownership checks  |
| Repositories | Database access                  |

### The endpoints by method

| Method   | Path            | Success | Failure                     |
|----------|-----------------|---------|-----------------------------|
| `GET`    | `/api/todos`    | 200     | 401 (no auth)               |
| `POST`   | `/api/todos`    | 201     | 422 (bad body)              |
| `GET`    | `/api/todos/{id}` | 200   | 404 (not yours or missing)  |
| `PATCH`  | `/api/todos/{id}` | 200  | 404, 422                    |
| `DELETE` | `/api/todos/{id}` | 204  | 404                         |

### Design decisions

- **Ownership**: every todo has `owner_id`; handlers only touch the current user's rows.
- **Auth**: `POST /api/auth/register` and `/api/auth/login` return a token.
- **Validation**: schemas reject bad bodies at the boundary.
- **Errors**: consistent JSON shape, right status codes.

Write this plan down, then implement it layer by layer — the module's exercises build the pieces.

---

**Next up:** building the auth and todo endpoints."""
    ),
    L(
        id="backend-project-auth-flow",
        course_id="backend-web-development",
        module_id="backend-project",
        title="The Authentication Flow",
        type="theory",
        order=2,
        content="""## The Authentication Flow

Every protected endpoint needs to know *who is calling*. This module walks the full flow from signup to protected request.

### 1. Register

```python
@app.post("/api/auth/register")
def register(data: RegisterRequest):
    if user_repo.get_by_email(data.email):
        raise HTTPException(409, "email already registered")
    user = user_repo.create(
        email=data.email,
        password_hash=hash_password(data.password),
    )
    return {"token": create_token(user.id)}
```

Never store the raw password — hash it at the boundary.

### 2. Login

```python
@app.post("/api/auth/login")
def login(data: LoginRequest):
    user = user_repo.get_by_email(data.email)
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "invalid credentials")
    return {"token": create_token(user["id"])}
```

Same error for "no such user" and "wrong password" — don't leak which one failed.

### 3. The dependency

One shared dependency authenticates every protected route:

```python
def get_current_user(authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ")
    payload = decode_token(token)             # raises on bad/expired
    return user_repo.get(payload["sub"])

@app.get("/api/todos")
def list_todos(user=Depends(get_current_user)):
    return todo_repo.list_for_user(user["id"])
```

### 4. Token lifetime

```python
def create_token(user_id):
    return jwt.encode(
        {"sub": str(user_id), "iat": now(), "exp": now() + 3600},
        SECRET_KEY,
    )
```

Short `exp` plus secure storage of the secret. Rotate the secret on suspicion of compromise.

### The flow in one picture

```text
register/login → token
request → Authorization: Bearer <token>
dependency decodes + loads user → handler acts as that user
```

Every security rule from module 4 lands here: hashed passwords, short-lived signed tokens, ownership checks on every todo.

---

**Next up:** logging and idempotency — the operational details."""
    ),
    L(
        id="backend-project-logging",
        course_id="backend-web-development",
        module_id="backend-project",
        title="Logging and Idempotency",
        type="theory",
        order=3,
        content="""## Logging and Idempotency

Two operational details separate a prototype from a dependable service: **logging** and **idempotency**.

### Structured logging

Every request should leave a trace you can search. A structured log line carries fields, not prose:

```text
method=GET path=/api/todos status=200 duration_ms=12 user_id=42
method=POST path=/api/todos status=201 duration_ms=5 user_id=42
```

Use a logging library and emit JSON or key=value lines. What to record:

| Field         | Why                                    |
|---------------|----------------------------------------|
| method, path  | What was called                        |
| status        | Outcome                                |
| duration_ms   | Performance signal                     |
| user_id       | Traceability (never log passwords/tokens) |
| request_id    | Correlate a single request across logs |

Never log secrets, full tokens, or raw password data — a common and embarrassing leak.

### Idempotency

A retried request should not duplicate work. **Idempotency keys** let a client mark a request so repeats return the original result:

```text
POST /api/payments
Idempotency-Key: order-123
```

The server keeps processed keys:

```python
def apply_idempotent(key, operation):
    if key in processed_keys:
        return stored_result[key]          # replay, don't re-run
    result = operation()
    processed_keys[key] = result
    return result
```

### Where it matters

- Payment creation, order placement, any "create" the client may retry.
- Webhooks and background jobs that can be delivered more than once.

### The mental model

Logging tells you *what happened*; idempotency keys make retries safe. Together they give you the confidence to run a service you cannot watch by hand.

---

**Next up:** testing and deploying the API."""
    ),
    L(
        id="backend-project-testing-deploy",
        course_id="backend-web-development",
        module_id="backend-project",
        title="Testing and Deployment",
        type="theory",
        order=4,
        content="""## Testing and Deployment

An API is only "done" when it is tested and can be shipped. Both follow repeatable habits.

### The test pyramid

```text
     /  few, slow, end-to-end   \
    /  some integration tests     \
   /     many fast unit tests        \
```

- **Unit tests** — one function, no I/O: validation, hashing, pagination math.
- **Integration tests** — endpoint + repository against a real (or test) database.
- **E2E tests** — full user flows through the running app.

### Testing the API layer

```python
def test_create_todo_requires_auth(client):
    res = client.post("/api/todos", json={"title": "x"})
    assert res.status_code == 401

def test_create_todo(client, auth_token):
    res = client.post("/api/todos", json={"title": "learn backend"},
                      headers={"Authorization": f"Bearer {auth_token}"})
    assert res.status_code == 201
    assert res.json()["title"] == "learn backend"
```

### What to test

- Every happy path and its main failure (404, 422, 401, 403).
- Validation rejects bad input.
- Ownership: user A cannot touch user B's todo.
- The repository: CRUD and edge cases, with the storage swapped for a fake.

### Deployment basics

| Concern       | Practice                                    |
|---------------|---------------------------------------------|
| Config        | Secrets via environment variables, not code |
| Build         | Reproducible image (Dockerfile)             |
| Health        | `GET /health` endpoint for the orchestrator |
| Logs          | Structured, shipped to a log store          |
| Rollbacks     | Keep previous image; migrate schema forward  |

### The loop

1. Green tests locally.
2. Build the image, run migration.
3. Deploy, watch health and logs.
4. Roll back on errors.

A well-tested, deployable API is the entire point of the module — the exercises hand you the pure logic pieces, and the design practice stitches them together.

---

**Next up:** exercises — the log formatter, idempotency, and the design capstone."""
    ),
    L(
        id="backend-project-exercise-logger",
        course_id="backend-web-development",
        module_id="backend-project",
        title="Exercise: Request Log Formatter",
        type="exercise",
        order=5,
        content="""## Exercise: Request Log Formatter

Write a function `solve(request)` that formats a request into a **structured log line**.

The request is a dict with `method`, `path`, `status`, and `duration_ms`. Return the line as `method=... path=... status=... duration_ms=...`.

### Sample

Input:

```text
{"method": "GET", "path": "/api/todos", "status": 200, "duration_ms": 12}
```

Output:

```text
method=GET path=/api/todos status=200 duration_ms=12
```

### How your code runs

The runner calls `solve(request)` with one dictionary parsed from the JSON input. Build the string with an f-string.

### Starter code

```python
def solve(request):
    return (
        f"method={request['method']} path={request['path']} "
        f"status={request['status']} duration_ms={request['duration_ms']}"
    )


def main():
    import sys, json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    print(solve(json.loads(raw)))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(request):
    return (
        f"method={request['method']} path={request['path']} "
        f"status={request['status']} duration_ms={request['duration_ms']}"
    )


def main():
    import sys, json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    print(solve(json.loads(raw)))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '{"method": "GET", "path": "/api/todos", "status": 200, "duration_ms": 12}', "expected_output": "method=GET path=/api/todos status=200 duration_ms=12", "description": "Successful list"},
            {"input": '{"method": "POST", "path": "/api/todos", "status": 201, "duration_ms": 5}', "expected_output": "method=POST path=/api/todos status=201 duration_ms=5", "description": "Created"},
            {"input": '{"method": "GET", "path": "/api/todos/42", "status": 404, "duration_ms": 1}', "expected_output": "method=GET path=/api/todos/42 status=404 duration_ms=1", "description": "Not found"},
        ],
    ),
    L(
        id="backend-project-exercise-idempotency",
        course_id="backend-web-development",
        module_id="backend-project",
        title="Exercise: Idempotency Key Check",
        type="exercise",
        order=6,
        content="""## Exercise: Idempotency Key Check

Write a function `solve(processed, key)` that decides whether a request with an **idempotency key** should run or be replayed.

- If `key` is in the list of already-processed keys, return `replay` (do not run again).
- Otherwise return `process`.

### Sample

Input:

```text
["order-1", "order-2"]
order-2
```

Output:

```text
replay
```

### How your code runs

The runner calls `solve(processed, key)` with a JSON list and a plain string parsed from the two input lines. Use `in` for the membership test.

### Starter code

```python
def solve(processed, key):
    if key in processed:
        return "replay"
    return "process"


def main():
    import sys, json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    lines = raw.split("\\n")
    processed = json.loads(lines[0])
    key = lines[1]
    print(solve(processed, key))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(processed, key):
    if key in processed:
        return "replay"
    return "process"


def main():
    import sys, json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    lines = raw.split("\\n")
    processed = json.loads(lines[0])
    key = lines[1]
    print(solve(processed, key))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '["order-1", "order-2"]\norder-2', "expected_output": "replay", "description": "Already processed"},
            {"input": '["order-1", "order-2"]\norder-3', "expected_output": "process", "description": "New key"},
            {"input": '[]\norder-1', "expected_output": "process", "description": "First request"},
        ],
    ),
    L(
        id="backend-project-exercise-design",
        course_id="backend-web-development",
        module_id="backend-project",
        title="Practice: Design the Full API",
        type="practice",
        order=7,
        content="""## Practice: Design the Full API

This is a **design capstone** — think it through and write your answer. There are no automated tests.

### The brief

Design a complete authenticated todo API that a frontend (like the one from the JavaScript course) could consume. Use the modules of this course as your checklist.

### Write down

1. **Endpoints** — the full table: method, path, purpose, success status, failure statuses.
2. **Models** — `TodoCreate`, `TodoOut`, `UserCreate`, `LoginRequest` and their required fields.
3. **Layers** — which routes, services, and repositories exist.
4. **Auth** — register/login flow, token shape, expiry, how protected routes resolve the user.
5. **Persistence** — tables and constraints; how ownership is stored.
6. **Security** — password hashing, input validation, rate limiting, ownership checks.
7. **Operations** — log format, idempotency keys on `POST /api/todos`.

### A starting sketch

```text
Tables:
  users (id, email UNIQUE, password_hash, created_at)
  todos (id, title, done, owner_id → users.id)

Endpoints:
  POST /api/auth/register    201 / 409 / 422
  POST /api/auth/login       200 / 401
  GET  /api/todos            200 / 401
  POST /api/todos            201 / 401 / 422
  GET  /api/todos/{id}       200 / 404 / 401
  PATCH /api/todos/{id}      200 / 404 / 422
  DELETE /api/todos/{id}     204 / 404

Auth: JWT with exp=3600s; Authorization: Bearer <token>.
```

### Check yourself

- Can a user never see another user's todo? (ownership in every handler)
- Is every error status chosen deliberately?
- Is there a layer for data access, business rules, and HTTP?
- What happens if `POST /api/todos` is retried?

### When you finish

You have designed a production-shaped API. Implementing it is the natural next step — and the exercises in this course already cover the trickiest pure logic: validation, pagination, hashing, expiry, rate limiting, logging, and idempotency.

---

**Next up:** the next course — putting a frontend in front of this API."""
    ),
]
