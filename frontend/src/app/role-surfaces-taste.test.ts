import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";

/**
 * Mechanical taste gates for the role surfaces (issues #292 and #230).
 *
 * The scope array grows slice by slice as the admin, professor and
 * demonstrator surfaces are redesigned, so every commit in the series keeps
 * the suite green while each newly scoped file starts red.
 *
 * Gates: zero em/en dashes, one radius system (pills plus 2xl/3xl surfaces),
 * emerald-only accents via tokens (no raw hue utilities), AA-safe brand text
 * (no text-primary on light surfaces), cards/tabs instead of divided lists,
 * no scroll cues, no 01/04 step numbering, WCAG AA token pairs for CTAs and
 * forms in light and dark, an emerald-band accent hue lock, and a global
 * prefers-reduced-motion collapse.
 */

const ROOT = path.resolve(process.cwd());

/**
 * Files scanned by the copy/shape gates. Directories are walked so each
 * slice only has to add its surface; test files and the auth login page are
 * never scanned (login is out of scope for issue #292).
 */
const SCOPED_FILES: string[] = [
  "src/components/ui/card.tsx",
  "src/components/ui/button.tsx",
  "src/components/ui/progress.tsx",
  "src/components/ui/avatar.tsx",
  "src/components/ui/tabs.tsx",
  "src/components/ui/separator.tsx",
  "src/components/ui/Skeleton.tsx",
  "src/components/ui/Toast.tsx",
  "src/components/instructor/InstructorWidgets.tsx",
  "src/components/instructor/InstructorSidebar.tsx",
];

const SCOPED_DIRS = ["src/app/admin", "src/components/admin"];

function collectScopedFiles(): string[] {
  const files = [...SCOPED_FILES];
  for (const dir of SCOPED_DIRS) {
    const abs = path.join(ROOT, dir);
    if (!fs.existsSync(abs)) continue;
    const stack = [abs];
    while (stack.length > 0) {
      const current = stack.pop() as string;
      for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
        const full = path.join(current, entry.name);
        if (entry.isDirectory()) {
          stack.push(full);
          continue;
        }
        if (!/\.(tsx?|css)$/.test(entry.name)) continue;
        if (entry.name.includes(".test.")) continue;
        const rel = path.relative(ROOT, full).split(path.sep).join("/");
        if (rel.includes("/admin/login/")) continue; // auth, out of scope
        files.push(rel);
      }
    }
  }
  return files;
}

const LAYOUT_FILES = [
  "src/app/admin/layout.tsx",
  "src/app/professor/layout.tsx",
  "src/app/demonstrator/layout.tsx",
];

const read = (rel: string) => fs.readFileSync(path.join(ROOT, rel), "utf8");

/** Drop comments so rule lines never trip copy gates. */
function stripComments(src: string): string {
  return src
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|[^:])\/\/[^\n]*/g, "$1");
}

const BANNED_PATTERNS: Array<{ name: string; pattern: RegExp }> = [
  {
    name: "em/en dash (or entity) in copy",
    pattern: /[\u2014\u2012\u2013]|&mdash;|&ndash;|&endash;/,
  },
  {
    name: "radius outside the pill/surface system (rounded-sm/md/lg/xl or bare rounded)",
    pattern: /\brounded(?:-[tblrse]{1,2})?-(?:sm|md|lg|xl)\b|\brounded\b(?![\w-])/,
  },
  {
    name: "raw hue utility (accents must come from tokens)",
    pattern:
      /\b(?:bg|text|border|ring|from|via|to|fill|stroke)-(?:red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose|slate|gray|zinc|neutral|stone)-\d{2,3}/,
  },
  {
    name: "text-primary/text-primary-foreground (use the AA-safe brand token)",
    pattern: /\btext-primary\b(?!-)|\btext-primary-foreground\b/,
  },
  { name: "divided list (use cards/tabs instead)", pattern: /\bdivide-/ },
  { name: "scroll cue", pattern: /\banimate-bounce\b|scroll cue|scroll down/i },
  {
    name: "decorative step numbering (01 / 04)",
    pattern: /\b0\d\s*(?:\/|of)\s*0\d\b/,
  },
];

function scanScopedSources(): string[] {
  const failures: string[] = [];
  for (const rel of collectScopedFiles()) {
    const src = stripComments(read(rel));
    for (const { name, pattern } of BANNED_PATTERNS) {
      if (pattern.test(src)) failures.push(`${rel}: ${name}`);
    }
  }
  return failures;
}

// --- token contrast helpers -------------------------------------------------

type Rgb = [number, number, number];

function parseHsl(value: string): { h: number; s: number; l: number } | null {
  const parts = value.trim().split(/\s+/);
  if (parts.length < 3) return null;
  const h = Number.parseFloat(parts[0]);
  const s = Number.parseFloat(parts[1]) / 100;
  const l = Number.parseFloat(parts[2]) / 100;
  if ([h, s, l].some((n) => Number.isNaN(n))) return null;
  return { h, s, l };
}

function hslToRgb({ h, s, l }: { h: number; s: number; l: number }): Rgb {
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const hp = (((h % 360) + 360) % 360) / 60;
  const x = c * (1 - Math.abs((hp % 2) - 1));
  const seg = [
    [c, x, 0],
    [x, c, 0],
    [0, c, x],
    [0, x, c],
    [x, 0, c],
    [c, 0, x],
  ][Math.min(5, Math.floor(hp))];
  const m = l - c / 2;
  return [(seg[0] + m) * 255, (seg[1] + m) * 255, (seg[2] + m) * 255];
}

function channelLuminance(v: number): number {
  const cs = v / 255;
  return cs <= 0.04045 ? cs / 12.92 : ((cs + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance(rgb: Rgb): number {
  return (
    0.2126 * channelLuminance(rgb[0]) +
    0.7152 * channelLuminance(rgb[1]) +
    0.0722 * channelLuminance(rgb[2])
  );
}

function contrastRatio(a: number, b: number): number {
  const [hi, lo] = a > b ? [a, b] : [b, a];
  return (hi + 0.05) / (lo + 0.05);
}

function tokensOf(css: string, selector: string): Record<string, string> {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const block = css.match(new RegExp(`${escaped}\\s*\\{([^}]*)\\}`));
  if (!block) return {};
  const out: Record<string, string> = {};
  for (const line of block[1].split(";")) {
    const m = line.match(/(--[\w-]+)\s*:\s*([^;]+)/);
    if (m) out[m[1]] = m[2].trim();
  }
  return out;
}

const CONTRAST_PAIRS: Array<{ fg: string; bg: string; min: number }> = [
  { fg: "foreground", bg: "background", min: 4.5 },
  { fg: "foreground", bg: "card", min: 4.5 },
  { fg: "muted-foreground", bg: "background", min: 4.5 },
  { fg: "muted-foreground", bg: "card", min: 4.5 },
  { fg: "brand-foreground", bg: "brand", min: 4.5 },
  { fg: "brand", bg: "card", min: 4.5 },
  { fg: "brand", bg: "background", min: 4.5 },
  { fg: "success", bg: "card", min: 4.5 },
  { fg: "warning", bg: "card", min: 4.5 },
  { fg: "destructive", bg: "card", min: 4.5 },
  { fg: "ring", bg: "background", min: 3 },
];

function contrastFailures(css: string): string[] {
  const failures: string[] = [];
  for (const theme of [":root", ".dark"]) {
    const tokens = tokensOf(css, theme);
    for (const { fg, bg, min } of CONTRAST_PAIRS) {
      const fgRaw = tokens[`--${fg}`];
      const bgRaw = tokens[`--${bg}`];
      if (!fgRaw || !bgRaw) {
        failures.push(`${theme}: missing --${!fgRaw ? fg : bg}`);
        continue;
      }
      const fgHsl = parseHsl(fgRaw);
      const bgHsl = parseHsl(bgRaw);
      if (!fgHsl || !bgHsl) {
        failures.push(`${theme}: unparseable --${!fgHsl ? fg : bg}`);
        continue;
      }
      const ratio = contrastRatio(
        relativeLuminance(hslToRgb(fgHsl)),
        relativeLuminance(hslToRgb(bgHsl)),
      );
      if (ratio < min) {
        failures.push(
          `${theme}: ${fg} on ${bg} = ${ratio.toFixed(2)}:1 (needs ${min}:1)`,
        );
      }
    }
  }
  return failures;
}

function hueFailures(css: string): string[] {
  const failures: string[] = [];
  for (const theme of [":root", ".dark"]) {
    const tokens = tokensOf(css, theme);
    for (const name of ["primary", "ring", "brand"]) {
      const raw = tokens[`--${name}`];
      const hsl = raw ? parseHsl(raw) : null;
      if (!hsl) {
        failures.push(`${theme}: missing or unparseable --${name}`);
        continue;
      }
      if (hsl.h < 150 || hsl.h > 170) {
        failures.push(`${theme}: --${name} hue ${hsl.h} outside emerald band`);
      }
    }
  }
  return failures;
}

// --- gates ------------------------------------------------------------------

describe("role surface source gates (issues #292/#230)", () => {
  it("keeps copy, radius, accent, list and numbering rules across scoped files", () => {
    expect(scanScopedSources()).toEqual([]);
  });

  it("collapses CSS motion under prefers-reduced-motion", () => {
    const css = read("src/app/globals.css");
    const block = css.match(
      /@media \(prefers-reduced-motion: reduce\)\s*\{([\s\S]*?)\n\}/,
    );
    expect(block, "a reduced-motion media block must exist").not.toBeNull();
    const body = block?.[1] ?? "";
    expect(body).toMatch(/animation-duration:\s*[\d.]+m?s\s*!important/);
    expect(body).toMatch(/transition-duration:\s*[\d.]+m?s\s*!important/);
    expect(body).toMatch(/scroll-behavior:\s*auto\s*!important/);
  });

  it.each(LAYOUT_FILES)("%s wraps content in MotionConfig reducedMotion=user", (rel) => {
    const src = stripComments(read(rel));
    expect(src).toMatch(/reducedMotion=["']user["']/);
  });
});

describe("role surface token gates (issues #292/#230)", () => {
  const css = read("src/app/globals.css");

  it("meets WCAG AA (4.5:1) for CTA/form token pairs in light and dark", () => {
    expect(contrastFailures(css)).toEqual([]);
  });

  it("keeps accent hues (primary, ring, brand) in the emerald band", () => {
    expect(hueFailures(css)).toEqual([]);
  });
});
