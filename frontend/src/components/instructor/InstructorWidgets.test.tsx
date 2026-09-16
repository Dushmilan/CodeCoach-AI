import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { RosterTable } from "./InstructorWidgets";

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
