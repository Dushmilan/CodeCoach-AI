import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import {
  expectEyebrowBudget,
  expectNoDash,
  expectNoDuplicateCtas,
} from "@/test-helpers/taste";

vi.mock("@/providers", () => ({
  useAuth: () => ({
    user: { id: "admin-1", username: "admin", role: "admin" },
    token: "t",
    isAuthenticated: true,
    isHydrated: true,
  }),
}));

import QuestionsPage from "./page";

const questionsPayload = {
  questions: [
    {
      id: "two-sum",
      title: "Two Sum",
      difficulty: "easy",
      category: "arrays",
      solution: "hash map",
    },
    {
      id: "lru-cache",
      title: "LRU Cache",
      difficulty: "hard",
      category: "design",
      solution: null,
    },
  ],
  total: 2,
};

describe("Admin questions page", () => {
  it("switches list, create and import through pill tabs", async () => {
    server.use(
      http.get("/api/admin/questions", () =>
        HttpResponse.json(questionsPayload),
      ),
    );
    const { container } = render(<QuestionsPage />);

    expect(await screen.findByText("Two Sum")).toBeInTheDocument();
    const tabs = screen.getAllByRole("tab");
    expect(tabs).toHaveLength(3);
    expect(tabs[0]).toHaveAttribute("data-state", "active");

    // Create tab reveals the question form without a URL change.
    // Radix tabs activate on mousedown, so use a full user click.
    const user = userEvent.setup();
    await user.click(screen.getByRole("tab", { name: /add question/i }));
    expect(await screen.findByPlaceholderText("Two Sum")).toBeInTheDocument();

    // Import tab reveals the JSON import panel.
    await user.click(screen.getByRole("tab", { name: /import json/i }));
    expect(
      await screen.findByPlaceholderText(/\[\{ "title"/),
    ).toBeInTheDocument();

    expectNoDash(container, "admin questions");
    expectEyebrowBudget(container, "admin questions");
    expectNoDuplicateCtas(container, "admin questions");
  });

  it("renders difficulty and solution status with tokens", async () => {
    server.use(
      http.get("/api/admin/questions", () =>
        HttpResponse.json(questionsPayload),
      ),
    );
    render(<QuestionsPage />);
    expect(await screen.findByText("Two Sum")).toBeInTheDocument();
    expect(screen.getByText("easy")).toBeInTheDocument();
    expect(screen.getByText("hard")).toBeInTheDocument();
    expect(screen.getByText(/has solution/i)).toBeInTheDocument();
    expect(screen.getByText("LRU Cache").closest("tr")).toBeTruthy();
  });
});
