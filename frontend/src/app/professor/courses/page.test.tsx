import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  expectEyebrowBudget,
  expectNoDash,
  expectNoDuplicateCtas,
} from "@/test-helpers/taste";

vi.mock("@/components/header/Header", () => ({
  Header: () => <div data-testid="header" />,
}));

import ProfessorCoursesPage from "./page";

describe("ProfessorCoursesPage", () => {
  it("renders the course list with its validation chip and curriculum CTA", () => {
    const { container } = render(<ProfessorCoursesPage />);
    expect(screen.getByTestId("prof-courses")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /create \/ edit in curriculum/i }),
    ).toHaveAttribute("href", "/professor/curriculum");
    expect(screen.getAllByText(/full_validate · animation passed/)).toHaveLength(
      2,
    );

    expectNoDash(container, "professor courses");
    expectEyebrowBudget(container, "professor courses");
    expectNoDuplicateCtas(container, "professor courses");
  });
});
