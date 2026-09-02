import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import StudentDashboardPage from "./page";

vi.mock("@/components/header/Header", () => ({ Header: () => <div data-testid="header" /> }));
vi.mock("@/features/analytics/LearningSignals", () => ({ default: () => <div data-testid="signals" /> }));
vi.mock("@/features/memory/MemoryGraph", () => ({ MemoryGraph: () => <div data-testid="memory-graph" /> }));
vi.mock("@/features/rescue/RescueDueQueue", () => ({ RescueDueQueue: () => <div data-testid="rescue-queue" /> }));
vi.mock("@/features/review/ReviewsDueQueue", () => ({ ReviewsDueQueue: () => <div data-testid="reviews-queue" /> }));
vi.mock("@/features/question/question.hook", () => ({
  useQuestion: () => ({ allQuestions: [], loadQuestions: vi.fn() }),
}));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

describe("StudentDashboardPage polish", () => {
  it("renders memory-first heading and dashboard queues", () => {
    render(<StudentDashboardPage />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("memory-graph")).toBeInTheDocument();
  });

  it("shows Replay tour button", () => {
    render(<StudentDashboardPage />);
    expect(screen.getByRole("button", { name: /replay tour/i })).toBeInTheDocument();
  });

  it("shows CTA to start practicing when empty", () => {
    render(<StudentDashboardPage />);
    // CTA link to /problems should be present as memory-first entry point
    expect(screen.getByRole("link", { name: /start practicing|browse problems/i })).toBeInTheDocument();
  });
});
