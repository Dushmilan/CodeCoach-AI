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
  it("resolves numeric camera regions by cell id, not shape position", () => {
    // shapes are cell/val interleaved: positional lookup would average
    // cell_0 (x=-100) with val_0 (x=500) → cx=200. Id lookup averages
    // cell_0 (x=-100) with cell_1 (x=100) → cx=0.
    const step = {
      narration: "Compare",
      shapes: [
        { id: "cell_0", type: "rect", x: -100, y: 0, width: 88, height: 88 },
        { id: "val_0", type: "text", x: 500, y: 0, text: "5", fontSize: 28 },
        { id: "cell_1", type: "rect", x: 100, y: 0, width: 88, height: 88 },
        { id: "val_1", type: "text", x: 500, y: 0, text: "1", fontSize: 28 },
      ],
      motion: [{ target: "cell_0", op: "fill", to: "#1d4ed8", duration: 0.35 }],
      camera: { action: "focus", region: [0, 1] },
    };
    const { container } = render(<GenericSceneRenderer script={script as never} step={step as never} stepIndex={0} />);
    // zoom_focus 1.25 → 1536x864 viewBox centered on cx=0, cy=0.
    expect(container.querySelector("svg")?.getAttribute("viewBox")).toBe("-768 -432 1536 864");
  });
  it("resolves numeric camera regions via node_ ids", () => {
    const step = {
      narration: "Visit",
      shapes: [
        { id: "node_0", type: "rect", x: -230, y: 0, width: 64, height: 44 },
        { id: "node_1", type: "rect", x: 230, y: 0, width: 64, height: 44 },
      ],
      motion: [{ target: "node_1", op: "fill", to: "#1d4ed8", duration: 0.3 }],
      camera: { action: "focus", region: [1] },
    };
    const { container } = render(<GenericSceneRenderer script={script as never} step={step as never} stepIndex={0} />);
    expect(container.querySelector("svg")?.getAttribute("viewBox")).toBe("-538 -432 1536 864");
  });
});
