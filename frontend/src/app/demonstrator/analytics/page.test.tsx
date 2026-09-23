import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  expectBentoStats,
  expectEyebrowBudget,
  expectNoDash,
  expectNoDuplicateCtas,
} from "@/test-helpers/taste";

vi.mock("@/components/header/Header", () => ({
  Header: () => <div data-testid="header" />,
}));

import DemonstratorAnalyticsPage from "./page";

describe("DemonstratorAnalyticsPage", () => {
  it("renders class analytics with taste gates for dash-free copy", async () => {
    const { container } = render(<DemonstratorAnalyticsPage />);
    expect(
      await screen.findByRole("heading", { name: /class analytics/i }),
    ).toBeInTheDocument();
    expect(
      (await screen.findAllByTestId(/^ta-analytics-/)).length,
    ).toBeGreaterThan(0);

    expectNoDash(container, "demonstrator analytics");
    expectEyebrowBudget(container, "demonstrator analytics");
    expectNoDuplicateCtas(container, "demonstrator analytics");
  });

  it("lays classroom stats out as a varied bento", async () => {
    const { container } = render(<DemonstratorAnalyticsPage />);
    await screen.findAllByTestId(/^ta-analytics-/);
    expectBentoStats(container);
  });
});
