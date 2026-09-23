import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MasteryBars, RosterTable, StatCard } from "./InstructorWidgets";

describe("RosterTable (Issue #177)", () => {
  it("renders the live username handle alongside the display name", () => {
    render(
      <RosterTable
        detailBase="/professor/students"
        students={[
          {
            userId: "stu-live-01",
            name: "mia.live",
            username: "mia.live",
            completionPct: 80,
            solved: 12,
            attempted: 20,
            lastActive: "",
          },
          {
            userId: "stu-live-02",
            name: "stu-live-02",
            username: "stu-live-02",
            completionPct: 10,
            solved: 3,
            attempted: 15,
            lastActive: "",
          },
        ]}
      />,
    );
    // The live username must be visible as a handle so the roster never
    // shows bare user ids when the API provides a username.
    expect(screen.getByText("@mia.live")).toBeInTheDocument();
    expect(screen.getByText("@stu-live-02")).toBeInTheDocument();
  });
});

describe("StatCard bento restyle (issue #292)", () => {
  it("marks the cell for bento rhythm checks", () => {
    render(<StatCard label="Students" value={12} testId="stat-students" />);
    expect(screen.getByTestId("stat-students").closest("[data-stat]")).not.toBeNull();
  });

  it("renders a featured cell with a progress meter", () => {
    render(<StatCard label="Avg completion" value="61%" progress={61} featured />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "61");
  });

  it("accepts a className so pages can span cells in the bento grid", () => {
    const { container } = render(
      <StatCard label="Courses" value={4} className="lg:col-span-2" />,
    );
    expect(container.querySelector("[data-stat]")).toHaveClass("lg:col-span-2");
  });

  it("renders an optional accent icon chip", () => {
    function DummyIcon() {
      return <svg data-testid="stat-icon" />;
    }
    render(<StatCard label="Users" value={3} icon={DummyIcon} />);
    expect(screen.getByTestId("stat-icon")).toBeInTheDocument();
  });
});

describe("MasteryBars progress meters (issue #292)", () => {
  it("renders each mastery row as an accessible progress meter", () => {
    render(
      <MasteryBars
        items={[
          { label: "Arrays", avgMastery: 0.72 },
          { label: "Graphs", avgMastery: 0.4 },
        ]}
      />,
    );
    const bars = screen.getAllByRole("progressbar");
    expect(bars).toHaveLength(2);
    expect(bars[0]).toHaveAttribute("aria-valuenow", "72");
    expect(bars[1]).toHaveAttribute("aria-valuenow", "40");
    expect(screen.getByText("72%")).toBeInTheDocument();
  });
});

describe("RosterTable person rows (issue #292)", () => {
  it("shows an avatar initial and a completion meter per student", () => {
    render(
      <RosterTable
        detailBase="/professor/students"
        students={[
          {
            userId: "s-1",
            name: "mia.live",
            username: "mia.live",
            completionPct: 80,
            solved: 12,
            attempted: 20,
            lastActive: "",
          },
          {
            userId: "s-2",
            name: "leo.codes",
            username: "leo.codes",
            completionPct: 35,
            solved: 4,
            attempted: 18,
            lastActive: "",
          },
        ]}
      />,
    );
    expect(screen.getAllByTestId("roster-avatar")).toHaveLength(2);
    expect(screen.getAllByRole("progressbar")).toHaveLength(2);
    expect(screen.getByText("80%")).toBeInTheDocument();
  });
});
