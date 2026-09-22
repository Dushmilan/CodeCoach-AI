import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import {
  expectEyebrowBudget,
  expectNoDash,
  expectNoDuplicateCtas,
} from "@/test-helpers/taste";

import CurriculumPage from "./page";

const treePayload = {
  courses: [
    {
      id: "python-fundamentals",
      title: "Python Fundamentals",
      language: "python",
      order: 1,
      description: "Core Python",
    },
  ],
  modules: [],
  lessons: [],
};

describe("Admin curriculum page", () => {
  it("renders the course tree with its management controls", async () => {
    server.use(
      http.get("/api/admin/courses/tree", () =>
        HttpResponse.json(treePayload),
      ),
    );
    const { container } = render(<CurriculumPage />);

    expect(
      await screen.findByText("Python Fundamentals"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /add course/i }),
    ).toBeInTheDocument();

    expectNoDash(container, "admin curriculum");
    expectEyebrowBudget(container, "admin curriculum");
    expectNoDuplicateCtas(container, "admin curriculum");
  });

  it("opens the side drawer with the course form (field names preserved)", async () => {
    server.use(
      http.get("/api/admin/courses/tree", () =>
        HttpResponse.json(treePayload),
      ),
    );
    render(<CurriculumPage />);

    fireEvent.click(await screen.findByRole("button", { name: /add course/i }));
    await waitFor(() =>
      expect(screen.getByText("New course")).toBeInTheDocument(),
    );
    // Form field labels must survive the redesign (contract per issue #292).
    expect(screen.getByText("ID *")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Python Fundamentals"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /^create$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /cancel/i }),
    ).toBeInTheDocument();
  });
});
