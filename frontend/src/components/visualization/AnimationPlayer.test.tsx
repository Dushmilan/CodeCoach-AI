import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AnimationPlayer } from "./AnimationPlayer";

const steps = [{ narration: "One" }, { narration: "Two" }, { narration: "Three" }];

describe("AnimationPlayer scrub", () => {
  it("scrubs via slider and announces narration", () => {
    render(<AnimationPlayer steps={steps as never}>{(s) => <div>{(s as { narration: string }).narration}</div>}</AnimationPlayer>);
    fireEvent.change(screen.getByRole("slider", { name: /animation progress/i }), { target: { value: "2" } });
    expect(screen.getByText("Three")).toBeInTheDocument();
  });
});
