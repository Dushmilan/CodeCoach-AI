import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

const mockUseTheme = vi.hoisted(() => vi.fn());
const mockUseAuth = vi.hoisted(() =>
  vi.fn(() => ({
    user: null,
    isAuthenticated: false,
    isHydrated: true,
    isLoading: false,
    logout: vi.fn(),
  })),
);

vi.mock("next-themes", () => ({
  useTheme: mockUseTheme,
}));

vi.mock("@/providers", () => ({
  useAuth: mockUseAuth,
}));

vi.mock("@/components/settings/SettingsModal", () => ({
  SettingsModal: () => null,
}));

import LandingPage from "./page";

if (typeof window !== "undefined" && !window.IntersectionObserver) {
  class MockIntersectionObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  window.IntersectionObserver =
    MockIntersectionObserver as unknown as typeof IntersectionObserver;
}

function renderLanding() {
  mockUseTheme.mockReturnValue({
    theme: "dark",
    setTheme: vi.fn(),
    resolvedTheme: "dark",
  });
  return render(<LandingPage />);
}

describe("landing contracts (preserved IA)", () => {
  it("keeps the hero heading and primary CTAs", () => {
    renderLanding();
    expect(
      screen.getByRole("heading", { name: /a free ai-powered/i }),
    ).toBeInTheDocument();
    const startLinks = screen.getAllByRole("link", {
      name: /start practicing/i,
    });
    expect(startLinks.length).toBeGreaterThan(0);
    expect(startLinks[0]).toHaveAttribute("href", "/problems");
    const curriculumLinks = screen.getAllByRole("link", {
      name: /view curriculum/i,
    });
    expect(curriculumLinks.length).toBeGreaterThan(0);
    expect(curriculumLinks[0]).toHaveAttribute("href", "/learn");
  });

  it("keeps the features section heading", () => {
    renderLanding();
    expect(
      screen.getByRole("heading", { name: /why codecoach ai/i }),
    ).toBeInTheDocument();
  });
});

describe("restored pre-redesign landing (issue #291)", () => {
  it("shows the centered hero headline ending in university students", () => {
    renderLanding();
    expect(
      screen.getByRole("heading", {
        level: 1,
        name: /a free ai-powered\s*coding platform for\s*university students/i,
      }),
    ).toBeInTheDocument();
  });

  it("shows the bullet-separated eyebrow pill", () => {
    renderLanding();
    expect(
      screen.getByText(/free • open source • ai-powered/i),
    ).toBeInTheDocument();
  });

  it("renders the feature grid with colored left-border accents", () => {
    const { container } = renderLanding();
    for (const accent of [
      "border-l-emerald-500/40",
      "border-l-blue-500/40",
      "border-l-violet-500/40",
      "border-l-amber-500/40",
    ]) {
      expect(container.querySelector(`[class*="${accent}"]`)).not.toBeNull();
    }
  });

  it("uses the ampersand wording for the open-source feature title", () => {
    renderLanding();
    expect(
      screen.getByRole("heading", { name: /open source & professor-ready/i }),
    ).toBeInTheDocument();
  });

  it("renders the four audience cards as headings, including professors", () => {
    renderLanding();
    for (const name of [
      /interview grinders/i,
      /struggling students/i,
      /curious learners/i,
      /^professors$/i,
    ]) {
      expect(screen.getByRole("heading", { name })).toBeInTheDocument();
    }
  });

  it("renders the div-bar algorithm preview in the showcase", () => {
    const { container } = renderLanding();
    expect(container.querySelectorAll(".sort-bar").length).toBeGreaterThan(0);
  });

  it("has no split-hero visual or subtext testids from the redesign", () => {
    renderLanding();
    expect(screen.queryByTestId("hero-visual")).toBeNull();
    expect(screen.queryByTestId("hero-subtext")).toBeNull();
  });
});
