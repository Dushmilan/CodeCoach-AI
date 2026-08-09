#!/usr/bin/env python3
"""Convert CodeCoach AI Markdown documentation into self-contained, styled HTML.

Stdlib only. Each output file is written next to its source as ``<name>.html``.

Usage:
    python tools/markdown_to_html.py [FILE.md ...]

If no files are given, the default documentation set is converted.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DOCS_INDEX = [
    ("README.html", "README"),
    ("Progress.html", "Progress"),
    ("Ideas.html", "Ideas"),
    ("CLAUDE.html", "Engineering Guidelines"),
    ("AGENTS.html", "Agent Guide"),
    ("SECURITY.html", "Security Policy"),
    ("CONTRIBUTING.html", "Contributing"),
    ("CODE_OF_CONDUCT.html", "Code of Conduct"),
    ("Docs/AUDIT_REPORT.html", "Audit Report"),
    ("backend/tests/README.html", "Test Suite"),
]

DEFAULT_DOCS = [
    "README.md",
    "Progress.md",
    "Ideas.md",
    "CLAUDE.md",
    "AGENTS.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "Docs/AUDIT_REPORT.md",
    "backend/tests/README.md",
]

CSS = """
:root {
  --bg: #f8fafc;
  --content: #1e293b;
  --muted: #64748b;
  --accent: #4f46e5;
  --accent-soft: #eef2ff;
  --border: #e2e8f0;
  --code-bg: #0f172a;
  --code-fg: #e2e8f0;
  --sidebar-bg: #0f172a;
  --sidebar-fg: #cbd5e1;
  --sidebar-hover: #1e293b;
  --sidebar-link: #94a3b8;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
  color: var(--content);
  background: var(--bg);
  line-height: 1.65;
  font-size: 16px;
}
.layout { display: grid; grid-template-columns: 280px minmax(0, 1fr); min-height: 100vh; }
.sidebar {
  position: sticky; top: 0; height: 100vh; overflow-y: auto;
  background: var(--sidebar-bg); color: var(--sidebar-fg);
  padding: 24px 16px 40px;
}
.sidebar .brand { display: block; color: #fff; font-weight: 700; font-size: 17px; text-decoration: none; padding: 0 8px 6px; }
.sidebar .brand small { display: block; color: #64748b; font-weight: 400; font-size: 12px; }
.sidebar h2 { font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: #64748b; margin: 22px 8px 8px; }
.sidebar a.doc-link {
  display: block; padding: 4px 8px; border-radius: 6px;
  color: var(--sidebar-link); text-decoration: none; font-size: 13px;
}
.sidebar a.doc-link:hover, .sidebar a.doc-link.current { background: var(--sidebar-hover); color: #fff; }
.sidebar nav.toc a {
  display: block; padding: 3px 8px; border-radius: 6px; font-size: 12.5px;
  color: var(--sidebar-link); text-decoration: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sidebar nav.toc a:hover { background: var(--sidebar-hover); color: #fff; }
.sidebar nav.toc a.l2 { padding-left: 18px; }
.sidebar nav.toc a.l3 { padding-left: 28px; }
.content { padding: 40px 56px 96px; max-width: 880px; }
.content h1 { font-size: 30px; line-height: 1.2; border-bottom: 1px solid var(--border); padding-bottom: 12px; margin: 0 0 24px; }
.content h2 { font-size: 23px; margin: 40px 0 14px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
.content h3 { font-size: 19px; margin: 28px 0 10px; }
.content h4, .content h5, .content h6 { font-size: 16px; margin: 22px 0 8px; }
.content h2:target, .content h3:target, .content h4:target { background: var(--accent-soft); }
.content p { margin: 12px 0; }
.content a { color: var(--accent); text-decoration: none; }
.content a:hover { text-decoration: underline; }
.content ul, .content ol { margin: 12px 0 12px 24px; padding: 0; }
.content li { margin: 4px 0; }
.content li > ul, .content li > ol { margin-top: 4px; margin-bottom: 4px; }
.content li input[type="checkbox"] { margin-right: 6px; vertical-align: middle; }
.content blockquote {
  margin: 16px 0; padding: 4px 18px;
  border-left: 4px solid var(--accent); background: var(--accent-soft);
  border-radius: 0 8px 8px 0;
}
.content blockquote p { margin: 8px 0; }
.content hr { border: 0; border-top: 1px solid var(--border); margin: 36px 0; }
.content pre {
  background: var(--code-bg); color: var(--code-fg);
  padding: 16px 18px; border-radius: 8px; overflow-x: auto;
  font-size: 13.5px; line-height: 1.55;
}
.content pre code { background: none; color: inherit; padding: 0; }
.content code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  background: #eef2f7; color: #be185d; padding: 2px 5px; border-radius: 4px; font-size: .88em;
}
.content table { border-collapse: collapse; width: 100%; margin: 18px 0; font-size: 14.5px; }
.content th, .content td { border: 1px solid var(--border); padding: 8px 12px; text-align: left; vertical-align: top; }
.content th { background: #f1f5f9; font-weight: 600; }
.content tr:nth-child(even) td { background: #fbfcfe; }
.content img { max-width: 100%; }
.content del { color: var(--muted); }
@media (max-width: 900px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar { position: static; height: auto; }
  .content { padding: 28px 20px 72px; }
}
"""

INLINE_RE = re.compile(
    r"(?P<code>`[^`\n]+`)"
    r"|(?P<img>!\[[^\]]*\]\([^)]*\))"
    r"|(?P<link>\[[^\]]+\]\([^)]*\))"
    r"|(?P<bold>\*\*[^*\n]+\*\*)"
    r"|(?P<em>\*[^*\n]+\*)"
    r"|(?P<strike>~~[^~\n]+~~)"
)

LIST_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.*)$")
HR_RE = re.compile(r"^(-{3,}|\*{3,}|_{3,})\s*$")
ATX_RE = re.compile(r"^(#{1,6})\s+(.*)$")
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _converted_basenames(inputs: list[str]) -> set[str]:
    names = set()
    for path in inputs:
        p = Path(path)
        if p.suffix.lower() == ".md":
            names.add(p.name[:-3].lower())
    return names


CONVERTED = set()


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9\s-]", "", text.lower()).strip()
    slug = re.sub(r"\s+", "-", slug)
    return slug or "section"


def parse_link(token: str) -> tuple[str, str]:
    m = re.match(r"!?\[([^\]]*)\]\(([^)]*)\)", token)
    if not m:
        return "", ""
    url = m.group(2).split()[0].strip("\"'")
    return m.group(1), url


def rewrite_href(url: str) -> str:
    if url.startswith(("#", "http://", "https://", "mailto:", "ws://", "wss://")):
        return url
    if url.lower().endswith(".md"):
        base = url[:-3]
        name = base.rsplit("/", 1)[-1].lower()
        return base + ".html" if name in CONVERTED else url
    if ".md#" in url:
        base, _, anchor = url.partition(".md#")
        name = base.rsplit("/", 1)[-1].lower()
        return base + ".html#" + anchor if name in CONVERTED else url
    return url


def render_inline(text: str) -> str:
    out: list[str] = []
    pos = 0
    for m in INLINE_RE.finditer(text):
        out.append(html.escape(text[pos : m.start()]))
        tok = m.group(0)
        if m.group("code"):
            out.append("<code>" + html.escape(tok[1:-1]) + "</code>")
        elif m.group("img"):
            alt, url = parse_link(tok[1:])
            out.append(
                f'<img src="{html.escape(url, quote=True)}" alt="{html.escape(alt, quote=True)}">'
            )
        elif m.group("link"):
            label, url = parse_link(tok)
            out.append(
                f'<a href="{html.escape(rewrite_href(url), quote=True)}">{render_inline(label)}</a>'
            )
        elif m.group("bold"):
            out.append("<strong>" + render_inline(tok[2:-2]) + "</strong>")
        elif m.group("em"):
            out.append("<em>" + render_inline(tok[1:-1]) + "</em>")
        elif m.group("strike"):
            out.append("<del>" + render_inline(tok[2:-2]) + "</del>")
        pos = m.end()
    out.append(html.escape(text[pos:]))
    return "".join(out)


def parse_table_row(line: str) -> list[str]:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


def render_table(header: list[str], rows: list[list[str]]) -> str:
    thead = "".join(f"<th>{render_inline(h)}</th>" for h in header)
    body = []
    for row in rows:
        cells = row + [""] * (len(header) - len(row))
        body.append(
            "<tr>"
            + "".join(f"<td>{render_inline(c)}</td>" for c in cells[: len(header)])
            + "</tr>"
        )
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{''.join(body)}</tbody></table>\n"


def render_task_item(text: str) -> tuple[str, str]:
    m = re.match(r"^\[( |x|X)\]\s+(.*)$", text.strip())
    if m:
        checked = " checked" if m.group(1) in "xX" else ""
        return (
            f'<input type="checkbox" disabled{checked}> <span>{render_inline(m.group(2))}</span>',
            m.group(2),
        )
    return "", text


def emit_list(items: list[dict], i: int) -> tuple[str, int]:
    tag = "ol" if items[i]["ordered"] else "ul"
    start = ""
    if tag == "ol" and items[i].get("start"):
        start = f' start="{items[i]["start"]}"'
    cur = items[i]["indent"]
    parts: list[str] = []
    while i < len(items) and items[i]["indent"] == cur:
        item = items[i]
        inner = ""
        j = i + 1
        if j < len(items) and items[j]["indent"] > cur:
            sub, j = emit_list(items, j)
            inner = sub
        parts.append("<li>" + render_item(item) + inner + "</li>")
        i = j
    return f"<{tag}{start}>" + "".join(parts) + f"</{tag}>", i


def render_item(item: dict) -> str:
    lines = [ln for ln in item["content"] if ln.strip()]
    if not lines:
        return ""
    first, remainder = lines[0], lines[1:]
    checkbox, label = render_task_item(first)
    if checkbox:
        body = "<p>" + checkbox + "</p>"
    else:
        body = "<p>" + render_inline(first) + "</p>"
    for ln in remainder:
        body += "<p>" + render_inline(ln) + "</p>"
    return body


def parse_list(lines: list[str], start: int, i: int) -> tuple[str, int]:
    items: list[dict] = []
    base_indent = len(lines[i]) - len(lines[i].lstrip())
    while i < len(lines):
        if lines[i].strip().startswith("```"):
            break
        m = LIST_RE.match(lines[i])
        if m:
            indent = len(m.group(1))
            ordered = bool(re.match(r"^\d+\.", m.group(2)))
            start_num = int(m.group(2)[:-1]) if ordered else None
            items.append(
                {
                    "line_indent": indent,
                    "indent": indent,
                    "ordered": ordered,
                    "start": start_num,
                    "content": [m.group(3)],
                }
            )
            i += 1
            continue
        if not lines[i].strip():
            break
        if len(lines[i]) - len(lines[i].lstrip()) >= base_indent + 2 and items:
            items[-1]["content"].append(lines[i].strip())
            i += 1
            continue
        break
    html_out, _ = emit_list(items, 0)
    return html_out, i


def md_to_html(text: str, heading_ids: list[tuple[int, str, str]]) -> str:
    lines = text.split("\n")
    out: list[str] = []
    used_ids: set[str] = set()
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            buf: list[str] = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            if i < n:
                i += 1
            cls = f' class="language-{html.escape(lang)}"' if lang else ""
            out.append(
                f"<pre><code{cls}>{html.escape(chr(10).join(buf))}</code></pre>\n"
            )
            continue

        if stripped.startswith("|") and i + 1 < n and "-" in lines[i + 1]:
            sep = lines[i + 1].strip()
            if re.match(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", sep):
                header = parse_table_row(line)
                i += 2
                rows = []
                while i < n and TABLE_ROW_RE.match(lines[i]):
                    rows.append(parse_table_row(lines[i]))
                    i += 1
                out.append(render_table(header, rows))
                continue

        if not stripped:
            i += 1
            continue

        m = ATX_RE.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            base = slugify(title)
            sid = base
            k = 2
            while sid in used_ids:
                sid = f"{base}-{k}"
                k += 1
            used_ids.add(sid)
            heading_ids.append((level, title, sid))
            out.append(f'<h{level} id="{sid}">{render_inline(title)}</h{level}>\n')
            i += 1
            continue

        if HR_RE.match(stripped):
            out.append("<hr>\n")
            i += 1
            continue

        if stripped.startswith(">"):
            buf: list[str] = []
            while i < n:
                s = lines[i].strip()
                if s.startswith(">"):
                    buf.append(s[1:].strip() if s[1:2] == " " else s[1:])
                    i += 1
                elif s == "" and i + 1 < n and lines[i + 1].strip().startswith(">"):
                    buf.append("")
                    i += 1
                else:
                    break
            paras = [p.strip() for p in "\n".join(buf).split("\n\n") if p.strip()]
            inner = "".join(f"<p>{render_inline(p)}</p>" for p in paras)
            out.append(f"<blockquote>{inner}</blockquote>\n")
            continue

        if LIST_RE.match(line):
            html_out, i = parse_list(lines, 0, i)
            out.append(html_out + "\n")
            continue

        buf: list[str] = []
        while i < n:
            s = lines[i]
            if not s.strip():
                break
            if ATX_RE.match(s) or HR_RE.match(s.strip()) or s.strip().startswith("```"):
                break
            if s.strip().startswith(">"):
                break
            if LIST_RE.match(s):
                break
            if s.strip().startswith("|") and i + 1 < n and "-" in lines[i + 1]:
                break
            buf.append(s)
            i += 1
        if buf:
            text_join = " ".join(x.strip() for x in buf)
            out.append(f"<p>{render_inline(text_join)}</p>\n")

    return "".join(out)


def relative_docs_index(out_dir: Path) -> list[tuple[str, str]]:
    links = []
    for rel, label in DOCS_INDEX:
        target = ROOT / rel
        try:
            link = os.path.relpath(target, out_dir)
        except ValueError:
            link = rel
        links.append((link, label))
    return links


def build_page(md_path: Path, out_path: Path, text: str) -> None:
    heading_ids: list[tuple[int, str, str]] = []
    body = md_to_html(text, heading_ids)

    title = out_path.stem.replace("_", " ").title()
    if heading_ids:
        title = heading_ids[0][1]
    site_title = title if "CodeCoach AI" in title else f"{title} — CodeCoach AI"

    current = os.path.relpath(out_path, ROOT).replace("\\", "/")

    doc_links = []
    for link, label in relative_docs_index(out_path.parent):
        cls = (
            ' class="doc-link current"'
            if link == current or link.endswith("/" + current)
            else ' class="doc-link"'
        )
        doc_links.append(f'<a href="{html.escape(link)}"{cls}>{html.escape(label)}</a>')

    toc_items = []
    for level, htext, sid in heading_ids:
        if level == 1:
            continue
        cls = "l2" if level == 2 else "l3"
        toc_items.append(f'<a class="{cls}" href="#{sid}">{html.escape(htext)}</a>')
    toc = "\n".join(toc_items)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="CodeCoach AI docs (tools/markdown_to_html.py)">
<title>{html.escape(site_title)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <a class="brand" href="{html.escape(relative_docs_index(out_path.parent)[0][0])}">CodeCoach AI<small>Documentation</small></a>
    <h2>Docs</h2>
    {chr(10).join(doc_links)}
    <h2>On this page</h2>
    <nav class="toc">
    {toc}
    </nav>
  </aside>
  <main class="content">
{body}
  </main>
</div>
</body>
</html>
"""
    out_path.write_text(page, encoding="utf-8")
    print(f"  wrote {out_path.relative_to(ROOT)} ({len(page):,} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Markdown docs to styled HTML."
    )
    parser.add_argument(
        "files", nargs="*", help="Markdown files to convert (default: all docs)"
    )
    args = parser.parse_args()

    files = args.files or DEFAULT_DOCS
    global CONVERTED
    CONVERTED = _converted_basenames(files)

    missing = [f for f in files if not (ROOT / f).exists()]
    if missing:
        print("Missing files:", ", ".join(missing), file=sys.stderr)
        sys.exit(1)

    for rel in files:
        src = ROOT / rel
        out = src.with_suffix(".html")
        build_page(src, out, src.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
