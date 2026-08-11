"""Data Analytics with R — curriculum content module."""

COURSE = {
    "id": "data-analytics-with-r",
    "title": "Data Analytics with R",
    "description": (
        "A complete analytics workflow in R: frame a question, import data, wrangle "
        "it into shape, explore distributions and relationships, run statistical "
        "checks, and report actionable recommendations. Concepts mirror the tidyverse "
        "style, while every exercise runs on base R so you can practice right here."
    ),
    "language": "r",
    "icon": "r",
    "order": 7,
}

MODULES = [
    {
        "id": "da-workflow",
        "course_id": "data-analytics-with-r",
        "title": "Analytics Workflow",
        "description": "Turn a business question into a data problem, get data into R, and structure analysis so it can be repeated.",
        "order": 1,
    },
    {
        "id": "da-wrangling",
        "course_id": "data-analytics-with-r",
        "title": "Data Wrangling",
        "description": "Filter, group, aggregate, join, and reshape data with the tidyverse mindset expressed in base R.",
        "order": 2,
    },
    {
        "id": "da-eda",
        "course_id": "data-analytics-with-r",
        "title": "Exploratory Data Analysis",
        "description": "Probe distributions, spot outliers, measure spread, and quantify relationships between variables.",
        "order": 3,
    },
    {
        "id": "da-statistics",
        "course_id": "data-analytics-with-r",
        "title": "Statistical Analysis",
        "description": "Sample data, build confidence intervals, run basic hypothesis checks, and fit simple regression lines.",
        "order": 4,
    },
    {
        "id": "da-project",
        "course_id": "data-analytics-with-r",
        "title": "Analytics Project",
        "description": "Pull the whole workflow together: choose a dataset, analyze it, and report data-driven recommendations.",
        "order": 5,
    },
]

_R = "r"


def L(**kw):
    kw.setdefault("language", _R)
    return kw


LESSONS = [
    # ── Module 1: Analytics Workflow ────────────────────────────────────
    L(
        id="da-workflow-questions",
        course_id="data-analytics-with-r",
        module_id="da-workflow",
        title="From Question to Data",
        type="theory",
        order=1,
        content="""## From Question to Data

Every analytics project starts with a **question**, not with data. Before loading a single file, decide what decision the analysis will inform.

### Turning a vague ask into a measurable question

A stakeholder might say *"sales are falling — look into it"*. As an analyst you refine that into something answerable:

| Vague ask                 | Measurable question                          |
|---------------------------|----------------------------------------------|
| "Sales are falling"       | "Which product lines dropped the most in Q4?" |
| "Our users seem unhappy"  | "Does the 2-star rating share exceed 10%?"    |
| "One region underperforms"| "Is the West region's mean order value below the overall mean?" |

### Choosing metrics

Pick metrics you can actually compute from available data — counts, sums, means, rates, shares. Each metric should map back to the decision:

```r
avg_order <- sum(revenue) / sum(orders)   # revenue per order
churn_rate <- churned_users / total_users # proportion who left
```

### The question drives everything

The question decides which columns matter, which groups to compare, and which statistical test fits. Changing the question changes the analysis — so write it down and confirm it before you start.

A clear question gives you three things: a **target** (what you measure), a **scope** (which subset of data), and a **decision rule** (what result means what action).

---

**Next up:** getting data into R so you can start answering the question."""
    ),
    L(
        id="da-workflow-import",
        course_id="data-analytics-with-r",
        module_id="da-workflow",
        title="Importing Data into R",
        type="theory",
        order=2,
        content="""## Importing Data into R

Analysis starts when data arrives in R. The workhorse is `read.csv()`, which turns a comma-separated file into a data frame.

### Reading a CSV file

```r
sales <- read.csv("sales.csv", stringsAsFactors = FALSE)
head(sales)       # first six rows
str(sales)        # column types
summary(sales)    # per-column stats
```

### Reading from a text string

When your data lives in a character string — as in this course's exercises — `read.csv(text = ...)` parses it directly:

```r
text <- "product,revenue
books,1200
toys,800
"
df <- read.csv(text = text, stringsAsFactors = FALSE)
```

### Reading raw lines

`readLines()` pulls a file in as plain text, one string per line. You then parse each line yourself — the pattern used by the sandbox exercises:

```r
lines <- readLines(file("stdin"), warn = FALSE)
first <- strsplit(lines[1], ",")[[1]]
```

### Inspect before you compute

The golden rule: **always inspect data right after loading**. `head()`, `str()`, `dim()`, `names()`, and `summary()` reveal wrong column types, stray separators, and missing values before they poison your analysis.

- `dim(df)` — rows and columns.
- `names(df)` — column names.
- `nrow(df)` / `ncol(df)` — row and column counts.

---

**Next up:** keeping your analysis reproducible so others (and future you) can trust it."""
    ),
    L(
        id="da-workflow-repro",
        course_id="data-analytics-with-r",
        module_id="da-workflow",
        title="Reproducible Analysis",
        type="theory",
        order=3,
        content="""## Reproducible Analysis

A **reproducible** analysis produces the same result every time it is run. It is the difference between "I found something" and "here is how I found it".

### The script is the source of truth

Keep every step in a script, not in console sessions. A script documents the analysis and lets you re-run it on new data:

```r
# 01_load.R
sales <- read.csv("data/sales.csv")

# 02_clean.R
sales <- sales[!is.na(sales$revenue), ]

# 03_report.R
mean_revenue <- mean(sales$revenue)
cat("Mean revenue:", mean_revenue, "\\n")
```

### Pin the random seed

Randomness breaks reproducibility. `set.seed()` makes `sample()` and other random functions repeatable:

```r
set.seed(42)
subset <- sample(1:nrow(df), size = 100)
```

Run it twice with the same seed and you get the same rows — critical for audits and debugging.

### Structure a project

A small, predictable layout helps every future reader:

- `data/` — raw, untouched inputs.
- `scripts/` — numbered analysis steps.
- `output/` — charts and result tables.
- `report/` — the write-up.

### Comment the why, not the what

Code says what it does; comments say why it does it. A one-line rationale above a non-obvious filter is worth ten lines of explanation later:

```r
# Only active accounts count toward retention
active <- df[df$status == "active", ]
```

---

**Next up:** the end-to-end pipeline that ties import, wrangle, explore, analyze, and report together."""
    ),
    L(
        id="da-workflow-pipeline",
        course_id="data-analytics-with-r",
        module_id="da-workflow",
        title="The Analytics Pipeline",
        type="theory",
        order=4,
        content="""## The Analytics Pipeline

Every analytics project follows the same five stages. Thinking of your work as a **pipeline** keeps each stage focused and makes it easy to fix a problem at exactly the step where it lives.

### The five stages

1. **Import** — get raw data into R (`read.csv`, `readLines`).
2. **Wrangle** — clean, filter, group, join, and reshape into the shape analysis needs.
3. **Explore** — distributions, outliers, and relationships (the EDA step).
4. **Analyze** — compute statistics, build intervals, fit models, test hypotheses.
5. **Report** — summarize findings and recommend actions.

### Data flows forward

Each stage consumes the previous stage's output:

```r
raw     <- read.csv("sales.csv")            # 1 import
clean   <- raw[!is.na(raw$revenue), ]       # 2 wrangle
summary(clean$revenue)                      # 3 explore
t.test(clean$revenue, mu = 1000)            # 4 analyze
cat("recommendation: keep SKU list")        # 5 report
```

### Iterate, don't go one-way

The pipeline is not rigid. Exploration often reveals a wrangling mistake; a surprise in the report sends you back to the question. Plan to loop.

### Why stage separation pays off

- **Debugging:** an error names its stage, so you look in one place.
- **Reuse:** the same wrangle block can feed three different analyses.
- **Trust:** each stage can be checked on its own before moving on.

Throughout this course the exercises mirror the pipeline: load data, wrangle it, explore it, run statistics, then report.

---

**Next up:** three exercises that put the first stage — importing and inspecting data — into practice."""
    ),
    L(
        id="da-workflow-ex-load",
        course_id="data-analytics-with-r",
        module_id="da-workflow",
        title="Exercise: Load and Inspect a Dataset",
        type="exercise",
        order=5,
        content="""## Exercise: Load and Inspect a Dataset

Write a function `dataset_shape(input)` that receives CSV text with a **header row** and returns the number of **data rows** and the number of **columns**, joined by a space.

### Sample

Input:

```text
name,score
Ada,92
Linus,57
Grace,88
```

Output:

```text
3 2
```

There are three data rows and two columns (`name`, `score`).

### How your code runs

Split the input into lines with `strsplit(input, "\\n")`, drop blank lines, count `length(lines) - 1` rows, and count the columns by splitting the header line on the comma.

### Starter code

```r
dataset_shape <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  rows <- length(lines) - 1
  cols <- length(strsplit(lines[1], ",")[[1]])
  return(paste(rows, cols))
}
```

Good luck!""",
        starter_code='''dataset_shape <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  rows <- length(lines) - 1
  cols <- length(strsplit(lines[1], ",")[[1]])
  return(paste(rows, cols))
}
''',
        test_cases=[
            {"input": "name,score\nAda,92\nLinus,57\nGrace,88\n", "expected_output": "3 2", "description": "Three rows, two columns"},
            {"input": "product,price,qty\nA,10,2\nB,5,3\n", "expected_output": "2 3", "description": "Two rows, three columns"},
            {"input": "x\n1\n2\n3\n", "expected_output": "3 1", "description": "Single column"},
        ],
    ),
    L(
        id="da-workflow-ex-columns",
        course_id="data-analytics-with-r",
        module_id="da-workflow",
        title="Exercise: Column Names",
        type="exercise",
        order=6,
        content="""## Exercise: Column Names

Write a function `column_names(input)` that receives CSV text and returns the **column names** (the header row) joined by spaces.

### Sample

Input:

```text
name,score,grade
Ada,92,A
```

Output:

```text
name score grade
```

### How your code runs

Take the first line of the input, split it on the comma with `strsplit(line, ",")`, and join the pieces with `paste(..., collapse = " ")`.

### Starter code

```r
column_names <- function(input) {
  header <- strsplit(input, "\\n")[[1]][1]
  return(paste(strsplit(header, ",")[[1]], collapse = " "))
}
```

Good luck!""",
        starter_code='''column_names <- function(input) {
  header <- strsplit(input, "\\n")[[1]][1]
  return(paste(strsplit(header, ",")[[1]], collapse = " "))
}
''',
        test_cases=[
            {"input": "name,score,grade\nAda,92,A\n", "expected_output": "name score grade", "description": "Three columns"},
            {"input": "a,b,c\n1,2,3\n", "expected_output": "a b c", "description": "Short names"},
            {"input": "region,sales\nNorth,10\n", "expected_output": "region sales", "description": "Two columns"},
        ],
    ),
    L(
        id="da-workflow-ex-rows",
        course_id="data-analytics-with-r",
        module_id="da-workflow",
        title="Exercise: Rows Above a Threshold",
        type="exercise",
        order=7,
        content="""## Exercise: Rows Above a Threshold

Write a function `rows_above(input)` that receives CSV text (`name,score` rows) and returns the **count of rows whose score is 60 or above**.

### Sample

Input:

```text
name,score
Ada,92
Linus,57
Grace,88
```

Output:

```text
2
```

Ada (92) and Grace (88) pass; Linus (57) does not.

### How your code runs

Drop the header line, split each remaining row on the comma, convert the score with `as.numeric()`, and count rows where the score is `>= 60`.

### Starter code

```r
rows_above <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  data <- lines[-1]
  count <- 0
  for (line in data) {
    parts <- strsplit(line, ",")[[1]]
    score <- as.numeric(parts[length(parts)])
    if (!is.na(score) && score >= 60) {
      count <- count + 1
    }
  }
  return(as.character(count))
}
```

Good luck!""",
        starter_code='''rows_above <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  data <- lines[-1]
  count <- 0
  for (line in data) {
    parts <- strsplit(line, ",")[[1]]
    score <- as.numeric(parts[length(parts)])
    if (!is.na(score) && score >= 60) {
      count <- count + 1
    }
  }
  return(as.character(count))
}
''',
        test_cases=[
            {"input": "name,score\nAda,92\nLinus,57\nGrace,88\n", "expected_output": "2", "description": "Two pass"},
            {"input": "name,score\nPat,60\nSam,59\n", "expected_output": "1", "description": "Boundary at 60"},
            {"input": "name,score\nKim,30\nLee,20\n", "expected_output": "0", "description": "Nobody passes"},
        ],
    ),
    # ── Module 2: Data Wrangling ────────────────────────────────────────
    L(
        id="da-wrangling-verbs",
        course_id="data-analytics-with-r",
        module_id="da-wrangling",
        title="Wrangling Verbs in R",
        type="theory",
        order=1,
        content="""## Wrangling Verbs in R

Data wrangling is the work of getting data into the shape your analysis needs. The **tidyverse** made this intuitive with named verbs; base R achieves the same with subsetting and assignment.

### The tidyverse verbs

| Verb     | What it does          | Base R equivalent                       |
|----------|-----------------------|-----------------------------------------|
| `select` | keep columns          | `df[, c("a", "b")]`                     |
| `filter` | keep rows by condition| `df[df$score >= 60, ]`                  |
| `mutate` | create/modify columns | `df$new <- df$a * 2`                    |
| `arrange`| sort rows             | `df[order(df$score), ]`                 |
| `summarise` | collapse to stats  | `mean(df$score)`                        |

### Filtering rows

Keep only the rows that satisfy a condition:

```r
clean <- df[df$status == "active", ]
top   <- df[df$score > 80 & df$age >= 18, ]
```

### Selecting and creating columns

```r
cols  <- df[, c("name", "score")]
df$margin <- df$revenue - df$cost
```

### Arranging

`order()` returns the indices that sort a column — feed them to `[`:

```r
df[order(df$revenue, decreasing = TRUE), ]
```

### Wrangle in a pipeline

Stage each step so the output of one line feeds the next:

```r
clean <- df[df$status == "active", ]
clean$revenue_per_order <- clean$revenue / clean$orders
clean <- clean[order(-clean$revenue_per_order), ]
head(clean, 5)
```

Clean, filter, and transform *before* you aggregate — garbage in, garbage out applies to every pipeline.

---

**Next up:** grouping rows and aggregating them into summaries."""
    ),
    L(
        id="da-wrangling-group",
        course_id="data-analytics-with-r",
        module_id="da-wrangling",
        title="Grouping and Aggregation",
        type="theory",
        order=2,
        content="""## Grouping and Aggregation

Most analyses compare groups: mean sales by region, total orders by product, churn by plan. This is **split-apply-combine** — split the data by group, apply a function, combine the results.

### tapply: group by one factor

`tapply(values, groups, function)` splits `values` by `groups` and applies the function to each piece:

```r
tapply(df$revenue, df$region, mean)
```

### aggregate: returns a neat table

`aggregate()` is a friendlier sibling that returns a small data frame:

```r
aggregate(revenue ~ region, data = df, FUN = mean)
```

### Manual grouping with a loop

In the sandbox exercises you accumulate sums and counts yourself, keeping **first-appearance order**:

```r
groups <- c(); sums <- c(); counts <- c()
for (line in rows) {
  parts <- strsplit(line, ",")[[1]]
  g <- parts[1]; v <- as.numeric(parts[2])
  idx <- match(g, groups)
  if (is.na(idx)) {
    groups <- c(groups, g); sums <- c(sums, v); counts <- c(counts, 1)
  } else {
    sums[idx] <- sums[idx] + v; counts[idx] <- counts[idx] + 1
  }
}
means <- sums / counts
```

### Choosing the aggregation

- **Count** — `sum(counts)` or `length()` per group.
- **Total** — `sum()` per group.
- **Average** — `mean()` per group.
- **Extreme** — `max()` / `min()` per group.

Aggregating before filtering is a classic bug: removing bad rows *after* the summary leaves their contribution baked in. Filter first, then group.

---

**Next up:** joining separate tables on a shared key."""
    ),
    L(
        id="da-wrangling-join",
        course_id="data-analytics-with-r",
        module_id="da-wrangling",
        title="Joining Tables",
        type="theory",
        order=3,
        content="""## Joining Tables

Real data lives across many tables — customers in one file, orders in another. **Joining** brings them together on a shared **key**.

### merge(): the base R join

```r
merged <- merge(customers, orders, by = "customer_id", all.x = TRUE)
```

- `by` — the key column(s) both tables share.
- `all.x = TRUE` — keep every row from the first table (a *left join*).

### The four join families

| Join        | Keeps                              |
|-------------|------------------------------------|
| inner       | rows matching in **both** tables   |
| left        | all rows from the left table       |
| right       | all rows from the right table      |
| full        | every row from both tables         |

### Matching by hand

In the sandbox exercises you implement a lookup by hand: store keys from the second table, then `match()` the first table's keys into them:

```r
idx <- match(left_ids[i], right_ids)
if (!is.na(idx)) {
  result <- c(result, paste0(left_names[i], ":", right_scores[idx]))
}
```

### Join hygiene

- **Check keys:** duplicate keys multiply rows (one-to-many).
- **Check coverage:** unmatched keys become `NA` in outer joins — decide what that means.
- **Verify cardinality:** row count after an inner join should make sense.

Joins are where silent data loss happens: a wrong key matches nothing and your merged table quietly loses rows. Always compare row counts before and after.

---

**Next up:** reshaping data between wide and long layouts."""
    ),
    L(
        id="da-wrangling-reshape",
        course_id="data-analytics-with-r",
        module_id="da-wrangling",
        title="Reshaping Data",
        type="theory",
        order=4,
        content="""## Reshaping Data

The same data can be laid out **wide** (one row per subject, repeated measurements across columns) or **long** (one row per measurement). Reshaping converts between them.

### Wide vs long

| Layout | Looks like                          | Good for                        |
|--------|-------------------------------------|---------------------------------|
| wide   | `region Q1 Q2 Q3 Q4`                | spreadsheets, many plotting libs|
| long   | `region quarter value`              | grouping, aggregating, ggplot2  |

### Wide to long in base R

A pivot melts repeated columns into key-value pairs:

```r
long <- data.frame(
  region  = rep(df$region, 4),
  quarter = rep(c("Q1", "Q2", "Q3", "Q4"), each = nrow(df)),
  value   = c(df$Q1, df$Q2, df$Q3, df$Q4)
)
```

### Long to wide with aggregate

To go back, aggregate long data over the wide columns:

```r
wide <- aggregate(value ~ region + quarter, data = long, FUN = sum)
```

### Reshaping by hand

In the exercises you often collapse a wide row into one summary — e.g. summing four quarter columns into a yearly total:

```r
parts <- strsplit(line, ",")[[1]]
total <- sum(as.numeric(parts[-1]))
```

### When to reshape

- Need a **per-category total**? Aggregate across the repeated columns.
- Need to **group by quarter**? You need the long form.
- Need to **plot by quarter**? Long form, almost always.

Reshaping mistakes (double-counting, wrong `each`/`rep`) are easy to make and hard to see. Total the numbers before and after reshaping — they must match.

---

**Next up:** three exercises — group extremes, joins, and wide-to-summary reshaping."""
    ),
    L(
        id="da-wrangling-ex-group",
        course_id="data-analytics-with-r",
        module_id="da-wrangling",
        title="Exercise: Maximum by Group",
        type="exercise",
        order=5,
        content="""## Exercise: Maximum by Group

Write a function `max_by_group(input)` that reads `group,value` rows and returns, for each distinct group, its **maximum value** as `group:max` — one per line, in first-appearance order.

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
books:120
toys:150
food:60
```

### How your code runs

Split each line on the comma, look the group up with `match()`, and keep the largest value seen so far. Join the result lines with `paste(..., collapse = "\\n")`.

### Starter code

```r
max_by_group <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  groups <- c()
  maxs <- c()
  for (line in lines) {
    parts <- strsplit(line, ",")[[1]]
    g <- parts[1]
    v <- as.numeric(parts[2])
    idx <- match(g, groups)
    if (is.na(idx)) {
      groups <- c(groups, g)
      maxs <- c(maxs, v)
    } else if (v > maxs[idx]) {
      maxs[idx] <- v
    }
  }
  out <- c()
  for (i in seq_along(groups)) {
    out <- c(out, paste0(groups[i], ":", maxs[i]))
  }
  return(paste(out, collapse = "\\n"))
}
```

Good luck!""",
        starter_code='''max_by_group <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  groups <- c()
  maxs <- c()
  for (line in lines) {
    parts <- strsplit(line, ",")[[1]]
    g <- parts[1]
    v <- as.numeric(parts[2])
    idx <- match(g, groups)
    if (is.na(idx)) {
      groups <- c(groups, g)
      maxs <- c(maxs, v)
    } else if (v > maxs[idx]) {
      maxs[idx] <- v
    }
  }
  out <- c()
  for (i in seq_along(groups)) {
    out <- c(out, paste0(groups[i], ":", maxs[i]))
  }
  return(paste(out, collapse = "\\n"))
}
''',
        test_cases=[
            {"input": "books,120\ntoys,90\nbooks,80\ntoys,150\nfood,60\n", "expected_output": "books:120\ntoys:150\nfood:60", "description": "Three groups"},
            {"input": "a,5\na,3\nb,8\n", "expected_output": "a:5\nb:8", "description": "Two groups"},
            {"input": "solo,42\n", "expected_output": "solo:42", "description": "Single group"},
        ],
    ),
    L(
        id="da-wrangling-ex-join",
        course_id="data-analytics-with-r",
        module_id="da-wrangling",
        title="Exercise: Join Two Tables",
        type="exercise",
        order=6,
        content="""## Exercise: Join Two Tables

Write a function `join_tables(input)` that receives two tables separated by a **blank line**.

- Table 1: `id,name` rows.
- Table 2: `id,score` rows.

Return each name from table 1 with its score from table 2, as `name:score`, joined by spaces, in table 1 order. Rows in table 1 with no matching id are omitted.

### Sample

Input:

```text
1,Ada
2,Linus
3,Grace

1,92
2,57
3,88
```

Output:

```text
Ada:92 Linus:57 Grace:88
```

### How your code runs

Split the input on a double newline (`strsplit(input, "\\n\\n")`) to separate the two tables, store table 2's keys, and `match()` each table-1 key.

### Starter code

```r
join_tables <- function(input) {
  parts <- strsplit(input, "\\n\\n")[[1]]
  left_lines <- strsplit(parts[1], "\\n")[[1]]
  right_lines <- strsplit(parts[2], "\\n")[[1]]
  left_ids <- c()
  left_names <- c()
  for (line in left_lines) {
    if (nchar(trimws(line)) == 0) next
    p <- strsplit(line, ",")[[1]]
    left_ids <- c(left_ids, p[1])
    left_names <- c(left_names, p[2])
  }
  right_ids <- c()
  right_scores <- c()
  for (line in right_lines) {
    if (nchar(trimws(line)) == 0) next
    p <- strsplit(line, ",")[[1]]
    right_ids <- c(right_ids, p[1])
    right_scores <- c(right_scores, as.numeric(p[2]))
  }
  out <- c()
  for (i in seq_along(left_ids)) {
    idx <- match(left_ids[i], right_ids)
    if (!is.na(idx)) {
      out <- c(out, paste0(left_names[i], ":", right_scores[idx]))
    }
  }
  return(paste(out, collapse = " "))
}
```

Good luck!""",
        starter_code='''join_tables <- function(input) {
  parts <- strsplit(input, "\\n\\n")[[1]]
  left_lines <- strsplit(parts[1], "\\n")[[1]]
  right_lines <- strsplit(parts[2], "\\n")[[1]]
  left_ids <- c()
  left_names <- c()
  for (line in left_lines) {
    if (nchar(trimws(line)) == 0) next
    p <- strsplit(line, ",")[[1]]
    left_ids <- c(left_ids, p[1])
    left_names <- c(left_names, p[2])
  }
  right_ids <- c()
  right_scores <- c()
  for (line in right_lines) {
    if (nchar(trimws(line)) == 0) next
    p <- strsplit(line, ",")[[1]]
    right_ids <- c(right_ids, p[1])
    right_scores <- c(right_scores, as.numeric(p[2]))
  }
  out <- c()
  for (i in seq_along(left_ids)) {
    idx <- match(left_ids[i], right_ids)
    if (!is.na(idx)) {
      out <- c(out, paste0(left_names[i], ":", right_scores[idx]))
    }
  }
  return(paste(out, collapse = " "))
}
''',
        test_cases=[
            {"input": "1,Ada\n2,Linus\n3,Grace\n\n1,92\n2,57\n3,88\n", "expected_output": "Ada:92 Linus:57 Grace:88", "description": "All keys match"},
            {"input": "1,Ada\n2,Linus\n\n1,92\n2,57\n", "expected_output": "Ada:92 Linus:57", "description": "Two pairs"},
            {"input": "1,Ada\n2,Linus\n3,Grace\n\n1,92\n3,88\n", "expected_output": "Ada:92 Grace:88", "description": "One key missing"},
        ],
    ),
    L(
        id="da-wrangling-ex-reshape",
        course_id="data-analytics-with-r",
        module_id="da-wrangling",
        title="Exercise: Quarterly Totals",
        type="exercise",
        order=7,
        content="""## Exercise: Quarterly Totals

Write a function `quarterly_total(input)` that reads CSV text with a header `region,Q1,Q2,Q3,Q4` and returns, for each region, its **yearly total** as `region:total`, one per line, in first-appearance order.

### Sample

Input:

```text
region,Q1,Q2,Q3,Q4
North,10,20,30,40
South,5,10,15,20
```

Output:

```text
North:100
South:50
```

### How your code runs

Drop the header, split each row on the comma, sum the four quarter values with `sum(as.numeric(parts[-1]))`, and accumulate per region.

### Starter code

```r
quarterly_total <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  data <- lines[-1]
  regions <- c()
  totals <- c()
  for (line in data) {
    parts <- strsplit(line, ",")[[1]]
    region <- parts[1]
    total <- sum(as.numeric(parts[-1]))
    idx <- match(region, regions)
    if (is.na(idx)) {
      regions <- c(regions, region)
      totals <- c(totals, total)
    } else {
      totals[idx] <- totals[idx] + total
    }
  }
  out <- c()
  for (i in seq_along(regions)) {
    out <- c(out, paste0(regions[i], ":", totals[i]))
  }
  return(paste(out, collapse = "\\n"))
}
```

Good luck!""",
        starter_code='''quarterly_total <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  data <- lines[-1]
  regions <- c()
  totals <- c()
  for (line in data) {
    parts <- strsplit(line, ",")[[1]]
    region <- parts[1]
    total <- sum(as.numeric(parts[-1]))
    idx <- match(region, regions)
    if (is.na(idx)) {
      regions <- c(regions, region)
      totals <- c(totals, total)
    } else {
      totals[idx] <- totals[idx] + total
    }
  }
  out <- c()
  for (i in seq_along(regions)) {
    out <- c(out, paste0(regions[i], ":", totals[i]))
  }
  return(paste(out, collapse = "\\n"))
}
''',
        test_cases=[
            {"input": "region,Q1,Q2,Q3,Q4\nNorth,10,20,30,40\nSouth,5,10,15,20\n", "expected_output": "North:100\nSouth:50", "description": "Two regions"},
            {"input": "region,Q1,Q2,Q3,Q4\nA,1,1,1,1\nB,2,2,2,2\n", "expected_output": "A:4\nB:8", "description": "Repeated rows"},
            {"input": "region,Q1,Q2,Q3,Q4\nWest,10,10,10,10\n", "expected_output": "West:40", "description": "Single region"},
        ],
    ),
    # ── Module 3: Exploratory Data Analysis ─────────────────────────────
    L(
        id="da-eda-distributions",
        course_id="data-analytics-with-r",
        module_id="da-eda",
        title="Exploring Distributions",
        type="theory",
        order=1,
        content="""## Exploring Distributions

A **distribution** describes how often each value of a variable occurs. Understanding it is the heart of exploratory data analysis (EDA).

### The three questions about any distribution

1. **Where is the center?** — the typical value (`mean`, `median`).
2. **How spread out is it?** — `sd`, range, IQR.
3. **What is the shape?** — symmetric, skewed, peaked, multi-modal.

### Look before you summarize

A histogram reveals what numbers alone hide:

```r
hist(df$revenue, breaks = 20, col = "lightblue", main = "Revenue")
```

- Symmetric distributions look like a bell around the center.
- **Right-skewed** distributions have a long tail of big values; the mean sits above the median.
- Two peaks suggest two subpopulations mixed together.

### The summary() shortcut

```r
summary(df$revenue)
```

gives min, 1st quartile, median, mean, 3rd quartile, max — enough to sketch any distribution quickly.

### Distribution checks catch data problems

- A surprise peak at zero often means "not measured", not "zero".
- A long tail may hide a handful of extreme (or erroneous) values.
- A bimodal shape means you should analyze groups separately.

### Always pair number and shape

The mean of `c(1, 2, 3, 4, 5, 6, 7, 8, 9, 100)` is 14.5 — but a histogram shows that's a lie about the typical value. Distributions force you to see the whole picture, not just the summary.

---

**Next up:** spotting and handling the outliers that distributions reveal."""
    ),
    L(
        id="da-eda-outliers",
        course_id="data-analytics-with-r",
        module_id="da-eda",
        title="Detecting Outliers",
        type="theory",
        order=2,
        content="""## Detecting Outliers

An **outlier** is a value that stands apart from the rest. Outliers can be real signal (a blockbuster sale) or data errors (a misplaced decimal). EDA is where you decide which.

### The IQR fence rule

The box plot's rule flags values outside the fences:

```r
q1    <- quantile(x, 0.25)
q3    <- quantile(x, 0.75)
iqr   <- q3 - q1
lower <- q1 - 1.5 * iqr
upper <- q3 + 1.5 * iqr
outliers <- x[x < lower | x > upper]
```

Anything below `lower` or above `upper` is drawn as a dot beyond the whiskers.

### Look with a box plot

```r
boxplot(df$revenue, horizontal = TRUE, main = "Revenue")
```

One glance shows the median line, the box (middle 50%), the whiskers, and any dots beyond.

### What to do with outliers

| Situation                     | Action                                    |
|-------------------------------|-------------------------------------------|
| Typo / sensor error           | fix or drop the value                     |
| Real but rare (a mega-deal)   | keep it, report it separately             |
| Extreme value skewing means   | prefer the median or use a robust measure |

### Don't delete silently

Removing outliers changes the answer. Document how many you removed and why, and — for a sanity check — compute key statistics with and without them.

### The z-score alternative

A value's z-score is how many standard deviations it is from the mean:

```r
z <- (x - mean(x)) / sd(x)   # |z| >= 3 is a common cutoff
```

The IQR rule is more robust because it ignores extreme values when defining the fences, whereas the mean and `sd` used by z-scores are themselves pulled by outliers.

---

**Next up:** measuring how two variables move together — correlation."""
    ),
    L(
        id="da-eda-correlation",
        course_id="data-analytics-with-r",
        module_id="da-eda",
        title="Correlation Between Variables",
        type="theory",
        order=3,
        content="""## Correlation Between Variables

**Correlation** measures how two numeric variables move together. It is a first probe for relationships before you model them.

### The correlation coefficient

`cor(x, y)` returns **Pearson's r**, always between -1 and 1:

```r
cor(df$ad_spend, df$revenue)
```

- `r` near **+1** — strong positive: as one rises, so does the other.
- `r` near **-1** — strong negative: as one rises, the other falls.
- `r` near **0** — no linear relationship.

### Always plot the scatter too

```r
plot(df$ad_spend, df$revenue, pch = 19, col = "steelblue")
```

Correlation only captures **linear** patterns. A perfect U-shaped curve can have `r = 0` while the relationship is clearly real. The scatter reveals curves and clusters that `r` cannot.

### Sensitivity to outliers

A single extreme point can dominate `r`. Check the scatter before trusting the number.

### Correlation is not causation

Ice-cream sales and drowning incidents are strongly correlated — because both rise with warm weather. Correlated variables may both be driven by a third cause, or the direction of influence may run opposite to what you assume.

### Correlation vs slope

Correlation and regression slope move together (both positive or both negative), but they are not the same: slope depends on the units and scale of the variables, while `r` is unit-free. You'll meet the slope in the statistics module.

---

**Next up:** pulling everything into a compact statistical summary of the data."""
    ),
    L(
        id="da-eda-summary",
        course_id="data-analytics-with-r",
        module_id="da-eda",
        title="Summary Statistics in Practice",
        type="theory",
        order=4,
        content="""## Summary Statistics in Practice

Summary statistics condense a whole column into a few numbers. Used well, they are a fast EDA pass over many variables at once.

### The five-number summary

`summary()` prints min, 1st quartile, median, mean, 3rd quartile, and max:

```r
summary(df$price)
```

| Statistic | Question it answers        |
|-----------|----------------------------|
| min / max | the range of the data      |
| median    | the middle (robust center) |
| mean      | the arithmetic average     |
| Q1 / Q3   | spread of the middle 50%   |

### Summarize many columns at once

```r
summary(df[, c("price", "quantity", "revenue")])
```

One command summarizes your whole numeric table — a fast scan for weird values, missing data, and scale differences.

### Summaries by group

Averages hide differences between groups. Compare them explicitly:

```r
tapply(df$revenue, df$region, summary)
```

Now you can see, at a glance, that the West region's median revenue is half the East's — a fact the overall mean buries.

### Sanity-check with summaries

- A **mean below the median** suggests left skew; above suggests right skew.
- A **max far above Q3** hints at outliers worth investigating.
- **NA counts** from `sum(is.na(x))` tell you how much data is missing.

### From summary to action

Summaries are not the end — they are the beginning. A suspicious summary sends you back to the plot; a striking one sends you forward to the statistics. Keep the loop tight.

---

**Next up:** three exercises — spread, correlation, and a full profile report."""
    ),
    L(
        id="da-eda-ex-spread",
        course_id="data-analytics-with-r",
        module_id="da-eda",
        title="Exercise: Measures of Spread",
        type="exercise",
        order=5,
        content="""## Exercise: Measures of Spread

Write a function `spread_measures(input)` that reads numbers (one per line) and returns three measures of spread joined by spaces, each rounded to 2 decimal places: the **range** (max - min), the **variance**, and the **standard deviation**.

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
4 2.5 1.58
```

### How your code runs

Convert the lines with `as.numeric()`, drop `NA`s, then compute `max(x) - min(x)`, `var(x)`, and `sd(x)`. Round each with `round(x, 2)` and join with `paste()`.

### Starter code

```r
spread_measures <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  rng <- round(max(nums) - min(nums), 2)
  varv <- round(var(nums), 2)
  sdv <- round(sd(nums), 2)
  return(paste(rng, varv, sdv))
}
```

Good luck!""",
        starter_code='''spread_measures <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  rng <- round(max(nums) - min(nums), 2)
  varv <- round(var(nums), 2)
  sdv <- round(sd(nums), 2)
  return(paste(rng, varv, sdv))
}
''',
        test_cases=[
            {"input": "1\n2\n3\n4\n5\n", "expected_output": "4 2.5 1.58", "description": "Sequential values"},
            {"input": "4\n8\n15\n16\n23\n42\n", "expected_output": "38 182 13.49", "description": "Classic data set"},
            {"input": "10\n10\n10\n", "expected_output": "0 0 0", "description": "No spread"},
        ],
    ),
    L(
        id="da-eda-ex-corr",
        course_id="data-analytics-with-r",
        module_id="da-eda",
        title="Exercise: Correlation Between Columns",
        type="exercise",
        order=6,
        content="""## Exercise: Correlation Between Columns

Write a function `column_corr(input)` that reads CSV text with a header `x,y` and returns the **correlation** between the two columns, rounded to 2 decimal places.

### Sample

Input:

```text
x,y
1,2
2,4
3,6
4,8
5,10
```

Output:

```text
1
```

### How your code runs

Drop the header line, split each row on the comma, collect the two numeric columns, and compute `cor(xs, ys)`.

### Starter code

```r
column_corr <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  data <- lines[-1]
  xs <- c()
  ys <- c()
  for (line in data) {
    parts <- strsplit(line, ",")[[1]]
    xs <- c(xs, as.numeric(parts[1]))
    ys <- c(ys, as.numeric(parts[2]))
  }
  return(as.character(round(cor(xs, ys), 2)))
}
```

Good luck!""",
        starter_code='''column_corr <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  data <- lines[-1]
  xs <- c()
  ys <- c()
  for (line in data) {
    parts <- strsplit(line, ",")[[1]]
    xs <- c(xs, as.numeric(parts[1]))
    ys <- c(ys, as.numeric(parts[2]))
  }
  return(as.character(round(cor(xs, ys), 2)))
}
''',
        test_cases=[
            {"input": "x,y\n1,2\n2,4\n3,6\n4,8\n5,10\n", "expected_output": "1", "description": "Perfect positive"},
            {"input": "x,y\n1,5\n2,4\n3,3\n4,2\n5,1\n", "expected_output": "-1", "description": "Perfect negative"},
            {"input": "x,y\n1,3\n2,1\n3,5\n4,2\n5,4\n", "expected_output": "0.3", "description": "Weak relationship"},
        ],
    ),
    L(
        id="da-eda-ex-profile",
        course_id="data-analytics-with-r",
        module_id="da-eda",
        title="Exercise: Column Profile Report",
        type="exercise",
        order=7,
        content="""## Exercise: Column Profile Report

Write a function `column_profile(input)` that reads CSV text with a two-column header (e.g. `height,weight`) and returns a two-line profile, one line per column, in the format:

```text
name:min=VALUE mean=VALUE max=VALUE
```

Each statistic is rounded to 2 decimal places.

### Sample

Input:

```text
height,weight
150,50
160,55
170,60
180,70
```

Output:

```text
height:min=150 mean=165 max=180
weight:min=50 mean=58.75 max=70
```

### How your code runs

Use the header names for the labels, then compute `min()`, `mean()`, and `max()` for each numeric column. Join the two lines with `paste(line1, line2, sep = "\\n")`.

### Starter code

```r
column_profile <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  header <- strsplit(lines[1], ",")[[1]]
  data <- lines[-1]
  a <- c()
  b <- c()
  for (line in data) {
    parts <- strsplit(line, ",")[[1]]
    a <- c(a, as.numeric(parts[1]))
    b <- c(b, as.numeric(parts[2]))
  }
  line1 <- paste0(header[1], ":min=", round(min(a), 2), " mean=", round(mean(a), 2), " max=", round(max(a), 2))
  line2 <- paste0(header[2], ":min=", round(min(b), 2), " mean=", round(mean(b), 2), " max=", round(max(b), 2))
  return(paste(line1, line2, sep = "\\n"))
}
```

Good luck!""",
        starter_code='''column_profile <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  header <- strsplit(lines[1], ",")[[1]]
  data <- lines[-1]
  a <- c()
  b <- c()
  for (line in data) {
    parts <- strsplit(line, ",")[[1]]
    a <- c(a, as.numeric(parts[1]))
    b <- c(b, as.numeric(parts[2]))
  }
  line1 <- paste0(header[1], ":min=", round(min(a), 2), " mean=", round(mean(a), 2), " max=", round(max(a), 2))
  line2 <- paste0(header[2], ":min=", round(min(b), 2), " mean=", round(mean(b), 2), " max=", round(max(b), 2))
  return(paste(line1, line2, sep = "\\n"))
}
''',
        test_cases=[
            {"input": "height,weight\n150,50\n160,55\n170,60\n180,70\n", "expected_output": "height:min=150 mean=165 max=180\nweight:min=50 mean=58.75 max=70", "description": "Two clean columns"},
            {"input": "score,time\n70,1.5\n80,2\n90,2.5\n", "expected_output": "score:min=70 mean=80 max=90\ntime:min=1.5 mean=2 max=2.5", "description": "Decimals in second column"},
            {"input": "x,y\n1,10\n2,20\n", "expected_output": "x:min=1 mean=1.5 max=2\ny:min=10 mean=15 max=20", "description": "Two rows"},
        ],
    ),
    # ── Module 4: Statistical Analysis ──────────────────────────────────
    L(
        id="da-statistics-sampling",
        course_id="data-analytics-with-r",
        module_id="da-statistics",
        title="Sampling from Data",
        type="theory",
        order=1,
        content="""## Sampling from Data

Analyzing a full population is expensive or impossible, so analysts work with **samples** and generalize to the population. Sampling is where that generalization starts.

### Drawing a sample in R

```r
set.seed(7)
rows <- sample(1:nrow(df), size = 100)
sample_df <- df[rows, ]
```

`sample()` picks rows at random. `set.seed()` makes the pick reproducible.

### Why sample size matters

A larger sample gives a more precise estimate of the population. The **standard error** captures this — it shrinks as the sample grows:

```r
se <- sd(x) / sqrt(length(x))
```

Double the sample size and the standard error drops by a factor of `sqrt(2)`.

### A sample must be representative

A sample that over-represents one group quietly lies. Classic failure modes:

- **Convenience sampling** — asking whoever is nearby, not whoever is relevant.
- **Self-selection** — only the most interested people respond.
- **Non-response** — the people who don't answer differ from those who do.

### Bias beats noise

A large biased sample is worse than a small unbiased one — you get a precise estimate of the wrong number. Random selection is the guard against systematic bias.

### The honest report

Every analysis that generalizes from a sample should say so: *"n = 120 orders sampled from 3,000"* tells the reader exactly how much weight the numbers can carry.

---

**Next up:** turning a sample into a range of plausible values — confidence intervals."""
    ),
    L(
        id="da-statistics-intervals",
        course_id="data-analytics-with-r",
        module_id="da-statistics",
        title="Confidence Intervals",
        type="theory",
        order=2,
        content="""## Confidence Intervals

A sample mean is a single guess at the population mean. A **confidence interval** turns that guess into a range of plausible values.

### The ingredients

```r
n  <- length(x)
m  <- mean(x)
se <- sd(x) / sqrt(n)      # standard error
margin <- 1.96 * se        # 95% margin of error
lower <- m - margin
upper <- m + margin
```

### What the interval means

If you repeated the sampling many times and built a 95% interval each time, about 95% of those intervals would contain the true population mean. It is **not** "95% of the data lies here" — it is a statement about the estimation procedure, not the data.

### The 1.96 multiplier

For a normal-ish distribution, 95% of a distribution sits within 1.96 standard deviations of its center. The multiplier changes with the confidence level:

| Confidence | Multiplier |
|------------|------------|
| 90%        | 1.645      |
| 95%        | 1.96       |
| 99%        | 2.576      |

### Wider data, wider interval

More spread (`sd`) widens the interval; more data (`n`) narrows it. The interval summarizes both the uncertainty and how much the sample can tell you.

### Interval vs single number

A point estimate hides uncertainty; an interval exposes it. "Mean order value is $48" sounds definitive. "Mean order value is $48, with a 95% interval of $41-$55" tells a manager how much to trust the number.

---

**Next up:** deciding whether the data contradicts a claim — hypothesis testing."""
    ),
    L(
        id="da-statistics-tests",
        course_id="data-analytics-with-r",
        module_id="da-statistics",
        title="Hypothesis Testing Basics",
        type="theory",
        order=3,
        content="""## Hypothesis Testing Basics

A **hypothesis test** formalizes the question *"is the difference we see real, or could it be chance?"*

### The two hypotheses

- **Null hypothesis (H0):** nothing special — the parameter equals a stated value.
- **Alternative hypothesis (Ha):** the parameter differs from that value.

For example: a store claims the average order is $60. H0 says mean = 60; Ha says it isn't.

### The test statistic

Measure how far the data sits from H0 in standard-error units:

```r
z <- (mean(x) - claimed_value) / (sd(x) / sqrt(length(x)))
```

A big `|z|` means the data is far from the claim relative to its own uncertainty — evidence against H0.

### The p-value idea

The p-value is the probability of seeing data this extreme if H0 were true. Small p-value → surprising under H0 → evidence against it.

### A working decision rule

In this course's exercises you use a simple threshold: if `|z| >= 2` (roughly a 5% threshold for the z-test), call the difference **"reject"** the claim; otherwise **"not enough evidence"**.

```r
if (abs(z) >= 2) {
  verdict <- "reject"
} else {
  verdict <- "not enough evidence"
}
```

### What tests can't tell you

- A non-significant result is not proof H0 is true — just weak evidence.
- A significant result does not mean the effect is practically important.
- Small samples rarely reject; huge samples reject everything — size matters when reading tests.

---

**Next up:** fitting a straight line to two variables — regression basics."""
    ),
    L(
        id="da-statistics-regression",
        course_id="data-analytics-with-r",
        module_id="da-statistics",
        title="Regression Basics",
        type="theory",
        order=4,
        content="""## Regression Basics

**Regression** fits a line that best describes how one variable depends on another. It turns correlation into a usable model.

### The regression line

```r
fit <- lm(y ~ x, data = df)
coef(fit)
```

produces an **intercept** (the predicted `y` when `x = 0`) and a **slope** (the change in `y` for a one-unit increase in `x`).

### Slope by hand

You do not need `lm()` to get the slope for a simple two-variable model:

```r
slope <- cov(x, y) / var(x)
intercept <- mean(y) - slope * mean(x)
```

The slope is the covariance scaled by the variance of `x`. Prediction is then:

```r
predicted <- intercept + slope * new_x
```

### Interpreting the slope

For ad spend and revenue, a slope of `3.2` means each additional dollar of ad spend is associated with about $3.20 more revenue in the data.

### Reading residuals

The difference between the actual `y` and the predicted `y` is the **residual**. Small residuals mean the line fits well; a systematic pattern in residuals (curves, fans) means a straight line is the wrong model.

### Regression and correlation

They are cousins: both describe linear association, and their signs always match. But slope is in the variables' units (`$` per `$`), while correlation `r` is unit-free between -1 and 1.

### The caution

A strong fitted line on observed data is not proof of causation, and predicting far outside the observed `x` range (extrapolation) is risky.

---

**Next up:** three exercises — standard error, a group-vs-threshold test, and regression slope."""
    ),
    L(
        id="da-statistics-ex-se",
        course_id="data-analytics-with-r",
        module_id="da-statistics",
        title="Exercise: Standard Error",
        type="exercise",
        order=5,
        content="""## Exercise: Standard Error

Write a function `standard_error(input)` that reads numbers (one per line) and returns the **mean** and the **standard error** (`sd(x) / sqrt(n)`), joined by a space, each rounded to 2 decimal places.

### Sample

Input:

```text
4
8
15
16
23
42
```

Output:

```text
18 5.51
```

Mean = 18; standard error = `sd / sqrt(6)` = 5.51.

### How your code runs

Drop `NA`s, then compute `mean(x)` and `sd(x) / sqrt(length(x))`. Round both with `round(x, 2)`.

### Starter code

```r
standard_error <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  n <- length(nums)
  m <- round(mean(nums), 2)
  se <- round(sd(nums) / sqrt(n), 2)
  return(paste(m, se))
}
```

Good luck!""",
        starter_code='''standard_error <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  n <- length(nums)
  m <- round(mean(nums), 2)
  se <- round(sd(nums) / sqrt(n), 2)
  return(paste(m, se))
}
''',
        test_cases=[
            {"input": "4\n8\n15\n16\n23\n42\n", "expected_output": "18 5.51", "description": "Classic data set"},
            {"input": "1\n2\n3\n4\n5\n", "expected_output": "3 0.71", "description": "Sequential values"},
            {"input": "10\n10\n10\n", "expected_output": "10 0", "description": "No spread"},
        ],
    ),
    L(
        id="da-statistics-ex-test",
        course_id="data-analytics-with-r",
        module_id="da-statistics",
        title="Exercise: Compare a Group to a Threshold",
        type="exercise",
        order=6,
        content="""## Exercise: Compare a Group to a Threshold

Write a function `group_vs_threshold(input)` that receives a **threshold** on the first line and a column of numbers below it, and tests whether the group differs from the threshold.

Compute the z-statistic `z = (mean - threshold) / (sd / sqrt(n))`. If `abs(z) >= 2` return `"reject"`, otherwise return `"not enough evidence"`.

### Sample

Input:

```text
60
70
72
74
76
78
```

Output:

```text
reject
```

### How your code runs

The mean (74) is far from the threshold (60) relative to the standard error, so the claim is rejected.

### Starter code

```r
group_vs_threshold <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  threshold <- as.numeric(lines[1])
  nums <- as.numeric(lines[-1])
  nums <- nums[!is.na(nums)]
  n <- length(nums)
  m <- mean(nums)
  se <- sd(nums) / sqrt(n)
  z <- (m - threshold) / se
  if (abs(z) >= 2) {
    return("reject")
  }
  return("not enough evidence")
}
```

Good luck!""",
        starter_code='''group_vs_threshold <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  threshold <- as.numeric(lines[1])
  nums <- as.numeric(lines[-1])
  nums <- nums[!is.na(nums)]
  n <- length(nums)
  m <- mean(nums)
  se <- sd(nums) / sqrt(n)
  z <- (m - threshold) / se
  if (abs(z) >= 2) {
    return("reject")
  }
  return("not enough evidence")
}
''',
        test_cases=[
            {"input": "60\n70\n72\n74\n76\n78\n", "expected_output": "reject", "description": "Clearly above threshold"},
            {"input": "50\n50\n51\n52\n", "expected_output": "not enough evidence", "description": "Small deviation"},
            {"input": "70\n65\n68\n70\n72\n75\n", "expected_output": "not enough evidence", "description": "Mean equals threshold"},
        ],
    ),
    L(
        id="da-statistics-ex-reg",
        course_id="data-analytics-with-r",
        module_id="da-statistics",
        title="Exercise: Regression Slope",
        type="exercise",
        order=7,
        content="""## Exercise: Regression Slope

Write a function `regression_slope(input)` that reads CSV text with a header `x,y` and returns the **regression slope** of `y` on `x`, rounded to 2 decimal places.

Slope = `cov(x, y) / var(x)`.

### Sample

Input:

```text
x,y
1,2
2,4
3,6
4,8
5,10
```

Output:

```text
2
```

### How your code runs

Drop the header, collect the two columns, then compute `cov(xs, ys) / var(xs)`.

### Starter code

```r
regression_slope <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  data <- lines[-1]
  xs <- c()
  ys <- c()
  for (line in data) {
    parts <- strsplit(line, ",")[[1]]
    xs <- c(xs, as.numeric(parts[1]))
    ys <- c(ys, as.numeric(parts[2]))
  }
  slope <- cov(xs, ys) / var(xs)
  return(as.character(round(slope, 2)))
}
```

Good luck!""",
        starter_code='''regression_slope <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  data <- lines[-1]
  xs <- c()
  ys <- c()
  for (line in data) {
    parts <- strsplit(line, ",")[[1]]
    xs <- c(xs, as.numeric(parts[1]))
    ys <- c(ys, as.numeric(parts[2]))
  }
  slope <- cov(xs, ys) / var(xs)
  return(as.character(round(slope, 2)))
}
''',
        test_cases=[
            {"input": "x,y\n1,2\n2,4\n3,6\n4,8\n5,10\n", "expected_output": "2", "description": "Rising line"},
            {"input": "x,y\n1,5\n2,4\n3,3\n4,2\n5,1\n", "expected_output": "-1", "description": "Falling line"},
            {"input": "x,y\n0,1\n2,5\n4,9\n6,13\n8,17\n", "expected_output": "2", "description": "Offset line"},
        ],
    ),
    # ── Module 5: Analytics Project ─────────────────────────────────────
    L(
        id="da-project-choose",
        course_id="data-analytics-with-r",
        module_id="da-project",
        title="Choosing a Dataset",
        type="theory",
        order=1,
        content="""## Choosing a Dataset

A good analysis starts with a dataset that can actually answer the question. Choosing well saves hours of forcing the wrong data through the pipeline.

### Start from the question, then find data

Write the question first, list what you need to measure, then hunt for data with those columns. Working backwards from "here's a cool file" usually ends in analysis that answers nothing.

### The checklist

- **Relevant** — does it contain the variables in your question?
- **Granular** — is the level of detail right (per order, not per quarter)?
- **Recent** — is the time window the question is about?
- **Complete** — how much is missing, and does missingness cluster?
- **Trustworthy** — who collected it, and how?

### Tidy vs raw

Keep raw data untouched in `data/` and write scripts that transform it. If a cleaning decision is wrong, you can re-run the pipeline — but only if the original is still there.

### Small beats big for learning

For practice, a small, clean dataset (a few dozen rows) is better than a giant messy one. You can see every value and check your work by hand before scaling up to real-world size.

### Document the source

Note where the data came from, when you got it, and any assumptions. A future reader (or auditor) needs to reproduce both your data and your logic.

---

**Next up:** running a disciplined analysis once the dataset is chosen."""
    ),
    L(
        id="da-project-analyze",
        course_id="data-analytics-with-r",
        module_id="da-project",
        title="Analyzing with a Plan",
        type="theory",
        order=2,
        content="""## Analyzing with a Plan

An analysis without a plan wanders. Following the pipeline — import, wrangle, explore, analyze, report — keeps every step purposeful.

### Write the plan as comments first

```r
# 1. Import sales data
# 2. Drop rows with missing revenue
# 3. Compare mean revenue by region
# 4. Recommend the region to double down on
```

Filling in the code under each comment is far easier than writing free-form.

### Sanity-check at every stage

- After import: do `dim()` and `names()` match expectations?
- After wrangle: did row counts change for the reason you expected?
- After analyze: are the numbers in a plausible range?

A single `head()` at the right moment catches most disasters early.

### Keep steps auditable

Prefer many small, clearly named steps over one giant expression. If a result surprises you, you can bisect: run the pipeline up to each stage and see where the surprise enters.

### Compare, don't just describe

Descriptions ("mean is 42") rarely drive decisions. Comparisons do: "mean is 42, vs 30 for the other group". Build every analysis around a comparison that maps to the question.

### Record decisions

Note the judgment calls: which threshold you used, which outliers you kept, which metric you chose. Analysts are judged on the journey as much as the destination.

---

**Next up:** turning analysis results into a report that people can act on."""
    ),
    L(
        id="da-project-report",
        course_id="data-analytics-with-r",
        module_id="da-project",
        title="Reporting Recommendations",
        type="theory",
        order=3,
        content="""## Reporting Recommendations

Analysis is finished when someone can act on it. The report is the bridge between numbers and decisions.

### Structure for busy readers

1. **The bottom line first** — the recommendation in one sentence.
2. **The evidence** — the numbers and comparisons that support it.
3. **The caveats** — limitations and what could change the answer.

### Write the answer, then the method

Managers want the recommendation, then enough method to trust it. Reserve deep technical detail for an appendix.

### Make numbers concrete

- "Mean order value rose 12%" is good.
- "Mean order value rose 12%, from $42 to $47, driven by the West region" is actionable.
- Pair every claim with its evidence: *"West mean $47 vs East $38 (n = 240 orders, 95% CI $44-$50)"*.

### State assumptions

Every analysis rests on assumptions — the metric chosen, the outliers removed, the time window. List them so a decision maker can see what the answer depends on.

### A recommendation template

```text
Recommendation: <do this>
Because: <statistic> compared with <comparison>
Caveat: <what could change the answer>
```

### Honesty over polish

A report that buries a weak result is worse than no report. If the data says "not enough evidence", say so — a wrong confident answer costs more than an honest uncertain one.

---

**Next up:** the pitfalls that quietly ruin otherwise good analyses."""
    ),
    L(
        id="da-project-pitfalls",
        course_id="data-analytics-with-r",
        module_id="da-project",
        title="Common Pitfalls",
        type="theory",
        order=4,
        content="""## Common Pitfalls

Most analytics failures are not math errors — they are judgment errors that survive perfect arithmetic. Knowing them is half the defense.

### Cleaning traps

- **Aggregating before filtering** — bad rows baked into group totals.
- **Ignoring NAs** — `mean(x)` silently returns `NA`; always decide the missing policy.
- **Silent outliers** — deleting values without recording it changes every downstream number.

### Interpretation traps

- **Correlation is not causation** — a third variable, or reverse direction, may explain the link.
- **Over-generalizing samples** — a convenience sample can't speak for a population.
- **Extrapolation** — a line fitted on 0-10 predicts poorly at 100.

### The aggregate fallacy

Averages hide splits. Two groups with opposite trends can combine into a flat overall mean. Always compare subgroups before trusting the headline number.

### Confirmation bias

We favor results that fit expectations. Guard by pre-committing to the decision rule — write down *before* seeing results what evidence would change your conclusion.

### Numeric precision theater

Reporting "mean = 42.1379" when the data is noisy is false confidence. Round sensibly and report uncertainty (`42`, 95% CI `39-45`).

### The fix is process

Scripts, seeds, sanity checks, and written assumptions don't make analysis glamorous — they make it correct and repeatable.

---

**Next up:** the capstone exercises — a segment comparison, imputation, and a final recommendation."""
    ),
    L(
        id="da-project-ex-segment",
        course_id="data-analytics-with-r",
        module_id="da-project",
        title="Exercise: Segment Comparison",
        type="exercise",
        order=5,
        content="""## Exercise: Segment Comparison

Write a function `segment_compare(input)` that reads `segment,value` rows and returns:

1. One line per distinct segment: `segment:mean` (mean rounded to 2 decimal places), in first-appearance order.
2. A final line `best:SEGMENT` naming the segment with the highest mean.

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
best:B
```

### How your code runs

Accumulate sums and counts per segment, compute the rounded means, then use `which.max()` on the means to find the best segment (ties go to the first appearance).

### Starter code

```r
segment_compare <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  segs <- c()
  sums <- c()
  counts <- c()
  for (line in lines) {
    parts <- strsplit(line, ",")[[1]]
    s <- parts[1]
    v <- as.numeric(parts[2])
    idx <- match(s, segs)
    if (is.na(idx)) {
      segs <- c(segs, s)
      sums <- c(sums, v)
      counts <- c(counts, 1)
    } else {
      sums[idx] <- sums[idx] + v
      counts[idx] <- counts[idx] + 1
    }
  }
  means <- round(sums / counts, 2)
  out <- c()
  for (i in seq_along(segs)) {
    out <- c(out, paste0(segs[i], ":", means[i]))
  }
  out <- c(out, paste0("best:", segs[which.max(means)]))
  return(paste(out, collapse = "\\n"))
}
```

Good luck!""",
        starter_code='''segment_compare <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  segs <- c()
  sums <- c()
  counts <- c()
  for (line in lines) {
    parts <- strsplit(line, ",")[[1]]
    s <- parts[1]
    v <- as.numeric(parts[2])
    idx <- match(s, segs)
    if (is.na(idx)) {
      segs <- c(segs, s)
      sums <- c(sums, v)
      counts <- c(counts, 1)
    } else {
      sums[idx] <- sums[idx] + v
      counts[idx] <- counts[idx] + 1
    }
  }
  means <- round(sums / counts, 2)
  out <- c()
  for (i in seq_along(segs)) {
    out <- c(out, paste0(segs[i], ":", means[i]))
  }
  out <- c(out, paste0("best:", segs[which.max(means)]))
  return(paste(out, collapse = "\\n"))
}
''',
        test_cases=[
            {"input": "A,10\nB,20\nA,30\nB,40\n", "expected_output": "A:20\nB:30\nbest:B", "description": "Two segments"},
            {"input": "X,5\nX,5\nX,5\nY,1\nY,1\nY,1\n", "expected_output": "X:5\nY:1\nbest:X", "description": "Clear winner"},
            {"input": "solo,42\n", "expected_output": "solo:42\nbest:solo", "description": "Single segment"},
        ],
    ),
    L(
        id="da-project-ex-impute",
        course_id="data-analytics-with-r",
        module_id="da-project",
        title="Exercise: Missing Value Imputation",
        type="exercise",
        order=6,
        content="""## Exercise: Missing Value Imputation

Write a function `impute_mean(input)` that reads a column of numbers where some lines may be `NA` (or blank) and returns the **imputed column**: every missing value replaced by the mean of the non-missing values, rounded to 2 decimal places. Output the values joined by spaces.

### Sample

Input:

```text
4
NA
8
```

Output:

```text
4 6 8
```

The mean of `4` and `8` is `6`, so the `NA` becomes `6`.

### How your code runs

Convert with `as.numeric()` (failed lines become `NA`), compute `mean(nums, na.rm = TRUE)` rounded to 2, replace missing entries, then join with `paste(round(nums, 2), collapse = " ")`.

### Starter code

```r
impute_mean <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  m <- round(mean(nums, na.rm = TRUE), 2)
  nums[is.na(nums)] <- m
  return(paste(round(nums, 2), collapse = " "))
}
```

Good luck!""",
        starter_code='''impute_mean <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  m <- round(mean(nums, na.rm = TRUE), 2)
  nums[is.na(nums)] <- m
  return(paste(round(nums, 2), collapse = " "))
}
''',
        test_cases=[
            {"input": "4\nNA\n8\n", "expected_output": "4 6 8", "description": "One missing value"},
            {"input": "1\n2\n\n4\n", "expected_output": "1 2 2.33 4", "description": "Blank line missing"},
            {"input": "10\n10\n10\n", "expected_output": "10 10 10", "description": "No missing values"},
        ],
    ),
    L(
        id="da-project-ex-recommend",
        course_id="data-analytics-with-r",
        module_id="da-project",
        title="Exercise: Final Recommendation",
        type="exercise",
        order=7,
        content="""## Exercise: Final Recommendation

Write a function `recommend(input)` that reads `product,rating` rows and returns a recommendation for the product with the **highest average rating**, formatted as:

```text
RECOMMEND:PRODUCT with MEAN
```

where MEAN is the average rounded to 2 decimal places. Ties go to the product that appears first.

### Sample

Input:

```text
omega,5
alpha,3
omega,4
alpha,3
omega,5
```

Output:

```text
RECOMMEND:omega with 4.67
```

### How your code runs

Accumulate rating sums and counts per product, compute the means, and pick the best with `which.max()`.

### Starter code

```r
recommend <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  prods <- c()
  sums <- c()
  counts <- c()
  for (line in lines) {
    parts <- strsplit(line, ",")[[1]]
    pr <- parts[1]
    v <- as.numeric(parts[2])
    idx <- match(pr, prods)
    if (is.na(idx)) {
      prods <- c(prods, pr)
      sums <- c(sums, v)
      counts <- c(counts, 1)
    } else {
      sums[idx] <- sums[idx] + v
      counts[idx] <- counts[idx] + 1
    }
  }
  means <- sums / counts
  best <- which.max(means)
  return(paste0("RECOMMEND:", prods[best], " with ", round(means[best], 2)))
}
```

Good luck!""",
        starter_code='''recommend <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  prods <- c()
  sums <- c()
  counts <- c()
  for (line in lines) {
    parts <- strsplit(line, ",")[[1]]
    pr <- parts[1]
    v <- as.numeric(parts[2])
    idx <- match(pr, prods)
    if (is.na(idx)) {
      prods <- c(prods, pr)
      sums <- c(sums, v)
      counts <- c(counts, 1)
    } else {
      sums[idx] <- sums[idx] + v
      counts[idx] <- counts[idx] + 1
    }
  }
  means <- sums / counts
  best <- which.max(means)
  return(paste0("RECOMMEND:", prods[best], " with ", round(means[best], 2)))
}
''',
        test_cases=[
            {"input": "omega,5\nalpha,3\nomega,4\nalpha,3\nomega,5\n", "expected_output": "RECOMMEND:omega with 4.67", "description": "Clear winner"},
            {"input": "p1,9\np1,9\np2,8\np2,8\n", "expected_output": "RECOMMEND:p1 with 9", "description": "Higher average"},
            {"input": "q,6\n", "expected_output": "RECOMMEND:q with 6", "description": "Single product"},
        ],
    ),
]
