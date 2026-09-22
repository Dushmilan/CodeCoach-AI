import { describe, it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";

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

describe("landing contracts (preserved IA, issue #230)", () => {
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

describe("landing taste gates (issue #230)", () => {
  it("contains zero em-dashes or en-dashes in visible copy", () => {
    const { container } = renderLanding();
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/[—–]/);
  });

  it("has no div-bar fake algorithm preview", () => {
    const { container } = renderLanding();
    expect(container.querySelectorAll(".sort-bar")).toHaveLength(0);
  });

  it("keeps the hero subtext within 20 words", () => {
    renderLanding();
    const subtext = screen.getByTestId("hero-subtext").textContent ?? "";
    const words = subtext.trim().split(/\s+/).filter(Boolean);
    expect(words.length).toBeLessThanOrEqual(20);
  });

  it("shows a real visual in the hero, not text alone", () => {
    renderLanding();
    const hero = screen.getByTestId("hero-visual");
    const img = within(hero).getByRole("img");
    expect(img).toHaveAttribute("alt");
    expect(img.getAttribute("alt")).not.toHaveLength(0);
  });
});
