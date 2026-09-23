import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import {
  expectEyebrowBudget,
  expectNoDash,
  expectNoDuplicateCtas,
} from "@/test-helpers/taste";

vi.mock("@/providers", () => ({
  useAuth: () => ({
    user: { id: "admin-1", username: "admin", role: "super_admin" },
    token: "t",
    isAuthenticated: true,
    isHydrated: true,
  }),
}));

import UsersPage from "./page";

const usersPayload = {
  users: [
    {
      id: "u-1",
      username: "admin",
      email: "admin@example.test",
      role: "super_admin",
      is_active: true,
      created_at: "2026-01-01T00:00:00Z",
    },
    {
      id: "u-2",
      username: "student.mia",
      email: "mia@example.test",
      role: "user",
      is_active: false,
      created_at: "2026-02-01T00:00:00Z",
    },
  ],
  total: 2,
};

describe("Admin users page", () => {
  it("renders each user with an avatar chip, role and status", async () => {
    server.use(
      http.get("/api/admin/users", () => HttpResponse.json(usersPayload)),
    );
    const { container } = render(<UsersPage />);

    expect(await screen.findByText("student.mia")).toBeInTheDocument();
    expect(screen.getAllByTestId("user-avatar")).toHaveLength(2);
    expect(
      screen.getByText("super_admin", { selector: "span.rounded-full" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Inactive")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/search users/i)).toBeInTheDocument();

    expectNoDash(container, "admin users");
    expectEyebrowBudget(container, "admin users");
    expectNoDuplicateCtas(container, "admin users");
  });

  it("keeps the empty state when the directory has no users", async () => {
    server.use(
      http.get("/api/admin/users", () =>
        HttpResponse.json({ users: [], total: 0 }),
      ),
    );
    render(<UsersPage />);
    expect(await screen.findByText(/no users found/i)).toBeInTheDocument();
  });
});
