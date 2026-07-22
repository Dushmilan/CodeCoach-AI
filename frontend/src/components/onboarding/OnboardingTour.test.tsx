import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { OnboardingTour } from "./OnboardingTour";

const mockSetItem = vi.fn();

beforeEach(() => {
  vi.spyOn(Storage.prototype, "getItem").mockReturnValue(null);
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(mockSetItem);
  mockSetItem.mockReset();
});

describe("OnboardingTour", () => {
  it("renders when no stored completion flag", () => {
    render(<OnboardingTour />);
    expect(screen.getByText("Welcome to CodeCoach AI")).toBeInTheDocument();
  });

  it("does not render when onboarding is already done", () => {
    vi.spyOn(Storage.prototype, "getItem").mockReturnValue(
      JSON.stringify(true),
    );
    const { container } = render(<OnboardingTour />);
    expect(container.innerHTML).toBe("");
  });

  it("navigates through steps", async () => {
    const user = userEvent.setup();
    render(<OnboardingTour />);

    expect(screen.getByText("Welcome to CodeCoach AI")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /next/i }));
    expect(screen.getByText("Question Browser")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /next/i }));
    expect(screen.getByText("AI Coach")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /next/i }));
    expect(screen.getByText("NVIDIA API Key")).toBeInTheDocument();
  });

  it("completes tour on last step", async () => {
    const user = userEvent.setup();
    render(<OnboardingTour />);

    for (let i = 0; i < 3; i++) {
      await user.click(screen.getByRole("button", { name: /next/i }));
    }

    await user.click(screen.getByRole("button", { name: /get started/i }));
    expect(
      screen.queryByText("Welcome to CodeCoach AI"),
    ).not.toBeInTheDocument();
  });

  it("dismisses tour on close", async () => {
    const user = userEvent.setup();
    render(<OnboardingTour />);

    await user.click(screen.getByLabelText("Dismiss tour"));
    expect(
      screen.queryByText("Welcome to CodeCoach AI"),
    ).not.toBeInTheDocument();
  });

  it("goes back to previous step", async () => {
    const user = userEvent.setup();
    render(<OnboardingTour />);

    await user.click(screen.getByRole("button", { name: /next/i }));
    expect(screen.getByText("Question Browser")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /back/i }));
    expect(screen.getByText("Welcome to CodeCoach AI")).toBeInTheDocument();
  });
});
