import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { render, screen } from "@testing-library/react";
import PrivacyPage from "./page";

describe("PrivacyPage", () => {
  it("renders section headings", () => {
    render(<PrivacyPage />);
    expect(
      screen.getByRole("heading", { name: "Privacy Policy" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "What data we collect" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Your rights" }),
    ).toBeInTheDocument();
  });

  it("renders bold labels as real <strong> elements (no raw HTML leakage)", () => {
    render(<PrivacyPage />);
    const strong = screen.getByText("Account information:");
    expect(strong.tagName).toBe("STRONG");
    // Full sentence is present and the label is not shown as literal markup.
    expect(
      screen.getByText(/email address and hashed password \(bcrypt\)/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/<strong>/)).not.toBeInTheDocument();
  });

  it("renders all legal list items without literal HTML leaking as text", () => {
    render(<PrivacyPage />);
    const body = document.body.innerHTML;
    // Rendered <strong> elements are fine; literal escaped markup is not.
    expect(body).not.toContain("&lt;strong&gt;");
    expect(body).not.toContain("&lt;/strong&gt;");
    expect(screen.getByText(/Code submissions:/)).toBeInTheDocument();
    expect(screen.getByText(/No tracking cookies/)).toBeInTheDocument();
  });

  it("does not rely on dangerouslySetInnerHTML to render content", () => {
    render(<PrivacyPage />);
    // The component source must not contain the raw-HTML sink (guards against
    // regressions re-introducing an unescaped injection point).
    const source = readFileSync(__dirname + "/page.tsx", "utf8");
    expect(source).not.toContain("dangerouslySetInnerHTML");
  });

  it("renders plain-text list items (no bold label, no empty bullets)", () => {
    render(<PrivacyPage />);
    // These sections have no <strong> prefix; they must render as plain text.
    const el = screen.getByText(
      "To authenticate you and maintain your session",
    );
    expect(el.closest("strong")).toBeNull();
    expect(
      screen.getByText(
        "Account data and submissions are stored in JSON files on the server",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Both services receive only what is necessary to function. No personal identifiers are shared.",
      ),
    ).toBeInTheDocument();
    // And no list item is left empty by a stray undefined.
    const lis = Array.from(document.querySelectorAll("li"));
    expect(lis.every((li) => li.textContent!.trim().length > 0)).toBe(true);
  });

  it("keeps non-bold bullet items unstyled (no <strong> wrapper)", () => {
    render(<PrivacyPage />);
    const item = screen.getByText("No tracking cookies or analytics scripts");
    expect(item.closest("strong")).toBeNull();
    expect(
      screen.getByText("No advertising identifiers").closest("strong"),
    ).toBeNull();
  });
});
