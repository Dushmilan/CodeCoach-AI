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

import DemonstratorClassroomsPage from "./page";

describe("DemonstratorClassroomsPage", () => {
  it("renders assigned classrooms read-only with taste gates", async () => {
    const { container } = render(<DemonstratorClassroomsPage />);
    expect(
      await screen.findByTestId("ta-classroom-list"),
    ).toBeInTheDocument();
    const openLinks = screen.getAllByRole("link", { name: /open classroom/i });
    expect(openLinks.length).toBeGreaterThan(0);
    expect(openLinks[0].className).toMatch(/bg-brand/);

    expectNoDash(container, "demonstrator classrooms");
    expectEyebrowBudget(container, "demonstrator classrooms");
    expectNoDuplicateCtas(container, "demonstrator classrooms");
  });
});
