import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

const usePathname = vi.hoisted(() => vi.fn(() => "/professor"));

vi.mock("next/navigation", () => ({
  usePathname,
}));

import { InstructorSidebar } from "./InstructorSidebar";

describe("InstructorSidebar (issues #292/#230)", () => {
  it("keeps the professor nav labels and hrefs (IA preserved)", () => {
    usePathname.mockReturnValue("/professor");
    render(<InstructorSidebar base="professor" />);
    const expected = [
      ["Overview", "/professor"],
      ["Courses", "/professor/courses"],
      ["Curriculum", "/professor/curriculum"],
      ["Classrooms", "/professor/classrooms"],
      ["Class Analytics", "/professor/analytics"],
    ] as const;
    for (const [label, href] of expected) {
      expect(screen.getByRole("link", { name: label })).toHaveAttribute(
        "href",
        href,
      );
    }
  });

  it("keeps the demonstrator nav labels and hrefs (IA preserved)", () => {
    usePathname.mockReturnValue("/demonstrator");
    render(<InstructorSidebar base="demonstrator" />);
    const expected = [
      ["Overview", "/demonstrator"],
      ["Classrooms", "/demonstrator/classrooms"],
      ["Class Analytics", "/demonstrator/analytics"],
    ] as const;
    for (const [label, href] of expected) {
      expect(screen.getByRole("link", { name: label })).toHaveAttribute(
        "href",
        href,
      );
    }
  });

  it("marks the active destination as a pill link with aria-current", () => {
    usePathname.mockReturnValue("/professor/courses");
    render(<InstructorSidebar base="professor" />);
    const active = screen.getByRole("link", { name: "Courses" });
    expect(active).toHaveAttribute("aria-current", "page");
    expect(active.className).toMatch(/rounded-full/);
    expect(active.className).toMatch(/bg-brand\b/);
  });

  it("marks only the most specific destination as active", () => {
    usePathname.mockReturnValue("/professor/courses");
    render(<InstructorSidebar base="professor" />);
    const current = document.querySelectorAll('[aria-current="page"]');
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Courses");
  });
});
