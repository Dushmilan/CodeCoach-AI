"""Cybersecurity Fundamentals — curriculum content module.

Every topic is taught defensively: we explain how vulnerabilities work only to
the depth needed to prevent or fix them, and all exercises are safe, pure-Python
logic running on toy data. No offensive tooling, no real target testing.
"""

COURSE = {
    "id": "cybersecurity-fundamentals",
    "title": "Cybersecurity Fundamentals",
    "description": (
        "Build a security mindset from the ground up: security foundations, web "
        "vulnerabilities and how to prevent them, secure coding habits, networks "
        "and access control, and a defensive project where you find and fix "
        "vulnerabilities in a safe Python sandbox."
    ),
    "language": "python",
    "icon": "shield",
    "order": 14,
}

MODULES = [
    {
        "id": "cyber-foundations",
        "course_id": "cybersecurity-fundamentals",
        "title": "Security Foundations",
        "description": "Threats, assets, attack surface, least privilege, and the CIA triad — the vocabulary and mindset of security.",
        "order": 1,
    },
    {
        "id": "cyber-web",
        "course_id": "cybersecurity-fundamentals",
        "title": "Web Security",
        "description": "Injection, XSS, CSRF, and authentication weaknesses — understood conceptually so you can detect and prevent them.",
        "order": 2,
    },
    {
        "id": "cyber-secure-code",
        "course_id": "cybersecurity-fundamentals",
        "title": "Secure Programming",
        "description": "Input validation, output encoding, secrets handling, and dependency risk — the habits that keep code safe by default.",
        "order": 3,
    },
    {
        "id": "cyber-networks",
        "course_id": "cybersecurity-fundamentals",
        "title": "Networks and Access Control",
        "description": "HTTP and TLS, sessions and tokens, permissions and role-based access, plus defensive network fundamentals.",
        "order": 4,
    },
    {
        "id": "cyber-project",
        "course_id": "cybersecurity-fundamentals",
        "title": "Secure Application Project",
        "description": "Find and fix vulnerabilities in a safe code sandbox: redaction, escaping, and access checks in pure Python logic.",
        "order": 5,
    },
]

_PY = "python"


def L(**kw):
    kw.setdefault("language", _PY)
    return kw


LESSONS = [
    # ── Module 1: Security Foundations ──────────────────────────────────
    L(
        id="cyber-foundations-threats",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-foundations",
        title="Threats and Assets",
        type="theory",
        order=1,
        content="""## Threats and Assets

Security starts with two questions: **what are you protecting?** and **who could harm it?**

### Assets

An **asset** is anything of value that needs protecting. In software, assets are usually:

| Asset            | Example                                   |
|------------------|-------------------------------------------|
| Data             | User passwords, emails, payment records   |
| Systems          | Web servers, databases, APIs              |
| Reputation       | The trust users place in your service     |
| Code             | Your source code and secrets              |

### Threats

A **threat** is anything that could harm an asset: a malicious actor, a careless employee, a bug, or even a natural disaster. Common categories:

- **Malware** — software designed to harm or steal.
- **Phishing** — tricking users into revealing credentials.
- **Injection** — inserting malicious input that the app executes.
- **Insider risk** — an employee with too much access.
- **Social engineering** — manipulating people instead of systems.

### Risk

**Risk** is the chance that a threat harms an asset. A useful formula:

```text
risk = likelihood × impact
```

A high-impact asset (customer data) with a likely threat (unvalidated login form) is high risk. Security work is about reducing either the likelihood (add protections) or the impact (encrypt, segment, back up).

### Threat modeling mindset

For every feature, ask:

1. What assets does it touch?
2. Who or what could abuse it?
3. What happens if they succeed?
4. What is the cheapest control that meaningfully reduces that risk?

You do not need a lab or special tools — a clear head and these questions are the starting point.

---

**Next up:** attack surface and the principle of least privilege."""
    ),
    L(
        id="cyber-foundations-attack-surface",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-foundations",
        title="Attack Surface and Least Privilege",
        type="theory",
        order=2,
        content="""## Attack Surface and Least Privilege

Two principles shape nearly every defensive decision.

### Attack surface

The **attack surface** is every place an attacker can interact with your system: inputs, endpoints, files, environment, anything reachable.

```python
# A small attack surface: one narrow entry point
def get_price(product_id):
    ...
```

```python
# A larger attack surface: anything goes
def handle_request(path, method, body, headers):
    ...
```

Each new input, route, library, or feature adds surface area. You cannot protect what you do not know exists, so **map your surface** and shrink it: fewer endpoints, strict schemas, and minimal exposure.

### Least privilege

**Least privilege** means every user and every component gets the **minimum access needed** to do its job — no more.

```python
ROLES = {
    "viewer": ["read"],
    "editor": ["read", "write"],
    "admin":  ["read", "write", "delete"],
}
```

A `viewer` has no business holding `delete` rights. If an attacker compromises a least-privileged account, they inherit only that account's limited power.

### Apply least privilege broadly

- **Users** — role-based access with the smallest capable role.
- **Processes** — a web worker should not run as root.
- **Secrets** — a CI job only receives the keys it needs.
- **Files** — readable only by the process that must read them.

### The compounding effect

A small surface *and* least privilege multiply: the attacker must find a way in (surface) and, once in, still cannot reach much (privilege). Neither alone is enough; together they make compromise expensive.

---

**Next up:** the CIA triad — confidentiality, integrity, availability."""
    ),
    L(
        id="cyber-foundations-cia",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-foundations",
        title="The CIA Triad",
        type="theory",
        order=3,
        content="""## The CIA Triad

**CIA** is the classic shorthand for the three core security goals: **Confidentiality**, **Integrity**, and **Availability**.

### Confidentiality — only the right people can see it

Keep data private from everyone who lacks permission. Controls: encryption, access control, redaction of secrets in logs.

```python
def redact(line):
    if "api_key=" in line:
        line = line.split("api_key=")[0] + "api_key=[REDACTED]"
    return line
```

### Integrity — data is accurate and untampered

Protect data from unauthorized modification. Controls: hashing, signatures, input validation, immutable logs.

### Availability — the system keeps working

Authorized users must be able to use the service. Controls: redundancy, backups, rate limiting, monitoring.

### Trade-offs

The three goals can conflict. Aggressive rate limiting protects **availability** of shared resources but slightly hurts **availability** of individual users; heavy encryption protects **confidentiality** but can hurt **performance**. Security decisions are about balancing the triad against cost and usability.

### Mapping controls to goals

| Control                | CIA goal addressed          |
|------------------------|-----------------------------|
| Encryption at rest     | Confidentiality             |
| Input validation       | Integrity (and more)        |
| Backups                | Availability                |
| Access control         | Confidentiality             |
| Rate limiting          | Availability                |
| Logging + monitoring   | All three (detection)       |

### Ask which goal matters most

A password vault prioritizes **confidentiality**. A booking system prioritizes **availability**. Naming the priority makes design choices explicit and defensible.

---

**Next up:** defense in depth and thinking about risk."""
    ),
    L(
        id="cyber-foundations-defense",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-foundations",
        title="Defense in Depth and Risk",
        type="theory",
        order=4,
        content="""## Defense in Depth and Risk

No single control is perfect. **Defense in depth** layers independent protections so that if one fails, others still stand.

### Layered defense

Imagine protecting a building: locked doors, an alarm, cameras, and a guard. If the doors are bypassed, the alarm still triggers. Software works the same way:

```text
input → validation → encoding → permissions → audit logs
```

A malicious string is stopped by validation; if it slips through, encoding neutralizes it; if it reaches a handler, permissions block it; and whatever happens, the audit log records it.

### Layers in a web app

1. **Network** — TLS encryption in transit.
2. **Application** — input validation, output encoding, CSRF tokens.
3. **Data** — encryption at rest, least-privilege database accounts.
4. **Detection** — logs, alerts, audit trails.

### Secure defaults and fail-closed

Configure systems to the **safe setting by default**, and make failures deny rather than allow:

```python
def is_allowed(role, action):
    permissions = ROLES.get(role, set())     # unknown role → no rights
    return action in permissions
```

An unknown role gets nothing (fail-closed) instead of everything.

### Continuous risk management

Security is a process, not a one-time fix:

1. Identify assets and threats.
2. Assess likelihood and impact.
3. Apply layered controls.
4. Test the controls.
5. Monitor and repeat.

### Your role as a developer

Most vulnerabilities are not exotic — they are missing validation, unencoded output, and over-broad permissions. Writing code with secure defaults *by default* is the single biggest lever you have.

---

**Next up:** your first defensive exercises — password strength, secret detection, and input length checks."""
    ),
    L(
        id="cyber-foundations-exercise-password",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-foundations",
        title="Exercise: Password Strength Checker",
        type="exercise",
        order=5,
        content="""## Exercise: Password Strength Checker

Write `solve(password)` that returns a **strength score** from 0 to 5. Add 1 for each rule the password satisfies:

1. At least 8 characters long.
2. Contains an uppercase letter.
3. Contains a lowercase letter.
4. Contains a digit.
5. Contains a special character (anything that is not a letter or digit).

### Sample

Input (one line):

```text
Passw0rd!
```

Output:

```text
5
```

### How your code runs

The harness passes the password as a single string. Your function treats it as text and returns the score.

### Starter code

```python
def solve(password):
    password = str(password)
    score = 0
    if len(password) >= 8:
        score += 1
    if any(ch.isupper() for ch in password):
        score += 1
    if any(ch.islower() for ch in password):
        score += 1
    if any(ch.isdigit() for ch in password):
        score += 1
    if any(not ch.isalnum() for ch in password):
        score += 1
    return score

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
        starter_code='''def solve(password):
    password = str(password)
    score = 0
    if len(password) >= 8:
        score += 1
    if any(ch.isupper() for ch in password):
        score += 1
    if any(ch.islower() for ch in password):
        score += 1
    if any(ch.isdigit() for ch in password):
        score += 1
    if any(not ch.isalnum() for ch in password):
        score += 1
    return score

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
            {"input": "Passw0rd!", "expected_output": "5", "description": "Meets every rule"},
            {"input": "abc", "expected_output": "1", "description": "Only a lowercase letter"},
            {"input": "password", "expected_output": "2", "description": "Length and lowercase"},
            {"input": "12345678", "expected_output": "2", "description": "Length and digits"},
            {"input": "aB1!", "expected_output": "4", "description": "All except length"},
        ],
    ),
    L(
        id="cyber-foundations-exercise-secrets",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-foundations",
        title="Exercise: Secret Detection in Logs",
        type="exercise",
        order=6,
        content="""## Exercise: Secret Detection in Logs

Write `solve(line)` that returns `True` when a log line contains a **secret pattern** and `False` otherwise. Detect (case-sensitive and case-insensitive where noted):

- `sk-` followed by content (an OpenAI-style key),
- `AKIA` (an AWS-style access key),
- `ghp_` (a GitHub token prefix),
- `api_key=` or `API_KEY=` (a parameterized key).

### Sample

Input (one line):

```text
token=sk-abcdefghijklmnop action=ok
```

Output:

```text
true
```

### How your code runs

The harness passes the log line as a single string. Search the text for the patterns and return a boolean (printed as `true`/`false`).

### Starter code

```python
def solve(line):
    text = str(line).lower()
    patterns = ["sk-", "akia", "ghp_", "api_key="]
    return any(pattern in text for pattern in patterns)

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
        starter_code='''def solve(line):
    text = str(line).lower()
    patterns = ["sk-", "akia", "ghp_", "api_key="]
    return any(pattern in text for pattern in patterns)

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
            {"input": "token=sk-abcdefghijklmnop action=ok", "expected_output": "true", "description": "sk- key present"},
            {"input": "gpg key AKIAIOSFODNN7EXAMPLE stored", "expected_output": "true", "description": "AWS-style key"},
            {"input": "INFO: completed in 120ms", "expected_output": "false", "description": "Benign log line"},
            {"input": "api_key=abcd1234 ready", "expected_output": "true", "description": "api_key parameter"},
            {"input": "no secrets here", "expected_output": "false", "description": "Clean line"},
        ],
    ),
    L(
        id="cyber-foundations-exercise-length",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-foundations",
        title="Exercise: Input Length Validation",
        type="exercise",
        order=7,
        content="""## Exercise: Input Length Validation

Write `solve(text, max_len)` that returns `True` when `len(text) <= max_len` and `False` otherwise. Length limits are a simple first line of defense against oversized inputs that can exhaust memory or overflow buffers.

### Sample

Input:

```text
"hello"
10
```

Output:

```text
true
```

### How your code runs

The harness passes the text (a quoted string) on line 1 and the maximum length on line 2. Compare lengths and return a boolean.

### Starter code

```python
def solve(text, max_len):
    return len(str(text)) <= max_len

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    text = lines[0].strip().strip('"')
    max_len = int(lines[1].strip())
    print(str(solve(text, max_len)).lower())

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(text, max_len):
    return len(str(text)) <= max_len

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    text = lines[0].strip().strip('"')
    max_len = int(lines[1].strip())
    print(str(solve(text, max_len)).lower())

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '"hello"\n10', "expected_output": "true", "description": "Well under limit"},
            {"input": '"hello world"\n5', "expected_output": "false", "description": "Over the limit"},
            {"input": '"ok"\n2', "expected_output": "true", "description": "Exactly at the limit"},
            {"input": '"way too long text"\n3', "expected_output": "false", "description": "Far over the limit"},
        ],
    ),
    # ── Module 2: Web Security ──────────────────────────────────────────
    L(
        id="cyber-web-injection",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-web",
        title="Injection Attacks and Prevention",
        type="theory",
        order=1,
        content="""## Injection Attacks and Prevention

**Injection** happens when untrusted input is interpreted as code. The most famous kind is **SQL injection**, where user text becomes part of a database query.

### How it happens (conceptually)

A query built by string concatenation is dangerous:

```python
query = "SELECT * FROM users WHERE name = '" + user_input + "'"
```

If `user_input` is `Robert'); DROP TABLE users;--`, the query now contains attacker-controlled SQL. The input was treated as **code**, not as **data**.

### The fix: parameterized queries

Never build SQL by concatenation. Parameterized queries keep data separate from code:

```python
# Safe: the driver treats user_input as a value, never as SQL
cursor.execute("SELECT * FROM users WHERE name = %s", (user_input,))
```

The placeholder `%s` is filled in by the database layer, which escapes the value safely.

### Prevention checklist

| Control                    | What it stops                          |
|----------------------------|----------------------------------------|
| Parameterized queries      | SQL injection                          |
| Output encoding            | HTML/JavaScript injection (XSS)        |
| Input validation           | Shell, path, and LDAP injection        |
| Least privilege on DB users| Damage from a successful injection     |

### A defensive detection exercise

Because concatenating user data into a query is so common in legacy code, one of this module's exercises asks you to **detect** risky query strings in toy data — checking whether a query contains SQL keywords *and* string concatenation. This is purely defensive: you are reviewing code, not attacking anything.

### Always assume input is hostile

Treat every request, header, file, and parameter as untrusted until validated. That habit prevents injection, path traversal, and a host of other classes.

---

**Next up:** cross-site scripting (XSS) and output encoding."""
    ),
    L(
        id="cyber-web-xss",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-web",
        title="XSS and Output Encoding",
        type="theory",
        order=2,
        content="""## XSS and Output Encoding

**Cross-site scripting (XSS)** injects scripts into pages other users view. A safe-looking comment form becomes a trap when it echoes attacker text into HTML without escaping.

### The attack, conceptually

```python
comment = '<script>steal_cookie()</script>'

# Unsafe: rendered into the page as HTML
page = "<p>" + comment + "</p>"
```

The browser interprets the text as markup and runs the script inside it.

### The defense: encode on output

Treat user data as **data**, never as HTML. Escape the characters that have special meaning in markup:

| Character | Encoded       |
|-----------|---------------|
| `<`       | `&lt;`        |
| `>`       | `&gt;`        |
| `&`       | `&amp;`       |
| `"`       | `&quot;`      |
| `'`       | `&#39;`       |

```python
def escape(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))
```

Escaped input renders as visible text instead of executing.

### Kinds of XSS

- **Stored** — the payload is saved on the server and shown to many users (worst case).
- **Reflected** — the payload is echoed back immediately in a response.
- **DOM-based** — the script manipulates the page in the browser without server involvement.

### Prevention checklist

- Encode output at every sink (HTML, attributes, URLs, JavaScript strings).
- Prefer safe DOM APIs like `textContent` over `innerHTML`.
- Set a strict `Content-Security-Policy` header.
- Validate input length and characters.

The exercises in this module detect script payloads in text and strip `<script>` blocks with plain string operations — safe review tasks on toy data.

---

**Next up:** CSRF and authentication weaknesses."""
    ),
    L(
        id="cyber-web-csrf",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-web",
        title="CSRF and Authentication Weaknesses",
        type="theory",
        order=3,
        content="""## CSRF and Authentication Weaknesses

Two more web weaknesses complete the picture.

### Cross-Site Request Forgery (CSRF)

**CSRF** tricks a logged-in user's browser into performing an action they did not intend. The site trusts the session cookie; the attacker crafts a request and the browser sends it with those cookies.

Conceptually: you are logged into a banking app; you visit a malicious page; the page submits a "transfer money" form using your browser's session, and the server cannot tell the request was not yours.

### CSRF defenses

- **CSRF tokens** — a per-session random value the server embeds in forms and checks on every state-changing request.
- **SameSite cookies** — restrict when cookies are sent on cross-site requests.
- **Verify the request origin** — compare the `Origin`/`Referer` header.

### Authentication weaknesses

Authentication answers *who are you?* Common weaknesses:

| Weakness                      | Fix                                       |
|-------------------------------|-------------------------------------------|
| Weak password policies        | Length + complexity requirements          |
| Storing plaintext passwords   | Hash with a slow, salted algorithm        |
| No rate limiting on logins    | Lockout and rate limits                   |
| Sessions that never expire    | Expiry, rotation, revocation              |
| No second factor              | MFA where risk warrants it                |

### Session hygiene

A session must have a finite life, be tied to a secret token, and be invalidated on logout and password change. Token expiry checks (later in this course) implement exactly this idea on toy data.

### The defensive frame

You do not need to *perform* these attacks to understand them. Your job is to build the defenses: validate, encode, tokenize, expire, and log.

---

**Next up:** the defensive detection mindset for reviewing code."""
    ),
    L(
        id="cyber-web-detection-mindset",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-web",
        title="The Defensive Detection Mindset",
        type="theory",
        order=4,
        content="""## The Defensive Detection Mindset

Security reviewers do not attack systems — they **inspect code and data for dangerous patterns** and fix them. This module's exercises teach detection with safe, pure-logic checks on toy inputs.

### What "detection" means here

Detection is pattern matching on strings and structures, nothing more:

- Does this query string concatenate user input into SQL?
- Does this text contain script markup?
- Does this HTML contain `<script>` blocks?

You are reading, classifying, and cleaning — never executing, probing, or targeting anything real.

### A review checklist

1. **Input** — is every external value validated for type, length, and allowed characters?
2. **Query** — is SQL built with parameters, never concatenation?
3. **Output** — is user data encoded before being rendered?
4. **Secrets** — do logs or code contain keys, tokens, or passwords?
5. **Access** — does every user have only the permissions they need?

### Detection is only the first step

Finding a problem is not the end. The fix matters more:

```python
# Before: risky concatenation
query = "SELECT * FROM users WHERE name = '" + name + "'"

# After: treated as data
cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
```

### Safety rules for this course

- All exercises run on **toy data you supply** — never real systems.
- Every task is defensive: detect, validate, sanitize, redact.
- If you are unsure whether something is safe to try, treat it as unsafe and do not try it.

---

**Next up:** exercises — detecting SQL concatenation, XSS payloads, and stripping script tags."""
    ),
    L(
        id="cyber-web-exercise-sql-detection",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-web",
        title="Exercise: Detect Risky SQL Construction",
        type="exercise",
        order=5,
        content="""## Exercise: Detect Risky SQL Construction

Write `solve(query)` that returns `True` when a query string looks **risky to build by concatenation** and `False` otherwise. A query is risky when it contains SQL keywords (`select`, `insert`, `update`, `delete`) **and** string concatenation (`+`), **or** classic injection markers such as `or 1=1`, `--`, or `union select`.

### Sample

Input (one line):

```text
SELECT * FROM users WHERE name = '" + user + "'
```

Output:

```text
true
```

### How your code runs

The harness passes the query as a single string. Lowercase it, then apply the pattern checks. This is a code-review helper — you are classifying toy strings.

### Starter code

```python
def solve(query):
    q = str(query).lower()
    if "or 1=1" in q or "--" in q or "union select" in q:
        return True
    has_keyword = any(k in q for k in ["select ", "insert ", "update ", "delete "])
    return has_keyword and "+" in q

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
        starter_code='''def solve(query):
    q = str(query).lower()
    if "or 1=1" in q or "--" in q or "union select" in q:
        return True
    has_keyword = any(k in q for k in ["select ", "insert ", "update ", "delete "])
    return has_keyword and "+" in q

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
            {"input": "SELECT * FROM users WHERE name = '\" + user + \"'", "expected_output": "true", "description": "Concatenated user input"},
            {"input": "SELECT * FROM users WHERE id = 42", "expected_output": "false", "description": "Parameter-free literal query"},
            {"input": "DELETE FROM logs WHERE id = '5' OR 1=1", "expected_output": "true", "description": "OR 1=1 marker"},
            {"input": "INSERT INTO t VALUES ('x')", "expected_output": "false", "description": "Literal insert"},
            {"input": "SELECT name FROM users WHERE role = '\" + role + \"'", "expected_output": "true", "description": "Concatenated role"},
        ],
    ),
    L(
        id="cyber-web-exercise-xss-detection",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-web",
        title="Exercise: Detect XSS Payloads",
        type="exercise",
        order=6,
        content="""## Exercise: Detect XSS Payloads

Write `solve(text)` that returns `True` when text contains **script payload markers** and `False` otherwise. Look for these (case-insensitive):

- `<script`,
- `onerror=`,
- `onload=`,
- `javascript:`,
- `<iframe`.

### Sample

Input (one line):

```text
<script>alert(1)</script>
```

Output:

```text
true
```

### How your code runs

The harness passes the text as a single string. Search for any of the markers and return a boolean.

### Starter code

```python
def solve(text):
    t = str(text).lower()
    markers = ["<script", "onerror=", "onload=", "javascript:", "<iframe"]
    return any(marker in t for marker in markers)

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
        starter_code='''def solve(text):
    t = str(text).lower()
    markers = ["<script", "onerror=", "onload=", "javascript:", "<iframe"]
    return any(marker in t for marker in markers)

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
            {"input": "<script>alert(1)</script>", "expected_output": "true", "description": "Script block"},
            {"input": "<img src=x onerror=alert(1)>", "expected_output": "true", "description": "Event handler"},
            {"input": "javascript:alert(1)", "expected_output": "true", "description": "Javascript scheme"},
            {"input": "hello world", "expected_output": "false", "description": "Plain text"},
            {"input": "<b>bold text</b>", "expected_output": "false", "description": "Benign markup"},
        ],
    ),
    L(
        id="cyber-web-exercise-sanitize-html",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-web",
        title="Exercise: Sanitize HTML (Strip Scripts)",
        type="exercise",
        order=7,
        content="""## Exercise: Sanitize HTML (Strip Scripts)

Write `solve(html)` that **removes every `<script>...</script>` block** from a string using plain string operations and returns the cleaned text.

- Find `<script` (case-insensitive), then find the matching `</script>`.
- Remove that whole block, then keep scanning the remaining text.

### Sample

Input (one line):

```text
<p>Hi</p><script>alert(1)</script>
```

Output:

```text
<p>Hi</p>
```

### How your code runs

The harness passes the HTML as a single string. Loop with `find`/`lower` to strip blocks until none remain, then return the result.

### Starter code

```python
def solve(html):
    text = html
    low = text.lower()
    start = low.find("<script")
    while start != -1:
        end = low.find("</script>", start)
        if end == -1:
            end = len(text)
        else:
            end += len("</script>")
        text = text[:start] + text[end:]
        low = text.lower()
        start = low.find("<script")
    return text.strip()

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
        starter_code='''def solve(html):
    text = html
    low = text.lower()
    start = low.find("<script")
    while start != -1:
        end = low.find("</script>", start)
        if end == -1:
            end = len(text)
        else:
            end += len("</script>")
        text = text[:start] + text[end:]
        low = text.lower()
        start = low.find("<script")
    return text.strip()

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
            {"input": "<p>Hi</p><script>alert(1)</script>", "expected_output": "<p>Hi</p>", "description": "Trailing script"},
            {"input": "<script>bad()</script>hello", "expected_output": "hello", "description": "Leading script"},
            {"input": "no script here", "expected_output": "no script here", "description": "No scripts"},
            {"input": "<SCRIPT>alert(1)</SCRIPT><div>ok</div>", "expected_output": "<div>ok</div>", "description": "Uppercase tags"},
            {"input": "<p>a</p><script>x()</script><p>b</p>", "expected_output": "<p>a</p><p>b</p>", "description": "Script in the middle"},
        ],
    ),
    # ── Module 3: Secure Programming ────────────────────────────────────
    L(
        id="cyber-secure-input-validation",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-secure-code",
        title="Input Validation",
        type="theory",
        order=1,
        content="""## Input Validation

**Input validation** checks that incoming data matches what your application expects *before* using it. It is the first and most important line of defense.

### The trust boundary

Anything that crosses a trust boundary — a network request, a file, an environment variable — is untrusted. Assume it is wrong until proven otherwise.

```python
def parse_amount(raw):
    try:
        amount = float(raw)
    except ValueError:
        raise ValueError("amount must be a number")
    if amount <= 0:
        raise ValueError("amount must be positive")
    return amount
```

### Validation techniques

| Technique                | What it checks                            |
|--------------------------|-------------------------------------------|
| Type check               | Is it the right type?                     |
| Length check             | Is it within acceptable bounds?           |
| Whitelist               | Does it contain only allowed characters?  |
| Range check              | Is it within acceptable numeric range?    |
| Format check             | Does it match the expected pattern?       |

### Whitelist vs blacklist

Prefer **whitelisting** (only allow what is known-good) over blacklisting (block what is known-bad):

```python
ALLOWED = set("abcdefghijklmnopqrstuvwxyz0123456789_")

def valid_username(name):
    return len(name) > 0 and all(ch in ALLOWED for ch in name)
```

A blacklist can never be complete — attackers invent new variants. A whitelist is complete by construction.

### Validate at the boundary

Validate once, as early as possible, and reject loudly:

1. Type — `isinstance` or conversion.
2. Length — bounds.
3. Charset — whitelist.
4. Range / format — semantic rules.

### Fail closed

When validation is ambiguous, deny:

```python
if not allowed:        # unknown case → denied
    return None
```

---

**Next up:** output encoding and safe display."""
    ),
    L(
        id="cyber-secure-output-encoding",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-secure-code",
        title="Output Encoding and Safe Display",
        type="theory",
        order=2,
        content="""## Output Encoding and Safe Display

Validation protects input; **output encoding** protects every place data gets rendered. Even validated data must be encoded before it appears in HTML, URLs, SQL, or shell commands.

### The principle

Interpretation context decides encoding: the same string is escaped differently in HTML, a URL, or JavaScript.

| Context      | Character set to encode       |
|--------------|-------------------------------|
| HTML body    | `< > & " '`                   |
| URL          | Anything non-alphanumeric     |
| SQL string   | `'` (and use parameters)      |
| Shell        | ``; | & $ `` " '`` etc.        |

### Safe DOM in the browser

In client code, prefer APIs that never parse strings as markup:

```javascript
// Safe: sets plain text, never executes markup
element.textContent = userComment;

// Dangerous: parses strings as HTML
element.innerHTML = userComment;
```

### Encoding vs validation — both

Encoding is not a substitute for validation, and validation is not a substitute for encoding:

- **Validation** rejects bad data at the boundary.
- **Encoding** neutralizes data that must pass through a context that interprets it.

```python
def escape_html(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))
```

### When encoding goes wrong

Forgetting encoding is how stored XSS happens: a "safe" comment rendered as raw HTML. Applying it consistently, at every sink, removes the whole class.

---

**Next up:** secrets handling — never hardcode, never log."""
    ),
    L(
        id="cyber-secure-secrets",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-secure-code",
        title="Secrets Handling",
        type="theory",
        order=3,
        content="""## Secrets Handling

**Secrets** are values that grant access: API keys, database passwords, signing tokens. Poorly handled secrets are one of the most common real-world breaches.

### Where secrets leak

1. **Hardcoded in source code** — committed to git, visible to everyone.
2. **Logged** — printed by mistake during debugging.
3. **Committed to version control** — `sk-...` pasted into a config file.
4. **Sent to the wrong place** — client-side bundles, chat, support tickets.

### Rules for handling secrets

| Rule                           | Why                                          |
|--------------------------------|----------------------------------------------|
| Never hardcode secrets         | Source is shared and versioned               |
| Use environment variables      | Kept out of the repo, per-deployment         |
| Inject at runtime              | Config in, code stays secret-free            |
| Rotate and revoke              | A leaked key becomes useless                 |
| Never log secrets              | Logs are read by many systems and people     |

```python
import os

API_KEY = os.environ["API_KEY"]   # not "sk-..." in the source
```

### Detect, then react

Scan logs and code for known secret patterns (`sk-`, `AKIA`, `ghp_`, `api_key=`). When one is found:

1. **Revoke it immediately** — assume it is already compromised.
2. **Rotate** — issue a new key.
3. **Find how it leaked** — fix the source.
4. **Redact** — scrub it from logs and history.

### Redaction is defense

When logs must contain request details, redact the secret-bearing fields before they hit disk:

```python
def redact(line):
    marker = "api_key="
    if marker in line:
        return line.split(marker)[0] + marker + "[REDACTED]"
    return line
```

---

**Next up:** dependency risk — third-party code is still your code."""
    ),
    L(
        id="cyber-secure-dependencies",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-secure-code",
        title="Dependency Risk",
        type="theory",
        order=4,
        content="""## Dependency Risk

Modern applications are built mostly from **dependencies** — libraries you did not write. Each one is code that runs with your application's privileges, so each one is part of your attack surface.

### Why dependencies are risky

- **Known vulnerabilities** — a library with a public CVE you installed.
- **Supply-chain attacks** — a compromised or malicious package.
- **Stale versions** — bug fixes you never received.
- **Scope creep** — huge libraries used for one tiny helper.

### Managing the risk

| Practice                      | Effect                              |
|-------------------------------|-------------------------------------|
| Pin exact versions            | Reproducible, auditable builds      |
| Update regularly              | Receive security fixes              |
| Audit with scanners           | `pip-audit`, `npm audit`, etc.      |
| Minimize dependencies         | Smaller attack surface              |
| Review unusual packages       | New, unknown packages deserve scrutiny |

```bash
# Example audits — run them regularly in CI
pip-audit
npm audit
```

### Know your supply chain

Ask before adding a package:

1. Is it well-known and actively maintained?
2. Does it have a history of CVEs?
3. Do I need all of it, or a smaller alternative?
4. Can I get the same result with less code?

### Treat dependencies as owned code

You are responsible for every line that ships, including borrowed ones. If a dependency is abandoned or vulnerable, replace or patch it — do not ignore it.

### The habit

Make dependency hygiene routine: audit on a schedule, update deliberately, and never install a package you do not understand.

---

**Next up:** exercises — whitelist validation, URL scheme allowlists, and HTML output encoding."""
    ),
    L(
        id="cyber-secure-exercise-whitelist",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-secure-code",
        title="Exercise: Input Whitelist Validation",
        type="exercise",
        order=5,
        content="""## Exercise: Input Whitelist Validation

Write `solve(text, allowed)` that returns `True` when **every character** of `text` appears in the `allowed` string, and `False` otherwise. An empty `text` is considered valid.

This is a whitelist check: only known-good characters pass.

### Sample

Input:

```text
"ada"
abcdefghijklmnopqrstuvwxyz
```

Output:

```text
true
```

### How your code runs

The harness passes the text (a quoted string) on line 1 and the allowed characters on line 2.

### Starter code

```python
def solve(text, allowed):
    return all(ch in allowed for ch in str(text))

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    text = lines[0].strip().strip('"')
    allowed = lines[1].strip()
    print(str(solve(text, allowed)).lower())

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(text, allowed):
    return all(ch in allowed for ch in str(text))

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    text = lines[0].strip().strip('"')
    allowed = lines[1].strip()
    print(str(solve(text, allowed)).lower())

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '"ada"\nabcdefghijklmnopqrstuvwxyz', "expected_output": "true", "description": "Lowercase letters"},
            {"input": '"Ada"\nabcdefghijklmnopqrstuvwxyz', "expected_output": "false", "description": "Uppercase not allowed"},
            {"input": '"user1"\nabcdefghijklmnopqrstuvwxyz0123456789', "expected_output": "true", "description": "Letters and digits"},
            {"input": '"user!"\nabcdefghijklmnopqrstuvwxyz0123456789', "expected_output": "false", "description": "Symbol not allowed"},
        ],
    ),
    L(
        id="cyber-secure-exercise-url-scheme",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-secure-code",
        title="Exercise: URL Scheme Allowlist",
        type="exercise",
        order=6,
        content="""## Exercise: URL Scheme Allowlist

Write `solve(url)` that returns `True` only when the URL uses a **safe scheme** (`http`, `https`, or `ftp`) and `False` otherwise.

- A scheme is the text before `://`.
- A URL with no `://` has no scheme → not allowed.

### Sample

Input (one line):

```text
https://example.com
```

Output:

```text
true
```

### How your code runs

The harness passes the URL as a single string. Extract the scheme and compare against the allowlist.

### Starter code

```python
def solve(url):
    u = str(url)
    if "://" not in u:
        return False
    scheme = u.split("://", 1)[0].lower()
    return scheme in {"http", "https", "ftp"}

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
        starter_code='''def solve(url):
    u = str(url)
    if "://" not in u:
        return False
    scheme = u.split("://", 1)[0].lower()
    return scheme in {"http", "https", "ftp"}

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
            {"input": "https://example.com", "expected_output": "true", "description": "HTTPS allowed"},
            {"input": "javascript:alert(1)", "expected_output": "false", "description": "Javascript scheme blocked"},
            {"input": "file:///etc/passwd", "expected_output": "false", "description": "File scheme blocked"},
            {"input": "ftp://files.example.com", "expected_output": "true", "description": "FTP allowed"},
            {"input": "example.com", "expected_output": "false", "description": "No scheme present"},
        ],
    ),
    L(
        id="cyber-secure-exercise-html-escape",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-secure-code",
        title="Exercise: HTML Output Encoding",
        type="exercise",
        order=7,
        content="""## Exercise: HTML Output Encoding

Write `solve(text)` that **encodes** text for safe HTML display. Replace (in this order):

- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`
- `'` → `&#39;`

### Sample

Input (one line):

```text
<b>hi</b>
```

Output:

```text
&lt;b&gt;hi&lt;/b&gt;
```

### How your code runs

The harness passes the text as a single string. Return the encoded version.

### Starter code

```python
def solve(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

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
        starter_code='''def solve(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

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
            {"input": "<b>hi</b>", "expected_output": "&lt;b&gt;hi&lt;/b&gt;", "description": "Angle brackets"},
            {"input": "a & b", "expected_output": "a &amp; b", "description": "Ampersand first"},
            {"input": 'she said "hi"', "expected_output": "she said &quot;hi&quot;", "description": "Double quotes"},
            {"input": "plain text 123", "expected_output": "plain text 123", "description": "Plain text unchanged"},
        ],
    ),
    # ── Module 4: Networks and Access Control ───────────────────────────
    L(
        id="cyber-networks-http-tls",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-networks",
        title="HTTP and TLS",
        type="theory",
        order=1,
        content="""## HTTP and TLS

Web traffic runs over **HTTP**, and in practice that traffic is protected by **TLS** (the `s` in `https`).

### HTTP in brief

An HTTP request has a **method**, a **path**, **headers**, and often a **body**:

```text
POST /api/login HTTP/1.1
Host: example.com
Content-Type: application/json

{"user": "ada", "password": "..."}
```

Responses carry a **status code**: `200` OK, `401` unauthorized, `403` forbidden, `404` not found, `500` server error.

### Why plain HTTP is insecure

Without encryption, anyone on the network path — a Wi-Fi hotspot, an ISP, a router — can read and modify traffic. Passwords, tokens, and messages travel in plain text.

### What TLS provides

| Property          | Meaning                                          |
|-------------------|--------------------------------------------------|
| Confidentiality   | Traffic is encrypted in transit                 |
| Integrity         | Tampering is detected                           |
| Authentication    | You can verify the server's identity (certificate) |

### HTTPS is the default

```text
https://example.com  → HTTP + TLS
```

- Certificates are validated by browsers, so users can trust the server identity.
- Modern practice: **only** HTTPS, with HTTP redirecting or refusing.

### Security headers

Defense also comes from HTTP response headers:

| Header                            | Purpose                          |
|-----------------------------------|----------------------------------|
| `Strict-Transport-Security`       | Force HTTPS                      |
| `Content-Security-Policy`         | Restrict what the page may load  |
| `X-Content-Type-Options`          | Prevent MIME sniffing            |
| `SameSite` cookie attribute       | Limit cross-site cookie sending  |

### Think in layers

TLS protects traffic *in transit*. It does not protect against a compromised server, an injection bug, or a leaked key — which is why transport security is one layer among many.

---

**Next up:** sessions and tokens — proving identity after the password."""
    ),
    L(
        id="cyber-networks-sessions",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-networks",
        title="Sessions and Tokens",
        type="theory",
        order=2,
        content="""## Sessions and Tokens

After a user logs in, the server must remember who they are for subsequent requests. That is the job of **sessions** and **tokens**.

### The session model

1. The user logs in with credentials.
2. The server creates a **session** (an id tied to the user) and stores it server-side.
3. The server sends a cookie containing the session id.
4. Every request carries the cookie; the server looks up the session.

```python
sessions = {"abc123": "user_42"}   # server-side store

def current_user(cookie):
    session_id = cookie.get("session_id")
    return sessions.get(session_id)
```

### Token-based model

Instead of server-side state, the server issues a **token** the client sends on every request. Tokens typically carry claims and an expiry.

```python
def token_is_valid(token):
    if token["expires"] <= now():
        return False
    return token["signature_is_valid"]
```

### Hardening sessions

| Practice                  | Why                                    |
|---------------------------|----------------------------------------|
| Expire sessions           | Limit a stolen cookie's usefulness     |
| Rotate on privilege change| Logout/role changes invalidate old ones|
| Secure cookie flags       | `HttpOnly`, `Secure`, `SameSite`       |
| Regenerate after login    | Prevent session fixation               |

### Expiry is a core control

A token or session that never expires is a standing credential an attacker can reuse forever. Expiry forces re-authentication:

```python
def expired(token, now):
    return now >= token["expires"]
```

The exercises in this module implement expiry checks and rate limiting on toy data — the same logic production code uses.

---

**Next up:** permissions and role-based access control."""
    ),
    L(
        id="cyber-networks-permissions",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-networks",
        title="Permissions and RBAC",
        type="theory",
        order=3,
        content="""## Permissions and RBAC

Knowing *who* a user is matters only if you then check *what they may do*. That is access control, and the common model is **Role-Based Access Control (RBAC)**.

### Roles and permissions

A **role** is a named bundle of **permissions**:

```python
ROLES = {
    "viewer": {"read"},
    "editor": {"read", "write"},
    "admin":  {"read", "write", "delete", "share"},
}
```

A user is assigned one or more roles. Access checks ask: does the user's role contain this permission?

```python
def can(user_role, action):
    return action in ROLES.get(user_role, set())
```

### Checking at every gate

Authorization must be enforced at the point of access, not just in the UI:

- **Frontend** hiding a button is convenience, not security.
- The **backend** must independently verify every action.

```python
def delete_document(user_role, doc_id):
    if not can(user_role, "delete"):
        raise PermissionError("forbidden")
    ...
```

### Least privilege in RBAC

Assign the smallest role that does the job. A support agent who only needs `read` should not hold `delete`. Combine least privilege with fail-closed lookups: an unknown role gets no permissions.

### Ownership checks

Roles are coarse; some permissions are **per-object**. A user may edit *their own* document but not another's:

```python
def can_edit(user, document):
    return user.role == "admin" or user.id == document.owner_id
```

### Why this matters defensively

Most access-control breaches are **missing checks**, not sophisticated attacks: an endpoint that forgets to authorize, a role map with an accidental wildcard. Writing explicit, fail-closed checks removes the whole class.

---

**Next up:** network fundamentals with a defensive lens."""
    ),
    L(
        id="cyber-networks-basics",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-networks",
        title="Network Fundamentals (Defensive)",
        type="theory",
        order=4,
        content="""## Network Fundamentals (Defensive)

You do not need to be a network engineer to secure software, but knowing the basics makes you a better defender.

### Addresses and ports

Every machine on a network has an **IP address**. Services listen on **ports**:

```text
web server   → port 80 / 443
ssh          → port 22
database     → port 5432 (PostgreSQL), 3306 (MySQL)
```

**Reduce exposure**: expose only the ports that must be public. A database should not listen on the public internet.

### Firewalls and rules

A **firewall** allows or blocks traffic by address, port, and protocol:

```text
allow 443/tcp from anywhere     # public HTTPS
allow 22/tcp from office       # admin SSH from trusted range only
deny  everything else
```

This is network-level least privilege.

### Rate limiting

A **rate limit** caps how many requests a client may make in a window. It protects availability and slows brute-force attacks:

```python
def within_limit(requests, limit, window, now):
    recent = [t for t in requests if now - window < t <= now]
    return len(recent) < limit
```

### Monitoring and logging

You cannot respond to what you cannot see. Collect structured logs of authentication events, access decisions, and errors — and review them. Logging is the detection layer of defense in depth.

### Threat modeling networks

For any networked feature ask:

1. Who can reach it (exposure)?
2. How can it be abused (rate, volume, content)?
3. What should be blocked by default (deny-by-default)?

Networks are just more attack surface to manage with the same principles: least privilege, fail-closed, layered defense.

---

**Next up:** exercises — role permission checks, token expiry, and rate limiting."""
    ),
    L(
        id="cyber-networks-exercise-permissions",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-networks",
        title="Exercise: Role Permission Check",
        type="exercise",
        order=5,
        content="""## Exercise: Role Permission Check

Write `solve(role, action)` that returns `True` when the role is allowed the action, using this role matrix:

| Role    | Allowed actions                  |
|---------|----------------------------------|
| `admin` | `read`, `write`, `delete`, `share` |
| `editor`| `read`, `write`                 |
| `viewer`| `read`                          |

Unknown roles get no permissions (fail closed).

### Sample

Input:

```text
admin
delete
```

Output:

```text
true
```

### How your code runs

The harness passes the role on line 1 and the action on line 2, both plain strings. Look up the role's permission set and test membership.

### Starter code

```python
ROLES = {
    "admin": {"read", "write", "delete", "share"},
    "editor": {"read", "write"},
    "viewer": {"read"},
}

def solve(role, action):
    return action in ROLES.get(role, set())

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    role = lines[0].strip()
    action = lines[1].strip()
    print(str(solve(role, action)).lower())

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''ROLES = {
    "admin": {"read", "write", "delete", "share"},
    "editor": {"read", "write"},
    "viewer": {"read"},
}

def solve(role, action):
    return action in ROLES.get(role, set())

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    role = lines[0].strip()
    action = lines[1].strip()
    print(str(solve(role, action)).lower())

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "admin\ndelete", "expected_output": "true", "description": "Admin can delete"},
            {"input": "editor\ndelete", "expected_output": "false", "description": "Editor cannot delete"},
            {"input": "viewer\nread", "expected_output": "true", "description": "Viewer can read"},
            {"input": "viewer\nwrite", "expected_output": "false", "description": "Viewer cannot write"},
            {"input": "guest\nread", "expected_output": "false", "description": "Unknown role is denied"},
        ],
    ),
    L(
        id="cyber-networks-exercise-token-expiry",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-networks",
        title="Exercise: Token Expiry Check",
        type="exercise",
        order=6,
        content="""## Exercise: Token Expiry Check

Write `solve(expires, now)` that returns `True` when a token is still valid (`now < expires`) and `False` when it is expired (`now >= expires`).

### Sample

Input:

```text
2000
1000
```

Output:

```text
true
```

### How your code runs

The harness passes two integers: the token's expiry time and the current time. Compare them and return a boolean.

### Starter code

```python
def solve(expires, now):
    return now < expires

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    expires = int(lines[0].strip())
    now = int(lines[1].strip())
    print(str(solve(expires, now)).lower())

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(expires, now):
    return now < expires

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    expires = int(lines[0].strip())
    now = int(lines[1].strip())
    print(str(solve(expires, now)).lower())

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "2000\n1000", "expected_output": "true", "description": "Token in the future"},
            {"input": "1000\n2000", "expected_output": "false", "description": "Token expired"},
            {"input": "1000\n1000", "expected_output": "false", "description": "Expired at the exact moment"},
            {"input": "500\n499", "expected_output": "true", "description": "About to expire but valid"},
        ],
    ),
    L(
        id="cyber-networks-exercise-rate-limit",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-networks",
        title="Exercise: Rate Limit Checker",
        type="exercise",
        order=7,
        content="""## Exercise: Rate Limit Checker

Write `solve(now, requests, limit)` that returns `True` when a client is **within** its rate limit and `False` when it exceeds it.

A request counts toward the limit if it falls inside the last 60 time units: `now - 60 < request_time <= now`. The client is allowed at most `limit` requests in that window.

### Sample

Input:

```text
1000
[900, 950, 980]
2
```

Output:

```text
true
```

At `now=1000`, the window is `(940, 1000]`. Requests `950` and `980` fall inside (2), `900` is outside. `2 <= 2`, so the request is allowed.

### How your code runs

The harness passes three values on three lines: the current time, a JSON list of request times, and the limit.

### Starter code

```python
def solve(now, requests, limit):
    recent = [t for t in requests if now - 60 < t <= now]
    return len(recent) <= limit

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    now = int(lines[0].strip())
    requests = json.loads(lines[1].strip())
    limit = int(lines[2].strip())
    print(str(solve(now, requests, limit)).lower())

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(now, requests, limit):
    recent = [t for t in requests if now - 60 < t <= now]
    return len(recent) <= limit

def main():
    import sys, json
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    now = int(lines[0].strip())
    requests = json.loads(lines[1].strip())
    limit = int(lines[2].strip())
    print(str(solve(now, requests, limit)).lower())

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "1000\n[900,950,980]\n2", "expected_output": "true", "description": "Two requests inside a limit of two"},
            {"input": "1000\n[900,950,980,990]\n2", "expected_output": "false", "description": "Three requests over the limit"},
            {"input": "1000\n[800,900]\n5", "expected_output": "true", "description": "No requests in the window"},
            {"input": "500\n[490,491]\n1", "expected_output": "false", "description": "Two requests, limit one"},
            {"input": "1000\n[]\n3", "expected_output": "true", "description": "Empty request list"},
        ],
    ),
    # ── Module 5: Secure Application Project ────────────────────────────
    L(
        id="cyber-project-finding",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-project",
        title="Finding Vulnerabilities Safely",
        type="theory",
        order=1,
        content="""## Finding Vulnerabilities Safely

The project module asks you to find and fix vulnerabilities **inside a safe code sandbox** — pure Python logic running on toy data you supply. Nothing here touches real systems, and nothing teaches attacking anything.

### What "safe" means here

- **Toy data only** — the inputs are example strings you invent.
- **Pure logic** — string checks, set membership, simple arithmetic.
- **Your own sandbox** — you are reviewing code you wrote, not probing others.

### The review approach

Read code like an adversary *conceptually*, but act like a defender:

1. Read the code for risky patterns.
2. Describe the risk in one sentence.
3. Fix the code so the risk is gone.
4. Test the fix with both safe and hostile-looking inputs.

### Example: a risky query builder

```python
def find_user(name):
    # RISK: name is concatenated into SQL
    return run("SELECT * FROM users WHERE name = '" + name + "'")
```

The fix treats input as data:

```python
def find_user(name):
    # SAFE: name is escaped (parameterized in real code)
    return run("SELECT * FROM users WHERE name = %s", name)
```

### Hostile inputs are just strings

In this course, "attack payloads" are ordinary strings like `Robert'); DROP TABLE users;--`. Running them through your own functions is no different from testing any string function — there is nothing live to harm.

### If you are ever unsure

When in doubt, do not try it. The exercises are self-contained; if a task feels like it could touch something real, stop and revisit the brief.

---

**Next up:** patching the safe sandbox — turning risky code into hardened code."""
    ),
    L(
        id="cyber-project-patching",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-project",
        title="Patching a Safe Code Sandbox",
        type="theory",
        order=2,
        content="""## Patching a Safe Code Sandbox

The project exercises present small, deliberately vulnerable functions and ask you to **harden them**. Each fix applies one defensive technique you have learned.

### The patch playbook

| Vulnerability        | Technique to apply                     |
|----------------------|----------------------------------------|
| Secret in logs       | Redact the value before writing        |
| SQL concatenation    | Escape quotes / use parameters         |
| Missing access check | Fail-closed permission lookup          |
| Overlong input       | Length limits                          |
| Unsafe URL scheme    | Scheme allowlist                       |

### Example patch 1: secret redaction

```python
# Before — full secret hits the log
logger.info(f"login from token={token}")

# After — value replaced
logger.info(f"login from token={redact(token)}")
```

### Example patch 2: escaping for SQL strings

Where parameters are not available, single quotes must be escaped so user data cannot break out of a string literal:

```python
def escape_sql(value):
    return str(value).replace("'", "''")
```

### Example patch 3: access control

```python
# Before — any caller can delete
def delete_doc(doc_id):
    ...

# After — fail-closed check first
def delete_doc(role, doc_id):
    if role not in ALLOWED_DELETE:
        raise PermissionError("forbidden")
    ...
```

### Test the patch both ways

For every fix, confirm two behaviors:

1. **Benign input still works** (no regressions).
2. **Hostile-looking input is neutralized** (the risk is gone).

Both matter: a patch that breaks normal use is not deployed, and one that only works for one payload is not a fix.

---

**Next up:** secure defaults and responsible logging."""
    ),
    L(
        id="cyber-project-defaults-logging",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-project",
        title="Secure Defaults and Logging",
        type="theory",
        order=3,
        content="""## Secure Defaults and Logging

Two habits separate hardened code from merely working code: **secure defaults** and **responsible logging**.

### Secure defaults

A system should be **safe unless configured otherwise**, not vulnerable until someone remembers to fix it.

```python
# Before — open by default (dangerous)
def share(document, everyone=False):
    if everyone:
        document.public = True

# After — closed by default (safe)
def share(document, everyone=False):
    if not everyone:
        return
    document.public = True
```

The default state of any new feature should be *deny*: private, unlisted, unprivileged. You can always relax later; tightening is painful.

### Fail-closed operations

When something goes wrong, deny rather than allow:

```python
def can_access(role, resource):
    return role in ROLES and resource in ROLES[role]   # unknown → False
```

An error path that "accidentally allows" is a vulnerability; one that denies is just an outage.

### Responsible logging

Logs must record *what happened* without recording *secrets*:

| Log                                   | Problem          |
|---------------------------------------|------------------|
| `login token=sk-abc123def`            | Secret exposed   |
| `password changed for user@example.com` | OK (no secret) |
| `request body: {"password": "x"}`     | Secret exposed   |

Rules:

- Never log passwords, tokens, or full request bodies.
- Redact secrets before any line hits the log.
- Log enough to investigate: who, what, when, result.

```python
def safe_log_event(action, actor, ok):
    return f"{action} by {actor}: {'ok' if ok else 'denied'}"
```

### The project lens

Every exercise in this module is one of these habits applied to toy data: redact the secret, escape the value, check the access. Get the defaults right and the logs clean, and the rest of security has a solid base.

---

**Next up:** a review workflow you can use on your own code."""
    ),
    L(
        id="cyber-project-review-workflow",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-project",
        title="The Security Review Workflow",
        type="theory",
        order=4,
        content="""## The Security Review Workflow

Reviewing your own code takes discipline. A short, repeatable checklist finds most problems before anyone else does.

### A five-minute checklist

For every function that accepts external data:

1. **Input** — Is the type, length, and charset validated?
2. **Query** — Is SQL parameterized, never concatenated?
3. **Output** — Is data encoded before rendering?
4. **Secrets** — Could this line leak a key or password?
5. **Access** — Is every action checked, fail-closed?

### The review loop

```text
read the code
 → name the data that crosses a trust boundary
 → trace it to every place it is used
 → at each use, ask: interpreted? displayed? stored? logged?
 → apply the matching control
 → test with benign and hostile inputs
```

### Data flow thinking

Follow a single value through the system. If it starts as user input and ends up in SQL, HTML, a log, or a file, it needs a control at that sink:

```python
# user input arrives
name = request.form["name"]

# validated at the boundary
name = validate(name, max_len=50, allowed=ALNUM)

# used safely downstream (parameterized / encoded / redacted)
```

### Pair review

A second reader sees what you miss. Rotating reviews of security-sensitive changes is cheap insurance.

### When to automate

Checks that are mechanical — "no `+` inside SQL strings", "no `sk-` in logs" — belong in linters and CI so humans can focus on the judgment calls.

### You are ready

You now have the tools: validate, encode, redact, expire, limit, and check access. The remaining exercises put all of it together on toy data.

---

**Next up:** the project exercises — redacting secrets, escaping SQL, and checking file access."""
    ),
    L(
        id="cyber-project-exercise-redact",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-project",
        title="Exercise: Redact Secrets in a Log Line",
        type="exercise",
        order=5,
        content="""## Exercise: Redact Secrets in a Log Line

Write `solve(line)` that **redacts secret values** in a log line and returns the safe version. Redact the value that follows each of these markers (until the next space or end of line):

- `token=`
- `api_key=`
- `password=`

Also redact the alphanumeric run that follows a bare `sk-`.

Replace each secret value with `[REDACTED]`.

### Sample

Input (one line):

```text
token=sk-1234567890abcdef action=ok
```

Output:

```text
token=[REDACTED] action=ok
```

### How your code runs

The harness passes the log line as a single string. Apply the markers and return the cleaned line.

### Starter code

```python
def solve(line):
    out = line
    for marker in ["token=", "api_key=", "password="]:
        out = redact_value(out, marker)
    out = redact_key(out, "sk-")
    return out

def redact_value(text, marker):
    out = text
    low = out.lower()
    idx = low.find(marker)
    while idx != -1:
        start = idx + len(marker)
        end = start
        while end < len(out) and not out[end].isspace():
            end += 1
        out = out[:start] + "[REDACTED]" + out[end:]
        low = out.lower()
        idx = low.find(marker, start + len("[REDACTED]"))
    return out

def redact_key(text, marker):
    out = text
    low = out.lower()
    idx = low.find(marker)
    while idx != -1:
        start = idx + len(marker)
        end = start
        while end < len(out) and out[end].isalnum():
            end += 1
        out = out[:start] + "[REDACTED]" + out[end:]
        low = out.lower()
        idx = low.find(marker, start + len("[REDACTED]"))
    return out

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
        starter_code='''def solve(line):
    out = line
    for marker in ["token=", "api_key=", "password="]:
        out = redact_value(out, marker)
    out = redact_key(out, "sk-")
    return out

def redact_value(text, marker):
    out = text
    low = out.lower()
    idx = low.find(marker)
    while idx != -1:
        start = idx + len(marker)
        end = start
        while end < len(out) and not out[end].isspace():
            end += 1
        out = out[:start] + "[REDACTED]" + out[end:]
        low = out.lower()
        idx = low.find(marker, start + len("[REDACTED]"))
    return out

def redact_key(text, marker):
    out = text
    low = out.lower()
    idx = low.find(marker)
    while idx != -1:
        start = idx + len(marker)
        end = start
        while end < len(out) and out[end].isalnum():
            end += 1
        out = out[:start] + "[REDACTED]" + out[end:]
        low = out.lower()
        idx = low.find(marker, start + len("[REDACTED]"))
    return out

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
            {"input": "token=sk-1234567890abcdef action=ok", "expected_output": "token=[REDACTED] action=ok", "description": "Token value redacted"},
            {"input": "password=supersecret123 ok", "expected_output": "password=[REDACTED] ok", "description": "Password value redacted"},
            {"input": "INFO: request completed 200", "expected_output": "INFO: request completed 200", "description": "Benign line unchanged"},
            {"input": "auth api_key=abc123xyz done", "expected_output": "auth api_key=[REDACTED] done", "description": "api_key value redacted"},
            {"input": "using sk-abcdefghijklmnop here", "expected_output": "using sk-[REDACTED] here", "description": "Bare sk- key redacted"},
        ],
    ),
    L(
        id="cyber-project-exercise-sql-escape",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-project",
        title="Exercise: Escape SQL String Input",
        type="exercise",
        order=6,
        content="""## Exercise: Escape SQL String Input

Write `solve(value)` that **escapes** a string for safe inclusion in a SQL string literal: every single quote `'` becomes two single quotes `''`. This neutralizes payloads that try to break out of a quoted string.

### Sample

Input (one line):

```text
Robert'); DROP TABLE users;--
```

Output:

```text
Robert''); DROP TABLE users;--
```

### How your code runs

The harness passes the value as a single string. Replace every `'` with `''` and return the result.

### Starter code

```python
def solve(value):
    return str(value).replace("'", "''")

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
        starter_code='''def solve(value):
    return str(value).replace("'", "''")

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
            {"input": "Robert'); DROP TABLE users;--", "expected_output": "Robert''); DROP TABLE users;--", "description": "Injection-style payload escaped"},
            {"input": "O'Reilly", "expected_output": "O''Reilly", "description": "Single quote doubled"},
            {"input": "safe query", "expected_output": "safe query", "description": "Benign value unchanged"},
            {"input": "it's fine", "expected_output": "it''s fine", "description": "Contraction escaped"},
        ],
    ),
    L(
        id="cyber-project-exercise-file-access",
        course_id="cybersecurity-fundamentals",
        module_id="cyber-project",
        title="Exercise: File Access Permission Check",
        type="exercise",
        order=7,
        content="""## Exercise: File Access Permission Check

Write `solve(owner, current_user, is_admin)` that returns `True` when a user may read a file:

- **Owners** may always read their own files.
- **Admins** may read any file.
- Otherwise the read is **denied** (fail closed).

### Sample

Input:

```text
"alice"
"alice"
false
```

Output:

```text
true
```

### How your code runs

The harness passes three values on three lines: the owner (a quoted string), the current user (a quoted string), and `true`/`false` for admin.

### Starter code

```python
def solve(owner, current_user, is_admin):
    return is_admin or owner == current_user

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    owner = lines[0].strip().strip('"')
    current_user = lines[1].strip().strip('"')
    is_admin = lines[2].strip().lower() == "true"
    print(str(solve(owner, current_user, is_admin)).lower())

if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(owner, current_user, is_admin):
    return is_admin or owner == current_user

def main():
    import sys
    data = sys.stdin.read().strip()
    if not data:
        return
    lines = data.splitlines()
    owner = lines[0].strip().strip('"')
    current_user = lines[1].strip().strip('"')
    is_admin = lines[2].strip().lower() == "true"
    print(str(solve(owner, current_user, is_admin)).lower())

if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": '"alice"\n"alice"\nfalse', "expected_output": "true", "description": "Owner can read"},
            {"input": '"alice"\n"bob"\nfalse', "expected_output": "false", "description": "Non-owner denied"},
            {"input": '"alice"\n"bob"\ntrue', "expected_output": "true", "description": "Admin can read any file"},
            {"input": '"alice"\n"alice"\ntrue', "expected_output": "true", "description": "Owner and admin"},
        ],
    ),
]
