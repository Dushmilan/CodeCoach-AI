import { expect } from "vitest";

/**
 * Rendered taste-gate helpers for role surfaces (issues #292/#230).
 * Each surface test calls these after render so copy and rhythm rules are
 * asserted against the real DOM, not just source scans.
 */

/** Zero em/en dashes anywhere in rendered copy. */
export function expectNoDash(container: HTMLElement, label = "page"): void {
  const text = container.textContent ?? "";
  expect(
    text,
    `${label} rendered copy must contain zero em/en dashes`,
  ).not.toMatch(/[\u2012\u2013\u2014]/);
}

/**
 * Bento rhythm for stat cells: every grid of data-stat cells must vary
 * visually, and an exactly-3-cell row needs a spanning cell (no 3-equal-cards).
 */
export function expectBentoStats(container: HTMLElement): void {
  const cells = Array.from(
    container.querySelectorAll<HTMLElement>("[data-stat]"),
  );
  expect(cells.length, "expected stat cells marked with data-stat").toBeGreaterThan(0);
  const groups = new Map<HTMLElement, HTMLElement[]>();
  for (const cell of cells) {
    const parent = cell.parentElement;
    if (!parent) continue;
    const group = groups.get(parent) ?? [];
    group.push(cell);
    groups.set(parent, group);
  }
  groups.forEach((group, parent) => {
    if (group.length < 2) return;
    const classes = new Set(group.map((c: HTMLElement) => c.className));
    expect(
      classes.size,
      `stat cells under "${parent.className}" must not be visually identical`,
    ).toBeGreaterThan(1);
    if (group.length === 3) {
      expect(
        group.some((c: HTMLElement) => c.className.includes("col-span")),
        `a 3-cell stat row under "${parent.className}" needs a spanning cell`,
      ).toBe(true);
    }
  });
}

/** Eyebrow budget: at most ceil(sections / 3) tracked-uppercase labels. */
export function expectEyebrowBudget(container: HTMLElement, label = "page"): void {
  const eyebrows = Array.from(
    container.querySelectorAll('[class*="tracking-widest"]'),
  );
  const sections = container.querySelectorAll("section, [data-section]").length;
  const budget = Math.ceil(sections / 3);
  expect(
    eyebrows.length,
    `${label} has ${eyebrows.length} eyebrows, budget is ${budget}`,
  ).toBeLessThanOrEqual(budget);
}

/** Primary (brand-filled) links on a page must target unique destinations. */
export function expectNoDuplicateCtas(
  container: HTMLElement,
  label = "page",
): void {
  const hrefs = Array.from(
    container.querySelectorAll<HTMLAnchorElement>("a"),
  )
    .filter((a) => /\bbg-brand\b|\bbg-primary\b/.test(a.className))
    .map((a) => a.getAttribute("href") ?? "");
  const seen = new Set<string>();
  const dupes = new Set<string>();
  for (const href of hrefs) {
    if (seen.has(href)) dupes.add(href);
    seen.add(href);
  }
  expect(
    dupes.size,
    `${label} duplicates primary CTA destinations: ${Array.from(dupes).join(", ")}`,
  ).toBe(0);
}
