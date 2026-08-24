import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import LearningSignals from "./LearningSignals";
import { AnalyticsService } from "./analytics.service";

vi.mock("./analytics.service");

describe("LearningSignals", () => {
  beforeEach(() => vi.resetAllMocks());

  it("shows plateau signal with skill badge", async () => {
    vi.mocked(AnalyticsService.getSignals).mockResolvedValue({
      signals: [{ type: "plateau", skill: "recursion", title: "Recursion plateau detected", detail: "3 failures in last 7 days", evidence: { failures: 3, passes: 0, window_days: 7, question_ids: ["invert-binary-tree"], signatures: ["sig A"] }, severity: "warning", first_seen_at: new Date().toISOString(), last_seen_at: new Date().toISOString() }],
      total: 1,
    });
    render(<LearningSignals />);
    expect(await screen.findByTestId("analytics-signal")).toBeInTheDocument();
    expect(screen.getByText(/Recursion plateau detected/i)).toBeInTheDocument();
  });

  it("shows empty state when no signals", async () => {
    vi.mocked(AnalyticsService.getSignals).mockResolvedValue({ signals: [], total: 0 });
    render(<LearningSignals />);
    expect(await screen.findByText(/No learning signals/i)).toBeInTheDocument();
  });

  it("is empty-safe on fetch failure", async () => {
    vi.mocked(AnalyticsService.getSignals).mockRejectedValue(new Error("network"));
    render(<LearningSignals />);
    expect(await screen.findByText(/No learning signals/i)).toBeInTheDocument();
  });

  it("renders multiple signals sorted by failures", async () => {
    vi.mocked(AnalyticsService.getSignals).mockResolvedValue({
      signals: [
        { type: "plateau", skill: "arrays", title: "Arrays plateau detected", detail: "3 failures", evidence: { failures: 3, passes: 0, window_days: 7, question_ids: [], signatures: [] }, severity: "warning", first_seen_at: new Date().toISOString(), last_seen_at: new Date().toISOString() },
        { type: "plateau", skill: "recursion", title: "Recursion plateau detected", detail: "4 failures", evidence: { failures: 4, passes: 0, window_days: 7, question_ids: [], signatures: [] }, severity: "warning", first_seen_at: new Date().toISOString(), last_seen_at: new Date().toISOString() },
      ],
      total: 2,
    });
    render(<LearningSignals />);
    const items = await screen.findAllByTestId("analytics-signal");
    expect(items).toHaveLength(2);
  });
});
