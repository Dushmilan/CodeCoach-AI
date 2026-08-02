import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  MarkdownRenderer,
  escapeHtml,
  sanitizeHtml,
  renderMarkdown,
} from "./MarkdownRenderer";

describe("escapeHtml", () => {
  it("escapes HTML metacharacters including single quotes", () => {
    const input = `<script>alert("xss")</script> & ' "`;
    expect(escapeHtml(input)).toBe(
      "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt; &amp; &#39; &quot;",
    );
  });
});

describe("sanitizeHtml", () => {
  it("strips script, iframe, object and form tags", () => {
    const html =
      "<p>hello</p><script>alert(1)</script><iframe src=\"x\"></iframe><object></object><form></form>";
    const out = sanitizeHtml(html);
    expect(out).not.toContain("<script");
    expect(out).not.toContain("<iframe");
    expect(out).not.toContain("<object");
    expect(out).not.toContain("<form");
    expect(out).toContain("<p>hello</p>");
  });

  it("removes inline event handler attributes", () => {
    const out = sanitizeHtml(
      '<p onclick="alert(1)" onmouseover=\'steal()\'>safe</p>',
    );
    expect(out).not.toContain("onclick");
    expect(out).not.toContain("onmouseover");
    expect(out).toContain("<p>safe</p>");
  });

  it("strips javascript: URLs from href/src", () => {
    const out = sanitizeHtml(
      '<a href="javascript:alert(1)">x</a><img src="javascript:evil()"/>',
    );
    expect(out).not.toContain("javascript:");
  });
});

describe("renderMarkdown", () => {
  it("escapes raw HTML inside markdown text", () => {
    const out = renderMarkdown("<script>alert(1)</script>");
    expect(out).not.toContain("<script>");
    expect(out).toContain("&lt;script&gt;");
  });

  it("renders headings and paragraphs", () => {
    const out = renderMarkdown("# Title\n\nHello");
    expect(out).toContain("<h1");
    expect(out).toContain("Title");
    expect(out).toContain("<p");
    expect(out).toContain("Hello");
  });

  it("escapes code block contents", () => {
    const out = renderMarkdown("```js\nconst a = '<b>';\n```");
    expect(out).toContain("&lt;b&gt;");
  });
});

describe("MarkdownRenderer component", () => {
  it("renders content without executing injected script", () => {
    render(
      <MarkdownRenderer
        content={"# Safe\n\n<script>window.__xss = 1</script>"}
      />,
    );
    expect(screen.getByText("Safe")).toBeInTheDocument();
    expect(document.querySelector("script")).toBeNull();
  });
});
