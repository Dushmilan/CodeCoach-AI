import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { Skeleton } from "./Skeleton";

describe("Skeleton (issue #292 light parity)", () => {
  it("uses muted tokens so it is visible in both themes", () => {
    const { container } = render(<Skeleton className="h-10 rounded-2xl" />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.className).toContain("bg-muted");
    expect(el.className).not.toContain("bg-white/");
    expect(el.className).toContain("animate-pulse");
    expect(el).toHaveAttribute("aria-hidden", "true");
  });
});
