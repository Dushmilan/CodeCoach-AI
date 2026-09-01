import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryGraph } from "./MemoryGraph";

vi.mock("./memory.service", () => ({
  memoryService: {
    getGraph: vi.fn(),
  },
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

import { memoryService } from "./memory.service";

const mockedGetGraph = vi.mocked(memoryService.getGraph);

describe("MemoryGraph", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders topics sorted by energy cost", async () => {
    mockedGetGraph.mockResolvedValue({
      topics: [
        {
          topic: "Arrays",
          totalCards: 1,
          dueCount: 1,
          avgIntervalDays: 1,
          daysSinceLastTouch: 2,
          lapseCount: 0,
          energyCostMinutes: 6,
          cardIds: ["c1"],
        },
        {
          topic: "DP",
          totalCards: 1,
          dueCount: 1,
          avgIntervalDays: 6,
          daysSinceLastTouch: 6,
          lapseCount: 2,
          energyCostMinutes: 29,
          cardIds: ["c2"],
        },
      ],
      totalDue: 2,
      totalCards: 2,
      oldestDueDays: 1,
    });

    render(<MemoryGraph />);

    await waitFor(() => expect(mockedGetGraph).toHaveBeenCalled());

    const items = await screen.findAllByTestId("memory-topic");
    expect(items).toHaveLength(2);
    // DP has higher energy cost, should be first
    expect(items[0].textContent).toContain("DP");
    expect(items[1].textContent).toContain("Arrays");
  });

  it("shows days-since copy", async () => {
    mockedGetGraph.mockResolvedValue({
      topics: [
        {
          topic: "Recursion",
          totalCards: 1,
          dueCount: 0,
          avgIntervalDays: 4,
          daysSinceLastTouch: 6,
          lapseCount: 0,
          energyCostMinutes: 13,
          cardIds: ["c1"],
        },
      ],
      totalDue: 0,
      totalCards: 1,
      oldestDueDays: null,
    });

    render(<MemoryGraph />);

    expect(await screen.findByText(/6 days since recursion/i)).toBeInTheDocument();
    expect(screen.getByText(/5-min refresher/i)).toBeInTheDocument();
  });

  it("renders empty state when no topics", async () => {
    mockedGetGraph.mockResolvedValue({ topics: [], totalDue: 0, totalCards: 0, oldestDueDays: null });
    render(<MemoryGraph />);

    await waitFor(() => expect(mockedGetGraph).toHaveBeenCalled());
    expect(await screen.findByText(/no memory yet/i)).toBeInTheDocument();
  });

  it("renders nothing when API fails", async () => {
    mockedGetGraph.mockRejectedValue(new Error("offline"));
    render(<MemoryGraph />);
    await waitFor(() => expect(mockedGetGraph).toHaveBeenCalled());
    expect(await screen.findByText(/couldn.t load/i)).toBeInTheDocument();
  });

  it("shows skeleton while loading", async () => {
    let resolve!: (v: unknown) => void;
    mockedGetGraph.mockReturnValue(new Promise((r) => (resolve = r)) as never);
    render(<MemoryGraph />);
    expect(screen.getByTestId("memory-graph-loading")).toBeInTheDocument();
    resolve({ topics: [], totalDue: 0, totalCards: 0, oldestDueDays: null });
    await waitFor(() => expect(mockedGetGraph).toHaveBeenCalled());
  });

  it("renders EmptyState with Browse action when no topics", async () => {
    mockedGetGraph.mockResolvedValue({ topics: [], totalDue: 0, totalCards: 0, oldestDueDays: null });
    render(<MemoryGraph />);
    await waitFor(() => expect(mockedGetGraph).toHaveBeenCalled());
    expect(await screen.findByText(/no memory yet/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /browse problems/i })).toBeInTheDocument();
  });

  it("renders retry action when API fails", async () => {
    mockedGetGraph.mockRejectedValue(new Error("offline"));
    render(<MemoryGraph />);
    await waitFor(() => expect(mockedGetGraph).toHaveBeenCalled());
    expect(await screen.findByRole("button", { name: /retry/i })).toBeInTheDocument();
  });
});
