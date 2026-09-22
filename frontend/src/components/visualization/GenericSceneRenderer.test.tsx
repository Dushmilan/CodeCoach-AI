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
  it("keeps intro shapes visible on beats with empty shapes (#240)", () => {
    // Planners emit shapes only in the intro beat; later beats carry
    // shapes: [] with action motions. The scene must persist.
    const { container } = render(
      <GenericSceneRenderer script={script as never} step={script.steps[1] as never} stepIndex={1} />,
    );
    expect(container.querySelector('rect')).toBeInTheDocument();
  });
  it("zooms focus camera on beats with empty shapes (#240)", () => {
    const actionBeat = {
      narration: "Search region [0..1]",
      shapes: [],
      motion: [{ target: "cell_0", op: "stroke", to: "#facc15", duration: 0.35 }],
      camera: { action: "focus", region: [0, 1] },
    };
    const scene = { ...script, steps: [script.steps[0], actionBeat] };
    const { container } = render(
      <GenericSceneRenderer script={scene as never} step={actionBeat as never} stepIndex={1} />,
    );
    // Resolved against the cumulative scene (cell_0 x=-50): must not fall
    // back to the full viewBox.
    expect(container.querySelector("svg")?.getAttribute("viewBox")).not.toBe(
      "-960 -540 1920 1080",
    );
  });
  it("persists prior-beat highlight overrides (#240)", () => {
    const highlightBeat = {
      narration: "Inspect mid",
      shapes: [],
      motion: [{ target: "cell_0", op: "fill", to: "#1d4ed8", duration: 0.35 }],
    };
    const laterBeat = { narration: "Search region", shapes: [], motion: [] };
    const scene = { ...script, steps: [script.steps[0], highlightBeat, laterBeat] };
    const { container } = render(
      <GenericSceneRenderer script={scene as never} step={laterBeat as never} stepIndex={2} />,
    );
    const rects = container.querySelectorAll("rect");
    expect(rects.length).toBeGreaterThan(0);
    expect(rects[0].getAttribute("fill")).toBe("#1d4ed8");
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
