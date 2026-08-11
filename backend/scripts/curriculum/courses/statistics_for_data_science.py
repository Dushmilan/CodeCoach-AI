"""Statistics for Data Science — curriculum content module."""

COURSE = {
    "id": "statistics-for-data-science",
    "title": "Statistics for Data Science",
    "description": (
        "The statistics a data scientist actually uses: descriptive statistics, "
        "probability and conditional reasoning, the distributions that underpin "
        "sampling, confidence intervals and hypothesis tests, and correlation and "
        "regression. Concepts stay front and center, with every exercise running on "
        "base R so you can practice the interpretation, not just the arithmetic."
    ),
    "language": "r",
    "icon": "bar-chart",
    "order": 8,
}

MODULES = [
    {
        "id": "stats-descriptive",
        "course_id": "statistics-for-data-science",
        "title": "Descriptive Statistics",
        "description": "Summarize a dataset with measures of center, spread, percentiles, and shape.",
        "order": 1,
    },
    {
        "id": "stats-probability",
        "course_id": "statistics-for-data-science",
        "title": "Probability Fundamentals",
        "description": "Reason about events, conditional probability, Bayes' theorem, and independence.",
        "order": 2,
    },
    {
        "id": "stats-distributions",
        "course_id": "statistics-for-data-science",
        "title": "Distributions and Sampling",
        "description": "Meet the normal and binomial distributions, z-scores, sampling, and the central limit theorem.",
        "order": 3,
    },
    {
        "id": "stats-inference",
        "course_id": "statistics-for-data-science",
        "title": "Inference and Relationships",
        "description": "Build confidence intervals, run hypothesis tests, and model relationships with correlation and regression.",
        "order": 4,
    },
    {
        "id": "stats-project",
        "course_id": "statistics-for-data-science",
        "title": "Applied Statistics Project",
        "description": "Tie everything together: design a question, analyze a dataset, and justify your conclusions.",
        "order": 5,
    },
]

_R = "r"


def L(**kw):
    kw.setdefault("language", _R)
    return kw


LESSONS = [
    # ── Module 1: Descriptive Statistics ────────────────────────────────
    L(
        id="stats-descriptive-center",
        course_id="statistics-for-data-science",
        module_id="stats-descriptive",
        title="Measures of Central Tendency",
        type="theory",
        order=1,
        content="""## Measures of Central Tendency

Central tendency answers the first question about any dataset: **what is typical?**

### The mean

The arithmetic average — sum divided by count:

```r
mean(c(1, 2, 3, 4, 5))   # 3
```

Sensitive to every value, including extreme ones. A single $10,000 purchase drags an average order value up.

### The median

The middle value when sorted. Robust to outliers:

```r
median(c(1, 2, 3, 4, 5))        # 3
median(c(1, 2, 3, 4, 100))      # 3  (the 100 barely matters)
```

### The mode

The most frequent value. Base R has no built-in mode — build one with a frequency count:

```r
x <- c(2, 3, 3, 3, 4)
tab <- table(x)
names(tab)[which.max(tab)]       # "3"
```

### Which one to report?

| Situation                              | Prefer         |
|----------------------------------------|----------------|
| Roughly symmetric, no outliers         | mean           |
| Skewed data or outliers present        | median         |
| Categorical / repeated values          | mode           |
| You need sums later in the analysis    | mean           |

### Mean vs median is a signal

When mean and median differ a lot, the data is skewed. Median is the honest "typical" value for income, prices, and response times — all classic right-skewed data.

---

**Next up:** how spread out the data is — variance and standard deviation."""
    ),
    L(
        id="stats-descriptive-spread",
        course_id="statistics-for-data-science",
        module_id="stats-descriptive",
        title="Measures of Spread",
        type="theory",
        order=2,
        content="""## Measures of Spread

Center tells you where the data sits; **spread** tells you how much it wobbles around that center. Two datasets can share a mean of 50 yet differ completely.

### Range

The simplest measure — max minus min:

```r
range(x)          # returns c(min, max)
max(x) - min(x)
```

Quick and fragile: a single outlier blows it up.

### Variance

The average squared deviation from the mean:

```r
var(x)
```

Squaring removes negative deviations but changes the units (dollars become dollars-squared), which is hard to read.

### Standard deviation

The square root of the variance — back in the original units:

```r
sd(x)
```

- Small `sd`: values cluster near the mean.
- Large `sd`: values are scattered.

### Population vs sample

R's `var()` and `sd()` divide by `n - 1` — the sample version. Using `n - 1` gives an unbiased estimate of the population spread when `x` is a sample, which is almost always what you want.

### The empirical rule

For bell-shaped (roughly normal) data:

- ~68% of values within 1 standard deviation of the mean.
- ~95% within 2.
- ~99.7% within 3.

This is why "within 1 sd of the mean" is a meaningful interpretation exercise — it describes where most real-world data lives.

---

**Next up:** percentiles and the interquartile range."""
    ),
    L(
        id="stats-descriptive-quartiles",
        course_id="statistics-for-data-science",
        module_id="stats-descriptive",
        title="Percentiles and the IQR",
        type="theory",
        order=3,
        content="""## Percentiles and the IQR

A **percentile** is the value below which a given percentage of the data falls. The 25th percentile means "25% of values are at or below this".

### Quartiles and quantiles

```r
quantile(x, c(0.25, 0.50, 0.75))
```

- **Q1** — 25th percentile.
- **Q2** — the median (50th percentile).
- **Q3** — 75th percentile.

Together with min and max they form the **five-number summary** (`summary()` in R).

### The interquartile range

```r
iqr <- quantile(x, 0.75) - quantile(x, 0.25)
```

The IQR is the width of the middle 50% of the data. Unlike the range, it ignores the extreme tails, so outliers barely affect it — that robustness makes it the backbone of the box plot.

### Box plot fences

The box plot draws whiskers to the last values within `1.5 * IQR` of the quartiles, and plots anything beyond as dots (outliers):

```r
q1    <- quantile(x, 0.25)
q3    <- quantile(x, 0.75)
lower <- q1 - 1.5 * (q3 - q1)
upper <- q3 + 1.5 * (q3 - q1)
```

### Why percentiles matter in data science

- **Thresholds:** "the 90th percentile response time" describes the worst experiences.
- **Robustness:** percentiles resist outliers better than means and standard deviations.
- **Box plots:** five numbers summarize an entire distribution at a glance.

---

**Next up:** reading the shape of a distribution from its statistics."""
    ),
    L(
        id="stats-descriptive-shape",
        course_id="statistics-for-data-science",
        module_id="stats-descriptive",
        title="Shape, Skew, and Symmetry",
        type="theory",
        order=4,
        content="""## Shape, Skew, and Symmetry

Statistics describe numbers, but **shape** describes what they mean. The relationship between mean and median is a fast, numeric way to detect skew without a plot.

### Symmetric data

In a symmetric distribution, mean and median sit together, and the distribution mirrors itself around the center:

```r
x <- c(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
mean(x)    # 6
median(x)  # 6
```

### Right-skewed (positive skew)

A long tail of large values pulls the mean above the median:

```r
y <- c(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100)
mean(y)    # 14.1
median(y)  # 6
```

The one huge value inflates the mean while the median stays put.

### Left-skewed (negative skew)

A long tail of small values pushes the mean below the median.

### The rule of thumb

| Condition                  | Shape                |
|----------------------------|----------------------|
| mean ≈ median              | symmetric            |
| mean > median              | right-skewed         |
| mean < median              | left-skewed          |

### A practical detector

```r
if (abs(mean(x) - median(x)) < 0.1 * sd(x)) {
  "symmetric"
} else {
  "skewed"
}
```

A small gap relative to the spread is symmetric; a large one is skewed.

### Why you care

Skew changes which summaries to trust (median over mean) and which tests and models are safe. Skew is also everywhere in real data — prices, salaries, response times — so spotting it is a daily skill.

---

**Next up:** three exercises — center, IQR fences, and a shape check."""
    ),
    L(
        id="stats-descriptive-ex-center",
        course_id="statistics-for-data-science",
        module_id="stats-descriptive",
        title="Exercise: Center Statistics",
        type="exercise",
        order=5,
        content="""## Exercise: Center Statistics

Write a function `center_stats(input)` that reads numbers (one per line) and returns the **mean**, the **median**, and the **mode** (most frequent value), joined by spaces, each rounded to 2 decimal places. When values tie for the mode, use the one that appears **first** in the input.

### Sample

Input:

```text
1
2
2
3
3
3
```

Output:

```text
2.33 2.5 3
```

### How your code runs

Compute the mode yourself: track each distinct value's count in first-appearance order, then pick the value with the largest count using `which.max()`.

### Starter code

```r
center_stats <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  vals <- c()
  counts <- c()
  for (v in nums) {
    idx <- match(v, vals)
    if (is.na(idx)) {
      vals <- c(vals, v)
      counts <- c(counts, 1)
    } else {
      counts[idx] <- counts[idx] + 1
    }
  }
  mode_val <- vals[which.max(counts)]
  return(paste(round(mean(nums), 2), round(median(nums), 2), round(mode_val, 2)))
}
```

Good luck!""",
        starter_code='''center_stats <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  vals <- c()
  counts <- c()
  for (v in nums) {
    idx <- match(v, vals)
    if (is.na(idx)) {
      vals <- c(vals, v)
      counts <- c(counts, 1)
    } else {
      counts[idx] <- counts[idx] + 1
    }
  }
  mode_val <- vals[which.max(counts)]
  return(paste(round(mean(nums), 2), round(median(nums), 2), round(mode_val, 2)))
}
''',
        test_cases=[
            {"input": "1\n2\n2\n3\n3\n3\n", "expected_output": "2.33 2.5 3", "description": "Mode is 3"},
            {"input": "4\n8\n15\n16\n23\n42\n", "expected_output": "18 15.5 4", "description": "All distinct, first is mode"},
            {"input": "5\n5\n5\n", "expected_output": "5 5 5", "description": "All equal"},
        ],
    ),
    L(
        id="stats-descriptive-ex-iqr",
        course_id="statistics-for-data-science",
        module_id="stats-descriptive",
        title="Exercise: IQR and Outlier Fences",
        type="exercise",
        order=6,
        content="""## Exercise: IQR and Outlier Fences

Write a function `iqr_fences(input)` that reads numbers (one per line) and returns five values joined by spaces, each rounded to 2 decimal places: **Q1**, **Q3**, **IQR**, **lower fence**, and **upper fence**.

- `Q1 = quantile(x, 0.25)`
- `Q3 = quantile(x, 0.75)`
- `IQR = Q3 - Q1`
- `lower = Q1 - 1.5 * IQR`
- `upper = Q3 + 1.5 * IQR`

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
2 4 2 -1 7
```

### How your code runs

Drop `NA`s, compute the five values, and join them with `paste()`.

### Starter code

```r
iqr_fences <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  q1 <- quantile(nums, 0.25)
  q3 <- quantile(nums, 0.75)
  iqr <- q3 - q1
  lower <- q1 - 1.5 * iqr
  upper <- q3 + 1.5 * iqr
  return(paste(round(q1, 2), round(q3, 2), round(iqr, 2), round(lower, 2), round(upper, 2)))
}
```

Good luck!""",
        starter_code='''iqr_fences <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  q1 <- quantile(nums, 0.25)
  q3 <- quantile(nums, 0.75)
  iqr <- q3 - q1
  lower <- q1 - 1.5 * iqr
  upper <- q3 + 1.5 * iqr
  return(paste(round(q1, 2), round(q3, 2), round(iqr, 2), round(lower, 2), round(upper, 2)))
}
''',
        test_cases=[
            {"input": "1\n2\n3\n4\n5\n", "expected_output": "2 4 2 -1 7", "description": "Simple sequence"},
            {"input": "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n", "expected_output": "3.25 7.75 4.5 -3.5 14.5", "description": "Ten values"},
            {"input": "1\n1\n1\n1\n", "expected_output": "1 1 0 1 1", "description": "No spread"},
        ],
    ),
    L(
        id="stats-descriptive-ex-shape",
        course_id="statistics-for-data-science",
        module_id="stats-descriptive",
        title="Exercise: Symmetric or Skewed",
        type="exercise",
        order=7,
        content="""## Exercise: Symmetric or Skewed

Write a function `shape_check(input)` that reads numbers (one per line) and returns **`symmetric`** or **`skewed`** by comparing the mean with the median.

Use the rule: symmetric if `abs(mean - median) <= 0.1 * sd`, or if `sd` is zero; otherwise skewed.

### Sample

Input:

```text
1
2
3
4
5
6
7
8
9
10
11
```

Output:

```text
symmetric
```

### How your code runs

The mean (6) and median (6) coincide, and the gap relative to the spread is tiny, so the distribution looks symmetric.

### Starter code

```r
shape_check <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  m <- mean(nums)
  md <- median(nums)
  s <- sd(nums)
  if (s == 0 || abs(m - md) <= 0.1 * s) {
    return("symmetric")
  }
  return("skewed")
}
```

Good luck!""",
        starter_code='''shape_check <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  m <- mean(nums)
  md <- median(nums)
  s <- sd(nums)
  if (s == 0 || abs(m - md) <= 0.1 * s) {
    return("symmetric")
  }
  return("skewed")
}
''',
        test_cases=[
            {"input": "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n", "expected_output": "symmetric", "description": "Symmetric sequence"},
            {"input": "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n100\n", "expected_output": "skewed", "description": "High outlier pulls mean"},
            {"input": "5\n5\n5\n5\n", "expected_output": "symmetric", "description": "Zero spread"},
        ],
    ),
    # ── Module 2: Probability Fundamentals ──────────────────────────────
    L(
        id="stats-probability-events",
        course_id="statistics-for-data-science",
        module_id="stats-probability",
        title="Events and Sample Spaces",
        type="theory",
        order=1,
        content="""## Events and Sample Spaces

Probability is the language of uncertainty. Before any formula, it helps to name the two building blocks.

### The sample space

The **sample space** is every outcome that could happen. For a coin flip it is `{H, T}`; for a die roll it is `{1, 2, 3, 4, 5, 6}`.

### Events

An **event** is a set of outcomes you care about. "Rolling an even number" is the set `{2, 4, 6}`.

### Probability of an event

For equally likely outcomes:

```
P(event) = number of favorable outcomes / number of total outcomes
```

P(even die roll) = 3/6 = 0.5.

### The rules of the game

- Probabilities are between 0 and 1.
- The probabilities of all outcomes in the sample space sum to 1.
- P(event does not happen) = 1 - P(event).

### Empirical probability

When you can't enumerate outcomes, estimate with data — the relative frequency:

```r
outcomes <- c("H", "H", "T", "H", "T")
mean(outcomes == "H")       # 0.6
```

### Working with tables

In the exercises, counts come from small tables or observation lists. Convert counts to proportions the same way: favorable over total.

```r
p <- count_favorable / count_total
round(p, 2)
```

Empirical probability from a sample is an estimate, not a guarantee — a big, representative sample makes it trustworthy.

---

**Next up:** updating probabilities when you know something extra — conditional probability."""
    ),
    L(
        id="stats-probability-conditional",
        course_id="statistics-for-data-science",
        module_id="stats-probability",
        title="Conditional Probability",
        type="theory",
        order=2,
        content="""## Conditional Probability

**Conditional probability** answers *"given that something is true, how likely is this?"* It is the single most used idea in statistics and machine learning.

### The definition

`P(A | B)` reads "probability of A given B":

```
P(A | B) = P(A and B) / P(B)
```

### From a contingency table

Take counts of group by outcome:

|        | pass | fail | total |
|--------|------|------|-------|
| Male   | 30   | 10   | 40    |
| Female | 40   | 20   | 60    |

P(pass | Male) = 30 / 40 = 0.75 — restrict attention to the Male row, then take the pass share of it.

### In R

```r
group_total <- 40
joint <- 30
p <- joint / group_total
```

### What conditioning changes

Unconditionally, P(pass) = 70/100 = 0.7. Conditioned on Male it is 0.75, on Female it is 40/60 = 0.67. The conditional view reveals differences the overall rate hides — the same "aggregate fallacy" you met in data analytics.

### Common pitfalls

- P(A | B) is not P(B | A). P(pass | Male) and P(Male | pass) are different numbers.
- Conditioning on a rare group can swing probabilities dramatically.
- Always check whether the extra information actually changes the odds.

Conditional reasoning is the engine behind spam filters, medical screening, and recommendation systems — nearly every model output is a conditional probability in disguise.

---

**Next up:** flipping that conditioning around with Bayes' theorem."""
    ),
    L(
        id="stats-probability-bayes",
        course_id="statistics-for-data-science",
        module_id="stats-probability",
        title="Bayes Theorem",
        type="theory",
        order=3,
        content="""## Bayes Theorem

Bayes' theorem turns conditional probability around: it computes `P(A | B)` from `P(B | A)` and the base rates.

### The theorem

```
P(A | B) = P(B | A) * P(A) / P(B)
```

where `P(B) = P(B | A) * P(A) + P(B | not A) * P(not A)`.

### A screening example

A test for a rare condition:

- Prior `P(D) = 0.01` (1% of people have the condition).
- Sensitivity `P(+ | D) = 0.90` (test is positive for 90% of ill people).
- False positive rate `P(+ | not D) = 0.05`.

What is `P(D | +)` — the chance someone who tests positive actually has the condition?

```r
prior <- 0.01
sens  <- 0.90
fpr   <- 0.05

num <- sens * prior
den <- num + fpr * (1 - prior)
posterior <- num / den        # 0.15
```

### The intuition

Even with a 90% sensitive test, the posterior is only 15%! Why? The condition is rare, so most positive results come from the 5% false-positive rate applied to the huge healthy majority. **Rare events are rarely confirmed by a single test.**

### Why data scientists care

Bayes is the foundation of Bayesian inference, A/B test updates, and many classifier outputs. The pattern — *start with a prior, update it with evidence* — appears everywhere.

### The arithmetic skill

Your exercises compute the posterior directly from `prior`, `sensitivity`, and `false_positive_rate`:

```r
posterior <- sens * prior / (sens * prior + fpr * (1 - prior))
```

---

**Next up:** when knowing one event says nothing about another — independence."""
    ),
    L(
        id="stats-probability-independence",
        course_id="statistics-for-data-science",
        module_id="stats-probability",
        title="Independence and Basic Counting",
        type="theory",
        order=4,
        content="""## Independence and Basic Counting

Two events are **independent** when knowing one tells you nothing about the other.

### The definition

A and B are independent exactly when:

```
P(A and B) = P(A) * P(B)
```

Equivalently, `P(A | B) = P(A)` — the conditioning changes nothing.

### Dependent vs independent

- Coin flips are independent: past flips don't change the next one.
- "It rained" and "the ground is wet" are dependent: knowing one sharply changes the other's probability.

### The multiplication rule

For independent events, the probability that both happen is the product:

```r
p_both <- p_heads * p_heads   # 0.5 * 0.5 = 0.25
```

Three heads in a row: `0.5^3 = 0.125`.

### Counting outcomes

For `k` independent choices each with `n` options, the sample space has `n^k` outcomes. Two dice: `6 * 6 = 36`. Three yes/no questions: `2^3 = 8`.

### When independence fails

Events are **not** independent when they share a cause, when one influences the other, or when they're drawn *without* replacement (each draw changes the deck). Sampling without replacement is the classic trap: the second card's probability depends on the first.

### Why it matters

Independence assumptions power simple probability models, variance rules, and the central limit theorem you'll meet next. When the assumption is wrong, the model quietly over- or under-estimates.

---

**Next up:** the workhorse distributions of data science — normal and binomial."""
    ),
    L(
        id="stats-probability-ex-empirical",
        course_id="statistics-for-data-science",
        module_id="stats-probability",
        title="Exercise: Empirical Probability",
        type="exercise",
        order=5,
        content="""## Exercise: Empirical Probability

Write a function `empirical_prob(input)` that reads a **target outcome** on the first line and a list of observed outcomes below it, and returns the empirical probability of the target, rounded to 2 decimal places.

Empirical probability = (count of target) / (total observations).

### Sample

Input:

```text
H
H
H
T
H
T
```

Output:

```text
0.6
```

Three heads out of five flips.

### How your code runs

Drop blank lines, take the first as the target, count matches among the rest with `sum(obs == target)`, and divide by the number of observations.

### Starter code

```r
empirical_prob <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  target <- lines[1]
  obs <- lines[-1]
  hits <- sum(obs == target)
  return(as.character(round(hits / length(obs), 2)))
}
```

Good luck!""",
        starter_code='''empirical_prob <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  target <- lines[1]
  obs <- lines[-1]
  hits <- sum(obs == target)
  return(as.character(round(hits / length(obs), 2)))
}
''',
        test_cases=[
            {"input": "H\nH\nH\nT\nH\nT\n", "expected_output": "0.6", "description": "Three of five heads"},
            {"input": "T\nT\nT\n", "expected_output": "1", "description": "Always tails"},
            {"input": "A\nB\nC\n", "expected_output": "0", "description": "Target never observed"},
        ],
    ),
    L(
        id="stats-probability-ex-conditional",
        course_id="statistics-for-data-science",
        module_id="stats-probability",
        title="Exercise: Conditional Probability from a Table",
        type="exercise",
        order=6,
        content="""## Exercise: Conditional Probability from a Table

Write a function `conditional_prob(input)` that receives a **request line** `group,outcome` followed by contingency table rows `group,outcome,count`, and returns `P(outcome | group)`, rounded to 2 decimal places.

`P(outcome | group) = (count of group AND outcome) / (total count of group)`.

### Sample

Input:

```text
M,pass
M,pass,30
M,fail,10
F,pass,40
F,fail,20
```

Output:

```text
0.75
```

### How your code runs

Parse the request from the first line, then sum counts for the group (denominator) and for the group-and-outcome pair (numerator).

### Starter code

```r
conditional_prob <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  req <- strsplit(lines[1], ",")[[1]]
  g_target <- req[1]
  o_target <- req[2]
  group_total <- 0
  joint <- 0
  for (line in lines[-1]) {
    parts <- strsplit(line, ",")[[1]]
    g <- parts[1]
    o <- parts[2]
    c <- as.numeric(parts[3])
    if (g == g_target) {
      group_total <- group_total + c
      if (o == o_target) {
        joint <- joint + c
      }
    }
  }
  return(as.character(round(joint / group_total, 2)))
}
```

Good luck!""",
        starter_code='''conditional_prob <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  req <- strsplit(lines[1], ",")[[1]]
  g_target <- req[1]
  o_target <- req[2]
  group_total <- 0
  joint <- 0
  for (line in lines[-1]) {
    parts <- strsplit(line, ",")[[1]]
    g <- parts[1]
    o <- parts[2]
    c <- as.numeric(parts[3])
    if (g == g_target) {
      group_total <- group_total + c
      if (o == o_target) {
        joint <- joint + c
      }
    }
  }
  return(as.character(round(joint / group_total, 2)))
}
''',
        test_cases=[
            {"input": "M,pass\nM,pass,30\nM,fail,10\nF,pass,40\nF,fail,20\n", "expected_output": "0.75", "description": "Pass given male"},
            {"input": "F,pass\nM,pass,30\nM,fail,10\nF,pass,40\nF,fail,20\n", "expected_output": "0.67", "description": "Pass given female"},
            {"input": "M,fail\nM,pass,30\nM,fail,10\nF,pass,40\nF,fail,20\n", "expected_output": "0.25", "description": "Fail given male"},
        ],
    ),
    L(
        id="stats-probability-ex-bayes",
        course_id="statistics-for-data-science",
        module_id="stats-probability",
        title="Exercise: Apply Bayes Theorem",
        type="exercise",
        order=7,
        content="""## Exercise: Apply Bayes Theorem

Write a function `bayes_posterior(input)` that reads three numbers, one per line — the **prior** `P(D)`, the **sensitivity** `P(+|D)`, and the **false positive rate** `P(+|not D)` — and returns the posterior `P(D|+)`, rounded to 2 decimal places.

```
P(D|+) = sens * prior / (sens * prior + fpr * (1 - prior))
```

### Sample

Input:

```text
0.01
0.9
0.05
```

Output:

```text
0.15
```

### How your code runs

Convert the three lines with `as.numeric()` and apply the formula.

### Starter code

```r
bayes_posterior <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  prior <- as.numeric(lines[1])
  sens <- as.numeric(lines[2])
  fpr <- as.numeric(lines[3])
  num <- sens * prior
  den <- num + fpr * (1 - prior)
  return(as.character(round(num / den, 2)))
}
```

Good luck!""",
        starter_code='''bayes_posterior <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  prior <- as.numeric(lines[1])
  sens <- as.numeric(lines[2])
  fpr <- as.numeric(lines[3])
  num <- sens * prior
  den <- num + fpr * (1 - prior)
  return(as.character(round(num / den, 2)))
}
''',
        test_cases=[
            {"input": "0.01\n0.9\n0.05\n", "expected_output": "0.15", "description": "Rare condition"},
            {"input": "0.5\n0.8\n0.2\n", "expected_output": "0.8", "description": "Balanced prior"},
            {"input": "0.001\n0.95\n0.01\n", "expected_output": "0.09", "description": "Very rare condition"},
        ],
    ),
    # ── Module 3: Distributions and Sampling ────────────────────────────
    L(
        id="stats-distributions-normal",
        course_id="statistics-for-data-science",
        module_id="stats-distributions",
        title="The Normal Distribution",
        type="theory",
        order=1,
        content="""## The Normal Distribution

The **normal** (Gaussian) distribution is the bell curve — symmetric, single-peaked, and described entirely by its mean and standard deviation.

### The shape

- Symmetric around the mean.
- Tails fall off smoothly in both directions.
- Mean = median = mode at the center.

### The parameters

```r
rnorm(1000, mean = 70, sd = 10)   # simulate a sample
```

- `mean` — the center.
- `sd` — the spread; smaller `sd` makes a taller, narrower bell.

### The empirical rule

For data that is approximately normal:

| Range                     | Share of data |
|---------------------------|---------------|
| mean ± 1 sd               | ~68%          |
| mean ± 2 sd               | ~95%          |
| mean ± 3 sd               | ~99.7%        |

```r
x <- rnorm(10000, mean = 70, sd = 10)
sum(x >= 60 & x <= 80) / length(x)   # about 0.68
```

### Why it's everywhere

The central limit theorem (next lessons) makes averages of many independent influences approximately normal — heights, measurement errors, test scores, and sample means all behave this way.

### Real data is only approximately normal

Income is right-skewed; wait times are skewed. Check with `hist(x)` or `qqnorm(x)` before assuming normality. Many statistical tests are robust to mild departures — but large departures matter.

### The two numbers to remember

68% of a normal distribution sits within one standard deviation of the mean, and 95% within two. Those two facts let you translate any bell-shaped data into intuition.

---

**Next up:** counting successes — the binomial distribution."""
    ),
    L(
        id="stats-distributions-binomial",
        course_id="statistics-for-data-science",
        module_id="stats-distributions",
        title="The Binomial Distribution",
        type="theory",
        order=2,
        content="""## The Binomial Distribution

The **binomial** distribution counts successes in a fixed number of independent trials, each with the same success probability.

### When is it binomial?

- A fixed number of trials `n`.
- Each trial is success or failure.
- Trials are independent.
- The success probability `p` is the same every trial.

### Examples

- 20 product flips (or 20 customer clicks), success = conversion, `p = 0.3`.
- 50 defect checks, success = defective, `p = 0.02`.

### The expectation

The expected number of successes is `n * p`:

```r
n * p   # 20 * 0.3 = 6 conversions expected
```

### The variance and sd

```r
var <- n * p * (1 - p)
sd  <- sqrt(n * p * (1 - p))
```

The standard deviation shows how much the count wanders around its expectation.

### Simulating

```r
rbinom(1, size = 20, prob = 0.3)   # one random draw
```

Run it many times and the average approaches `n * p` — a hands-on proof of the expectation.

### Reading the output

A binomial distribution is discrete: possible outcomes are whole counts. It is symmetric when `p = 0.5` and skewed toward the rarer outcome otherwise (more skewed as `p` moves away from 0.5 and `n` shrinks).

### Data science link

Conversion rates, click-through rates, churn counts, and A/B test counts are all binomial in nature. Recognizing the setup tells you which formulas apply.

---

**Next up:** why averages of anything tend to look normal — the central limit theorem."""
    ),
    L(
        id="stats-distributions-clt",
        course_id="statistics-for-data-science",
        module_id="stats-distributions",
        title="Sampling Distributions and the CLT",
        type="theory",
        order=3,
        content="""## Sampling Distributions and the CLT

A statistic computed from a sample (a mean, say) is itself a random quantity — draw a different sample and you get a different value. The **sampling distribution** describes how that statistic varies.

### The central limit theorem

The CLT says: draw random samples of size `n` from any population with a finite variance, compute the mean of each, and the distribution of those means approaches a **normal** distribution as `n` grows.

Two consequences:

1. Sample means cluster around the population mean.
2. The spread of the sample means shrinks as `n` grows.

### The standard error

The standard deviation of the sampling distribution is the **standard error**:

```r
se <- sd(x) / sqrt(length(x))
```

- Larger `n` → smaller standard error → more precise estimates.
- The relationship is `sqrt(n)`, not `n`: quadrupling the sample halves the standard error.

### Demonstration

```r
means <- replicate(1000, mean(sample(x, size = 30, replace = TRUE)))
hist(means)          # bell-shaped, even if x is skewed
sd(means)            # close to sd(x) / sqrt(30)
```

### Why the CLT matters

It is the reason so much of statistics works: confidence intervals and hypothesis tests lean on the normality of sample means even when the population is not normal. It converts "one noisy sample" into "a rough idea of where the population mean lives".

### The caveat

The CLT needs a reasonably large `n` (common rule: 30 or more) and no pathological skew or heavy tails. Small samples from skewed populations are not safely normal.

---

**Next up:** standardizing any value into z-scores."""
    ),
    L(
        id="stats-distributions-zscore",
        course_id="statistics-for-data-science",
        module_id="stats-distributions",
        title="Z-Scores and Standardization",
        type="theory",
        order=4,
        content="""## Z-Scores and Standardization

A **z-score** says how far a value sits from the mean, measured in standard deviations. It puts values from different scales onto one common ruler.

### The formula

```r
z <- (x - mean(x)) / sd(x)
```

- z = 0 → the value equals the mean.
- z = 1 → one standard deviation above the mean.
- z = -2 → two standard deviations below.

### Why standardize

A 5% return on $1M and a 5% return on $100 are the same percentage but completely different in scale. A z-score answers *"how unusual is this within its own distribution?"* regardless of units.

### Interpreting z-scores with the empirical rule

For roughly normal data:

| |z|  | Meaning                       |
|-----|-------------------------------|
| < 1 | common                        |
| 1-2 | moderately unusual            |
| > 2 | unusual (~5% of the data)     |
| > 3 | very unusual (~0.3%)          |

### The standard normal

A z-score transforms any normal distribution into the **standard normal**: mean 0, sd 1. All normal probability calculations reduce to the same table (or `pnorm()`).

```r
pnorm(1.5)          # P(Z <= 1.5) for the standard normal
```

### In the exercises

Z-scores appear in three flavors: computing `z = (x - mean) / sd` directly, counting values within ±1 sd of the mean, and flagging values with `|z| >= 2` as unusual.

### The caution

Z-scores inherit the mean and sd, so a single outlier inflates the sd and makes *everything else* look closer to the center than it is. Check the distribution before trusting the z's.

---

**Next up:** three exercises — z-scores, the ±1 sd band, and flagging unusual values."""
    ),
    L(
        id="stats-distributions-ex-zscore",
        course_id="statistics-for-data-science",
        module_id="stats-distributions",
        title="Exercise: Compute a Z-Score",
        type="exercise",
        order=5,
        content="""## Exercise: Compute a Z-Score

Write a function `z_score(input)` that reads three numbers — a value `x`, the mean, and the standard deviation, one per line — and returns the z-score `(x - mean) / sd`, rounded to 2 decimal places.

### Sample

Input:

```text
85
70
10
```

Output:

```text
1.5
```

### How your code runs

Convert the three lines with `as.numeric()` and apply the formula.

### Starter code

```r
z_score <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  x <- as.numeric(lines[1])
  m <- as.numeric(lines[2])
  s <- as.numeric(lines[3])
  return(as.character(round((x - m) / s, 2)))
}
```

Good luck!""",
        starter_code='''z_score <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  x <- as.numeric(lines[1])
  m <- as.numeric(lines[2])
  s <- as.numeric(lines[3])
  return(as.character(round((x - m) / s, 2)))
}
''',
        test_cases=[
            {"input": "85\n70\n10\n", "expected_output": "1.5", "description": "Above the mean"},
            {"input": "60\n70\n10\n", "expected_output": "-1", "description": "Below the mean"},
            {"input": "70\n70\n5\n", "expected_output": "0", "description": "At the mean"},
        ],
    ),
    L(
        id="stats-distributions-ex-band",
        course_id="statistics-for-data-science",
        module_id="stats-distributions",
        title="Exercise: Values within One Standard Deviation",
        type="exercise",
        order=6,
        content="""## Exercise: Values within One Standard Deviation

Write a function `within_one_sd(input)` that reads numbers (one per line) and returns the **count of values within one standard deviation of the mean** (inclusive).

The band is `mean - sd` to `mean + sd`.

### Sample

Input:

```text
1
2
3
4
5
6
7
8
9
10
11
```

Output:

```text
7
```

For this symmetric sequence the mean is 6 and `sd` is about 3.32, so the band runs from roughly 2.68 to 9.32 — seven of the eleven values lie inside it.

### How your code runs

Drop `NA`s, compute `mean(x)` and `sd(x)`, then count with `sum(x >= m - s & x <= m + s)`.

### Starter code

```r
within_one_sd <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  m <- mean(nums)
  s <- sd(nums)
  return(as.character(sum(nums >= m - s & nums <= m + s)))
}
```

Good luck!""",
        starter_code='''within_one_sd <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  m <- mean(nums)
  s <- sd(nums)
  return(as.character(sum(nums >= m - s & nums <= m + s)))
}
''',
        test_cases=[
            {"input": "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n", "expected_output": "7", "description": "Symmetric sequence"},
            {"input": "1\n2\n3\n4\n5\n", "expected_output": "3", "description": "Small sequence"},
            {"input": "5\n5\n5\n5\n", "expected_output": "4", "description": "Zero spread, all inside"},
        ],
    ),
    L(
        id="stats-distributions-ex-unusual",
        course_id="statistics-for-data-science",
        module_id="stats-distributions",
        title="Exercise: Count Unusual Values",
        type="exercise",
        order=7,
        content="""## Exercise: Count Unusual Values

Write a function `unusual_values(input)` that reads numbers (one per line) and returns the **count of values with `|z| >= 2`**, where `z = (x - mean) / sd`.

These are the values more than two standard deviations from the mean — the "unusual" tail values of a roughly normal distribution.

### Sample

Input:

```text
1
2
3
4
5
6
7
8
9
100
```

Output:

```text
1
```

The value 100 sits more than two standard deviations above the mean, so it is counted; the rest are not.

### How your code runs

Compute the z-scores with `(nums - mean(nums)) / sd(nums)` and count how many have absolute value at least 2.

### Starter code

```r
unusual_values <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  m <- mean(nums)
  s <- sd(nums)
  zs <- (nums - m) / s
  return(as.character(sum(abs(zs) >= 2)))
}
```

Good luck!""",
        starter_code='''unusual_values <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  m <- mean(nums)
  s <- sd(nums)
  zs <- (nums - m) / s
  return(as.character(sum(abs(zs) >= 2)))
}
''',
        test_cases=[
            {"input": "1\n2\n3\n4\n5\n6\n7\n8\n9\n100\n", "expected_output": "1", "description": "One clear outlier"},
            {"input": "10\n20\n30\n40\n50\n", "expected_output": "0", "description": "All within two sd"},
            {"input": "1\n1\n2\n2\n3\n3\n10\n10\n", "expected_output": "0", "description": "Mild spread"},
        ],
    ),
    # ── Module 4: Inference and Relationships ───────────────────────────
    L(
        id="stats-inference-ci",
        course_id="statistics-for-data-science",
        module_id="stats-inference",
        title="Confidence Intervals",
        type="theory",
        order=1,
        content="""## Confidence Intervals

A sample mean is one noisy estimate of the population mean. A **confidence interval** wraps it in a range of plausible values so decisions can account for the noise.

### The mechanics

```r
n  <- length(x)
m  <- mean(x)
se <- sd(x) / sqrt(n)          # standard error
lower <- m - 1.96 * se         # 95% confidence
upper <- m + 1.96 * se
```

The `1.96` comes from the normal distribution: 95% of the standard normal sits between -1.96 and 1.96. For a 99% interval, use 2.576.

### What "95% confident" really means

If you repeated the whole sampling process many times, about 95% of the intervals you built would capture the true population mean. It is a statement about the **procedure**, not about any single interval's contents.

### What it does not mean

- Not "95% of the data is in the interval" (that's a different question).
- Not "the true mean has a 95% chance of being here" (the true mean is fixed; the interval is what varies).

### Three levers

| Change                    | Effect on interval          |
|---------------------------|-----------------------------|
| More data (`n` up)        | narrower                    |
| More spread (`sd` up)     | wider                       |
| Higher confidence         | wider                       |

### Reading an interval

An interval that excludes a claimed value is evidence the claim is off. An interval that includes zero (for a difference) is evidence the difference is not clearly real. This is the informal bridge into hypothesis testing.

---

**Next up:** formalizing those decisions — hypothesis testing."""
    ),
    L(
        id="stats-inference-htest",
        course_id="statistics-for-data-science",
        module_id="stats-inference",
        title="Hypothesis Testing",
        type="theory",
        order=2,
        content="""## Hypothesis Testing

A **hypothesis test** asks: *is the pattern in the data real, or could it be chance?* It works by assuming the boring explanation is true and seeing how surprising the data would be.

### The setup

- **Null (H0):** no effect — e.g. the mean equals a claimed value.
- **Alternative (Ha):** the claim is wrong.

### The test statistic

Measure the data's distance from H0 in standard-error units:

```r
z <- (mean(x) - claimed) / (sd(x) / sqrt(n))
```

Big |z| means the data is far from the claim relative to its own uncertainty.

### The p-value

The p-value is the probability of seeing data at least this extreme if H0 were true. A small p-value makes the null look implausible.

### The decision

Standard thresholds: p < 0.05 → "reject H0" (statistically significant). Otherwise, "fail to reject" — you haven't proven H0, you just lack strong evidence against it.

### A working shortcut

With a z-based test and a 95% threshold, `|z| >= 1.96` ≈ `p <= 0.05`. Many of this course's exercises use the even simpler `|z| >= 2` rule as a stand-in.

### The two classic errors

- **Type I:** rejecting a true null (a false alarm).
- **Type II:** failing to reject a false null (a miss).

The significance level (usually 5%) sets the Type I rate you're willing to accept.

### Reading results honestly

A significant result says "unlikely by chance" — not "large", "important", or "true". With a big enough sample, trivial differences become significant. Always pair the test with the size of the effect.

---

**Next up:** measuring relationships between variables — correlation."""
    ),
    L(
        id="stats-inference-correlation",
        course_id="statistics-for-data-science",
        module_id="stats-inference",
        title="Correlation",
        type="theory",
        order=3,
        content="""## Correlation

**Correlation** quantifies how two numeric variables move together, as a single number between -1 and 1.

### Pearson's r

```r
cor(x, y)
```

- Near +1: strong positive linear association.
- Near -1: strong negative linear association.
- Near 0: no linear association.

### Reading the strength

A common loose scale for |r|:

| |r|    | Strength  |
|--------|-----------|
| 0.0-0.2| weak      |
| 0.2-0.4| weak/moderate |
| 0.4-0.7| moderate  |
| 0.7-0.9| strong    |
| 0.9-1.0| very strong|

The exercises use: `|r| >= 0.7` → strong, `>= 0.4` → moderate, else weak.

### The three warnings

1. **Correlation captures only linear patterns.** A strong curve can have `r = 0`.
2. **One outlier can dominate it.** Always plot the scatter.
3. **Correlation is not causation.** Both variables may be driven by a third cause, or the causal direction may be reversed.

### Correlation vs slope

The regression slope shares the sign of `r` but carries units (change in y per unit change in x). Correlation is unit-free, so it is comparable across different variables — which makes it a favorite for feature screening in data science.

### Always visualize

```r
plot(x, y, pch = 19)
```

The scatter tells you whether `r` is a fair summary. Clusters, curves, and wild outliers are all invisible in the single number.

---

**Next up:** turning correlation into a prediction — regression."""
    ),
    L(
        id="stats-inference-regression",
        course_id="statistics-for-data-science",
        module_id="stats-inference",
        title="Regression",
        type="theory",
        order=4,
        content="""## Regression

**Regression** fits a line that predicts one variable from another, turning the correlation into a usable equation.

### The fitted line

```r
fit <- lm(y ~ x, data = df)
coef(fit)
```

- **Intercept:** the predicted y when x = 0.
- **Slope:** the predicted change in y for a one-unit increase in x.

### Slope by hand

For a single predictor, the slope is covariance over variance:

```r
slope <- cov(x, y) / var(x)
intercept <- mean(y) - slope * mean(x)
predicted <- intercept + slope * new_x
```

### Interpreting

A slope of `2.5` for study hours → score means each extra hour of study is associated with 2.5 more points, within the range of the data.

### Residuals

The vertical gaps between the points and the line are **residuals**. Small residuals → good fit. Patterns in the residuals (a curve, a fan shape) mean a straight line is the wrong shape.

### Correlation vs slope

`slope = r * (sd_y / sd_x)`. They always share a sign, but slope is in the variables' units while `r` is unit-free.

### The dangers

- **Extrapolation:** predicting far outside the observed x range is unreliable.
- **Causation:** a fitted line on observed data does not prove x causes y.
- **Influential points:** a single extreme x can tilt the whole line.

### Data science role

Regression is the gateway to machine learning — the same fitting logic (minimize residuals) powers everything from linear models to gradient descent.

---

**Next up:** three exercises — a confidence interval, correlation interpretation, and regression prediction."""
    ),
    L(
        id="stats-inference-ex-ci",
        course_id="statistics-for-data-science",
        module_id="stats-inference",
        title="Exercise: Confidence Interval",
        type="exercise",
        order=5,
        content="""## Exercise: Confidence Interval

Write a function `confidence_interval(input)` that reads numbers (one per line) and returns the **lower and upper bounds** of a 95% confidence interval for the mean, joined by a space, each rounded to 2 decimal places.

Use `mean +- 1.96 * (sd / sqrt(n))`.

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
7.21 28.79
```

### How your code runs

Drop `NA`s, compute `n`, the mean, and the standard error, then apply the 1.96 multiplier.

### Starter code

```r
confidence_interval <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  n <- length(nums)
  m <- mean(nums)
  se <- sd(nums) / sqrt(n)
  lower <- round(m - 1.96 * se, 2)
  upper <- round(m + 1.96 * se, 2)
  return(paste(lower, upper))
}
```

Good luck!""",
        starter_code='''confidence_interval <- function(input) {
  nums <- as.numeric(strsplit(input, "\\n")[[1]])
  nums <- nums[!is.na(nums)]
  n <- length(nums)
  m <- mean(nums)
  se <- sd(nums) / sqrt(n)
  lower <- round(m - 1.96 * se, 2)
  upper <- round(m + 1.96 * se, 2)
  return(paste(lower, upper))
}
''',
        test_cases=[
            {"input": "4\n8\n15\n16\n23\n42\n", "expected_output": "7.21 28.79", "description": "Classic data set"},
            {"input": "50\n52\n54\n56\n", "expected_output": "50.47 55.53", "description": "Tight sample"},
            {"input": "10\n10\n10\n", "expected_output": "10 10", "description": "No spread"},
        ],
    ),
    L(
        id="stats-inference-ex-corr",
        course_id="statistics-for-data-science",
        module_id="stats-inference",
        title="Exercise: Interpret Correlation",
        type="exercise",
        order=6,
        content="""## Exercise: Interpret Correlation

Write a function `correlation_interpret(input)` that reads CSV text with a header `x,y` and returns the **correlation rounded to 2 decimal places followed by a direction word**: `positive`, `negative`, or `weak`.

- `r > 0.2` → positive
- `r < -0.2` → negative
- otherwise → weak

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
1 positive
```

### How your code runs

Collect the two columns and classify the correlation with `ifelse()`.

### Starter code

```r
correlation_interpret <- function(input) {
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
  r <- cor(xs, ys)
  direction <- ifelse(r > 0.2, "positive", ifelse(r < -0.2, "negative", "weak"))
  return(paste(round(r, 2), direction))
}
```

Good luck!""",
        starter_code='''correlation_interpret <- function(input) {
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
  r <- cor(xs, ys)
  direction <- ifelse(r > 0.2, "positive", ifelse(r < -0.2, "negative", "weak"))
  return(paste(round(r, 2), direction))
}
''',
        test_cases=[
            {"input": "x,y\n1,2\n2,4\n3,6\n4,8\n5,10\n", "expected_output": "1 positive", "description": "Perfect positive"},
            {"input": "x,y\n1,5\n2,4\n3,3\n4,2\n5,1\n", "expected_output": "-1 negative", "description": "Perfect negative"},
            {"input": "x,y\n1,3\n2,1\n3,5\n4,2\n5,4\n", "expected_output": "0.3 positive", "description": "Weak positive"},
        ],
    ),
    L(
        id="stats-inference-ex-reg",
        course_id="statistics-for-data-science",
        module_id="stats-inference",
        title="Exercise: Regression Prediction",
        type="exercise",
        order=7,
        content="""## Exercise: Regression Prediction

Write a function `regression_predict(input)` that reads CSV text with a header `x,y`, then a **blank line**, then a **new x value**, and returns the predicted `y` for that new x, rounded to 2 decimal places.

Fit `predicted = intercept + slope * new_x` where `slope = cov(x, y) / var(x)` and `intercept = mean(y) - slope * mean(x)`.

### Sample

Input:

```text
x,y
1,2
2,4
3,6
4,8
5,10

6
```

Output:

```text
12
```

### How your code runs

Split the input on the blank line (`strsplit(input, "\\n\\n")`), parse the table, fit the line, and evaluate it at the new x.

### Starter code

```r
regression_predict <- function(input) {
  parts <- strsplit(input, "\\n\\n")[[1]]
  lines <- strsplit(parts[1], "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  data <- lines[-1]
  xs <- c()
  ys <- c()
  for (line in data) {
    p <- strsplit(line, ",")[[1]]
    xs <- c(xs, as.numeric(p[1]))
    ys <- c(ys, as.numeric(p[2]))
  }
  new_x <- as.numeric(trimws(parts[2]))
  slope <- cov(xs, ys) / var(xs)
  intercept <- mean(ys) - slope * mean(xs)
  pred <- intercept + slope * new_x
  return(as.character(round(pred, 2)))
}
```

Good luck!""",
        starter_code='''regression_predict <- function(input) {
  parts <- strsplit(input, "\\n\\n")[[1]]
  lines <- strsplit(parts[1], "\\n")[[1]]
  lines <- lines[nchar(trimws(lines)) > 0]
  data <- lines[-1]
  xs <- c()
  ys <- c()
  for (line in data) {
    p <- strsplit(line, ",")[[1]]
    xs <- c(xs, as.numeric(p[1]))
    ys <- c(ys, as.numeric(p[2]))
  }
  new_x <- as.numeric(trimws(parts[2]))
  slope <- cov(xs, ys) / var(xs)
  intercept <- mean(ys) - slope * mean(xs)
  pred <- intercept + slope * new_x
  return(as.character(round(pred, 2)))
}
''',
        test_cases=[
            {"input": "x,y\n1,2\n2,4\n3,6\n4,8\n5,10\n\n6\n", "expected_output": "12", "description": "Rising line"},
            {"input": "x,y\n1,5\n2,4\n3,3\n4,2\n5,1\n\n3\n", "expected_output": "3", "description": "Falling line"},
            {"input": "x,y\n0,1\n2,5\n4,9\n6,13\n8,17\n\n10\n", "expected_output": "21", "description": "Offset line"},
        ],
    ),
    # ── Module 5: Applied Statistics Project ────────────────────────────
    L(
        id="stats-project-design",
        course_id="statistics-for-data-science",
        module_id="stats-project",
        title="Designing a Statistical Question",
        type="theory",
        order=1,
        content="""## Designing a Statistical Question

Statistics answers questions, so the quality of the answer starts with the quality of the question. A well-designed statistical question is precise enough to be tested.

### The anatomy of a good question

- **A target:** the quantity you measure (mean rating, correlation, proportion).
- **A comparison:** the baseline or group you compare against.
- **A population:** who or what the answer generalizes to.

### Examples

| Vague question                     | Testable question                                |
|------------------------------------|--------------------------------------------------|
| "Is our new feature good?"         | "Is the mean 7-day retention after launch above 40%?" |
| "Do users prefer design A or B?"   | "Is the A/B click-through difference beyond chance?" |
| "Is temperature related to sales?" | "Is the correlation between temperature and sales stronger than 0.5?" |

### The null hypothesis falls out naturally

A testable question names its **null**: the boring claim you try to knock down.

- "Retention is 40%" vs "it is above 40%".
- "No difference between A and B" vs "a difference exists".

### Pick the right tool

| Question                         | Tool                          |
|----------------------------------|-------------------------------|
| What's the typical value?        | mean / median / summary       |
| Where might the true mean be?    | confidence interval           |
| Does a group beat a threshold?   | hypothesis test               |
| Do two variables move together?  | correlation                   |
| How can we predict y from x?     | regression                    |

### Write it down first

Committing the question, comparison, and decision rule to text *before* running the analysis prevents "I'll know the right test when I see the data" — which usually ends in results that fit the answer you wanted.

---

**Next up:** gathering and cleaning the data that will answer the question."""
    ),
    L(
        id="stats-project-collect",
        course_id="statistics-for-data-science",
        module_id="stats-project",
        title="Collecting and Cleaning Data",
        type="theory",
        order=2,
        content="""## Collecting and Cleaning Data

The question is designed; now the data must be gathered and made trustworthy. Garbage in, garbage out is the most reliable law in statistics.

### Sampling decisions

- **Representative:** the sample should mirror the population's composition.
- **Random:** `sample()` avoids systematic bias.
- **Big enough:** larger samples shrink the standard error, but big and biased is worse than small and random.

```r
set.seed(11)
sample_df <- df[sample(1:nrow(df), size = 100), ]
```

### The cleaning checklist

1. **Missing values** — count them with `sum(is.na(x))` and decide: drop, impute, or analyze separately.
2. **Types** — numbers stored as text (`as.numeric`), dates, stray characters.
3. **Duplicates** — repeated rows inflate evidence; check with `duplicated()`.
4. **Outliers** — record them, then decide keep/drop with a stated rule (e.g. the IQR fences).
5. **Units** — consistent scales across rows and columns.

### The null data trap

An empty cell, a `0` used as "not recorded", and a true `0` are three different things. If your cleaning conflates them, your summary statistics will be quietly wrong.

### Document the process

Every cleaning decision should be traceable: how many rows dropped, which values imputed, why. A reviewer must be able to rebuild your dataset from the raw file.

### Check after cleaning

Compare before/after: row counts, totals, and a `summary()` pass. The numbers should change for reasons you can name.

---

**Next up:** running the statistics that answer the question."""
    ),
    L(
        id="stats-project-analyze",
        course_id="statistics-for-data-science",
        module_id="stats-project",
        title="Analyzing with Inference",
        type="theory",
        order=3,
        content="""## Analyzing with Inference

With a clean dataset and a precise question, inference turns the sample into a statement about the population.

### The analysis ladder

1. **Describe:** summary statistics for the variables of interest.
2. **Estimate:** a confidence interval around the key statistic.
3. **Test:** a hypothesis test against the null.
4. **Relate:** correlation or regression for relationships.

### Describe first

```r
summary(df$retention)
```

Check that the numbers look sane and match the question's target.

### Estimate the uncertainty

```r
n  <- length(x)
m  <- mean(x)
se <- sd(x) / sqrt(n)
lower <- m - 1.96 * se
upper <- m + 1.96 * se
```

The interval says how precise the sample estimate is. A wide interval means the sample can't support a fine-grained claim.

### Test the claim

```r
z <- (m - threshold) / se
```

Compare the statistic against the decision rule you wrote in the design phase — not a rule you invent after seeing the results.

### Relate the variables

If the question involves two variables, add `cor(x, y)` and, when prediction is the goal, fit the regression line.

### Keep every output labeled

Every number in a report should say what it is, what it's based on, and how uncertain it is. "Mean = 41 (95% CI 38-44, n = 90)" is a complete, honest sentence.

---

**Next up:** justifying conclusions and writing the final statistical report."""
    ),
    L(
        id="stats-project-conclude",
        course_id="statistics-for-data-science",
        module_id="stats-project",
        title="Justifying Conclusions",
        type="theory",
        order=4,
        content="""## Justifying Conclusions

A conclusion is only as good as the reasoning that supports it. This lesson is about turning output into a defensible answer.

### The four-part justification

1. **Claim** — the conclusion in one sentence.
2. **Evidence** — the statistic, the comparison, and the uncertainty.
3. **Logic** — why the evidence supports the claim (the test or interval logic).
4. **Limits** — what could undermine it.

### Example

> "Recommend keeping the new checkout. Mean conversion is 4.2% versus 3.1% before (n = 1,200, 95% CI 3.9-4.5%), and the difference is beyond what chance explains. Caveat: the test ran two weeks during a holiday sale, which may inflate conversion for both variants."

### Match the claim to the strength of evidence

- **Interval excludes the null** → "the data supports a difference".
- **Interval includes zero** → "we cannot rule out no difference".
- **Significant but tiny effect** → "real but practically negligible".

### The honesty rules

- Do not overstate: "significant" is not "large" or "proven".
- Report what you actually did — samples, filters, exclusions.
- A conclusion that surprised you deserves extra scrutiny, not extra confidence.

### Write for the decision maker

Lead with the claim, follow with evidence, end with limits. Your reader needs to act, not to relive your analysis.

---

**Next up:** the capstone exercises — back a claim, compare two groups, and write a statistical report."""
    ),
    L(
        id="stats-project-ex-claim",
        course_id="statistics-for-data-science",
        module_id="stats-project",
        title="Exercise: Back a Claim with a Statistic",
        type="exercise",
        order=5,
        content="""## Exercise: Back a Claim with a Statistic

Write a function `back_claim(input)` that reads a **target** on the first line and a column of measurements below it, and returns the **mean rounded to 2 decimal places** and a verdict — `meets` if the mean is at or above the target, otherwise `fails` — joined by a space.

### Sample

Input:

```text
70
65
68
72
75
```

Output:

```text
70 meets
```

### How your code runs

Convert the target, compute the rounded mean of the measurements, and choose the verdict with `ifelse(m >= target, "meets", "fails")`.

### Starter code

```r
back_claim <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  target <- as.numeric(lines[1])
  nums <- as.numeric(lines[-1])
  nums <- nums[!is.na(nums)]
  m <- round(mean(nums), 2)
  verdict <- ifelse(m >= target, "meets", "fails")
  return(paste(m, verdict))
}
```

Good luck!""",
        starter_code='''back_claim <- function(input) {
  lines <- strsplit(input, "\\n")[[1]]
  target <- as.numeric(lines[1])
  nums <- as.numeric(lines[-1])
  nums <- nums[!is.na(nums)]
  m <- round(mean(nums), 2)
  verdict <- ifelse(m >= target, "meets", "fails")
  return(paste(m, verdict))
}
''',
        test_cases=[
            {"input": "70\n65\n68\n72\n75\n", "expected_output": "70 meets", "description": "Exactly at target"},
            {"input": "75\n65\n68\n72\n75\n", "expected_output": "70 fails", "description": "Below target"},
            {"input": "8\n9\n9\n10\n", "expected_output": "9.33 meets", "description": "Clearly above target"},
        ],
    ),
    L(
        id="stats-project-ex-compare",
        course_id="statistics-for-data-science",
        module_id="stats-project",
        title="Exercise: Compare Two Groups",
        type="exercise",
        order=6,
        content="""## Exercise: Compare Two Groups

Write a function `compare_groups(input)` that receives two columns of numbers separated by a **blank line** and returns the **mean of group 1**, the **mean of group 2**, and their **difference** (group1 - group2), joined by spaces, each rounded to 2 decimal places.

### Sample

Input:

```text
10
20
30
40

5
15
25
35
```

Output:

```text
25 20 5
```

### How your code runs

Split the input on the double newline, parse each column, and compute the two means and their difference.

### Starter code

```r
compare_groups <- function(input) {
  parts <- strsplit(input, "\\n\\n")[[1]]
  a <- as.numeric(strsplit(parts[1], "\\n")[[1]])
  b <- as.numeric(strsplit(parts[2], "\\n")[[1]])
  a <- a[!is.na(a)]
  b <- b[!is.na(b)]
  ma <- round(mean(a), 2)
  mb <- round(mean(b), 2)
  return(paste(ma, mb, round(ma - mb, 2)))
}
```

Good luck!""",
        starter_code='''compare_groups <- function(input) {
  parts <- strsplit(input, "\\n\\n")[[1]]
  a <- as.numeric(strsplit(parts[1], "\\n")[[1]])
  b <- as.numeric(strsplit(parts[2], "\\n")[[1]])
  a <- a[!is.na(a)]
  b <- b[!is.na(b)]
  ma <- round(mean(a), 2)
  mb <- round(mean(b), 2)
  return(paste(ma, mb, round(ma - mb, 2)))
}
''',
        test_cases=[
            {"input": "10\n20\n30\n40\n\n5\n15\n25\n35\n", "expected_output": "25 20 5", "description": "Group one higher"},
            {"input": "1\n2\n3\n\n4\n5\n6\n", "expected_output": "2 5 -3", "description": "Group two higher"},
            {"input": "7\n7\n7\n\n7\n7\n7\n", "expected_output": "7 7 0", "description": "Equal groups"},
        ],
    ),
    L(
        id="stats-project-ex-report",
        course_id="statistics-for-data-science",
        module_id="stats-project",
        title="Exercise: Statistical Report",
        type="exercise",
        order=7,
        content="""## Exercise: Statistical Report

Write a function `stats_report(input)` that reads CSV text with a header `x,y` and returns a three-line report:

```text
correlation: VALUE
slope: VALUE
relationship: STRENGTH
```

- Values are rounded to 2 decimal places.
- `STRENGTH` is `strong` if `abs(r) >= 0.7`, `moderate` if `abs(r) >= 0.4`, else `weak`.
- Slope is `cov(x, y) / var(x)`.

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
correlation: 1
slope: 2
relationship: strong
```

### How your code runs

Compute the correlation and slope, classify the strength, and join the three labeled lines with `paste(..., collapse = "\\n")`.

### Starter code

```r
stats_report <- function(input) {
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
  r <- cor(xs, ys)
  slope <- cov(xs, ys) / var(xs)
  strength <- ifelse(abs(r) >= 0.7, "strong", ifelse(abs(r) >= 0.4, "moderate", "weak"))
  out <- c(
    paste0("correlation: ", round(r, 2)),
    paste0("slope: ", round(slope, 2)),
    paste0("relationship: ", strength)
  )
  return(paste(out, collapse = "\\n"))
}
```

Good luck!""",
        starter_code='''stats_report <- function(input) {
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
  r <- cor(xs, ys)
  slope <- cov(xs, ys) / var(xs)
  strength <- ifelse(abs(r) >= 0.7, "strong", ifelse(abs(r) >= 0.4, "moderate", "weak"))
  out <- c(
    paste0("correlation: ", round(r, 2)),
    paste0("slope: ", round(slope, 2)),
    paste0("relationship: ", strength)
  )
  return(paste(out, collapse = "\\n"))
}
''',
        test_cases=[
            {"input": "x,y\n1,2\n2,4\n3,6\n4,8\n5,10\n", "expected_output": "correlation: 1\nslope: 2\nrelationship: strong", "description": "Perfect rising line"},
            {"input": "x,y\n1,5\n2,4\n3,3\n4,2\n5,1\n", "expected_output": "correlation: -1\nslope: -1\nrelationship: strong", "description": "Perfect falling line"},
            {"input": "x,y\n1,3\n2,1\n3,5\n4,2\n5,4\n", "expected_output": "correlation: 0.3\nslope: 0.3\nrelationship: weak", "description": "Weak scatter"},
        ],
    ),
]
