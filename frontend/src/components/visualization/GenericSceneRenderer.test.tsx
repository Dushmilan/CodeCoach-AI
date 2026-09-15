import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { GenericSceneRenderer } from "./GenericSceneRenderer";

const script = {
  title: "Bubble Sort",
  data: { family: "array" },
  steps: [
    {
      narration: "Compare arr[0]=5 vs arr[1]=1",
      shapes: [
        { id: "cell_0", type: "rect", x: -50, y: 0, width: 88, height: 88, fill: "#1e293b", stroke: "#334155" },
        { id: "val_0", type: "text", x: -50, y: 0, text: "5", fontSize: 28, fill: "#e2e8f0" },
      ],
      motion: [{ target: "cell_0", op: "fill", to: "#1d4ed8", duration: 0.35 }],
      camera: { action: "focus", region: [0, 1] },
    },
    {
      narration: "Complexity O(n²) time, O(1) space",
      shapes: [],
      motion: [{ target: "cell_0", op: "scale", to: 1.0, duration: 0.25 }],
      badge: { time: "O(n²)", space: "O(1)" },
    },
  ],
};

describe("GenericSceneRenderer", () => {
  it("renders shapes, narration, and badge", () => {
    render(<GenericSceneRenderer script={script as never} step={script.steps[1] as never} stepIndex={1} />);
    expect(screen.getByText("Complexity O(n²) time, O(1) space")).toBeInTheDocument();
    expect(screen.getByText("O(n²)")).toBeInTheDocument();
  });
  it("skips unknown motion targets without crashing", () => {
    const bad = { ...script.steps[0], motion: [{ target: "nope", op: "fill", to: "#1d4ed8", duration: 0.3 }] };
    const { container } = render(<GenericSceneRenderer script={script as never} step={bad as never} stepIndex={0} />);
    expect(container.querySelector("svg")).toBeInTheDocument();
  });
});
