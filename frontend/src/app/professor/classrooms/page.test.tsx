import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "@/mocks/server";
import {
  expectEyebrowBudget,
  expectNoDash,
  expectNoDuplicateCtas,
} from "@/test-helpers/taste";

vi.mock("@/components/header/Header", () => ({
  Header: () => <div data-testid="header" />,
}));

import ProfessorClassroomsPage from "./page";

describe("ProfessorClassroomsPage", () => {
  it("renders owned classrooms with meters, invite codes and taste gates", async () => {
    const { container } = render(<ProfessorClassroomsPage />);
    expect(await screen.findByTestId("prof-classroom-list")).toBeInTheDocument();
    expect(await screen.findByText(/CS101 · Section A/)).toBeInTheDocument();
    expect(
      container.querySelectorAll('[role="progressbar"]').length,
    ).toBeGreaterThan(0);
    const openLinks = screen.getAllByRole("link", { name: /open classroom/i });
    expect(openLinks.length).toBeGreaterThan(0);
    expect(openLinks[0].className).toMatch(/bg-brand/);

    expectNoDash(container, "professor classrooms");
    expectEyebrowBudget(container, "professor classrooms");
    expectNoDuplicateCtas(container, "professor classrooms");
  });
});
