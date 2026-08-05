import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MarkdownRenderer } from "./MarkdownRenderer";

describe("MarkdownRenderer", () => {
  it("renders headings and paragraphs", () => {
    render(<MarkdownRenderer content={"# Title\n\nHello"} />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Title" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Hello")).toBeInTheDocument();
  });

  it("escapes raw HTML so injected scripts never execute", () => {
    render(
      <MarkdownRenderer
        content={"# Safe\n\n<script>window.__xss = 1</script>"}
      />,
    );
    expect(screen.getByText("Safe")).toBeInTheDocument();
    expect(document.querySelector("script")).toBeNull();
  });

  it("escapes code block contents", () => {
    render(<MarkdownRenderer content={"```js\nconst a = '<b>';\n```"} />);
    expect(document.querySelector("pre code")).toBeInTheDocument();
    expect(document.querySelector("b")).toBeNull();
    expect(document.querySelector("pre")?.textContent).toContain(
      "const a = '<b>'",
    );
  });

  it("renders language-less fenced blocks as block code, not inline", () => {
    render(<MarkdownRenderer content={"```\nconst a = 1;\n```"} />);
    const pre = document.querySelector("pre");
    expect(pre).not.toBeNull();
    const code = pre!.querySelector("code");
    expect(code?.className).not.toContain("bg-white/5");
  });

  it("does not render javascript: URLs as clickable links", () => {
    render(<MarkdownRenderer content={"[click](javascript:alert(1))"} />);
    expect(document.querySelector("a[href^='javascript:']")).toBeNull();
    expect(screen.getByText("click")).toBeInTheDocument();
  });

  it("renders safe external links with noreferrer", () => {
    render(<MarkdownRenderer content={"[docs](https://example.com)"} />);
    const link = document.querySelector("a");
    expect(link?.getAttribute("href")).toBe("https://example.com");
    expect(link?.getAttribute("rel")).toContain("noreferrer");
  });

  it("renders GFM tables as real table elements", () => {
    render(
      <MarkdownRenderer
        content={"| Type | Example |\n|---|---|\n| `int` | 42 |\n| `str` | \"hi\" |"}
      />,
    );
    const table = document.querySelector("table");
    expect(table).not.toBeNull();
    const headers = table!.querySelectorAll("th");
    expect(headers).toHaveLength(2);
    expect(headers[0].textContent).toContain("Type");
    expect(headers[1].textContent).toContain("Example");
    const rows = table!.querySelectorAll("tbody tr");
    expect(rows).toHaveLength(2);
    expect(rows[0].querySelectorAll("td")).toHaveLength(2);
    expect(rows[0].querySelector("code")?.textContent).toBe("int");
  });

  it("wraps list items in a ul", () => {
    render(<MarkdownRenderer content={"- item one\n- item two"} />);
    const ul = document.querySelector("ul");
    expect(ul).not.toBeNull();
    expect(ul!.querySelectorAll("li")).toHaveLength(2);
  });

  it("renders inline code and bold text", () => {
    render(<MarkdownRenderer content={"Use `strand1` and **strand2**"} />);
    expect(document.querySelector("code")?.textContent).toBe("strand1");
    expect(document.querySelector("strong")?.textContent).toBe("strand2");
    expect(screen.queryByText(/`strand1`/)).not.toBeInTheDocument();
    expect(screen.queryByText(/\*\*strand2\*\*/)).not.toBeInTheDocument();
  });
});
