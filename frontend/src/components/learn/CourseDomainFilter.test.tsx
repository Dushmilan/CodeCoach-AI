import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CourseDomainFilter } from "./CourseDomainFilter";
import type { CourseSummary } from "@/types";

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

const courses: CourseSummary[] = [
  {
    id: "python-fundamentals",
    title: "Python Fundamentals",
    description: "Python course",
    language: "python",
    icon: "python",
    domain: "se",
    order: 1,
    progress: 0,
  },
  {
    id: "intro-to-machine-learning",
    title: "Intro to ML",
    description: "ML course",
    language: "python",
    icon: "ml",
    domain: "ml",
    order: 2,
    progress: 0,
  },
  {
    id: "prompt-engineering",
    title: "Prompt Engineering",
    description: "AI course",
    language: "python",
    icon: "prompt",
    domain: "ai",
    order: 3,
    progress: 0,
  },
];

function renderFilter() {
  return render(
    <CourseDomainFilter
      courses={courses}
      renderCourse={(c) => <div>{c.title}</div>}
    />,
  );
}

describe("CourseDomainFilter", () => {
  it("renders tabs for All, SE, ML, and AI", () => {
    renderFilter();
    expect(screen.getByRole("tab", { name: "All" })).toBeInTheDocument();
    expect(
      screen.getByRole("tab", { name: /Software Engineering/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("tab", { name: /Machine Learning/ }),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "AI" })).toBeInTheDocument();
  });

  it("shows all courses by default", () => {
    renderFilter();
    expect(screen.getByText("Python Fundamentals")).toBeInTheDocument();
    expect(screen.getByText("Intro to ML")).toBeInTheDocument();
    expect(screen.getByText("Prompt Engineering")).toBeInTheDocument();
  });

  it("filters to ML courses when the ML tab is clicked", async () => {
    const user = userEvent.setup();
    renderFilter();
    await user.click(screen.getByRole("tab", { name: /Machine Learning/ }));
    expect(screen.queryByText("Python Fundamentals")).not.toBeInTheDocument();
    expect(screen.getByText("Intro to ML")).toBeInTheDocument();
    expect(screen.queryByText("Prompt Engineering")).not.toBeInTheDocument();
  });

  it("filters to AI courses when the AI tab is clicked", async () => {
    const user = userEvent.setup();
    renderFilter();
    await user.click(screen.getByRole("tab", { name: "AI" }));
    expect(screen.getByText("Prompt Engineering")).toBeInTheDocument();
    expect(screen.queryByText("Intro to ML")).not.toBeInTheDocument();
    expect(screen.queryByText("Python Fundamentals")).not.toBeInTheDocument();
  });
});
