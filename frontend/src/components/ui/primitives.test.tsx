import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Avatar, AvatarFallback, AvatarImage } from "./avatar";
import { Progress } from "./progress";
import { Separator } from "./separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./tabs";

describe("shadcn owned primitives (issue #230)", () => {
  it("renders tabs with list, triggers and content", () => {
    render(
      <Tabs defaultValue="a">
        <TabsList>
          <TabsTrigger value="a">Alpha</TabsTrigger>
          <TabsTrigger value="b">Beta</TabsTrigger>
        </TabsList>
        <TabsContent value="a">Content A</TabsContent>
        <TabsContent value="b">Content B</TabsContent>
      </Tabs>,
    );
    expect(screen.getByRole("tablist")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Alpha" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Beta" })).toBeInTheDocument();
  });

  it("renders progress with progressbar role and value", () => {
    render(<Progress value={40} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toBeInTheDocument();
    expect(bar).toHaveAttribute("aria-valuenow", "40");
  });

  it("renders avatar fallback when no image loads", () => {
    render(
      <Avatar>
        <AvatarImage src="" alt="Student" />
        <AvatarFallback>ST</AvatarFallback>
      </Avatar>,
    );
    expect(screen.getByText("ST")).toBeInTheDocument();
  });

  it("renders separators with orientation roles", () => {
    const { container } = render(
      <div>
        <Separator />
        <Separator orientation="vertical" />
      </div>,
    );
    const seps = container.querySelectorAll('[data-slot="separator"]');
    expect(seps).toHaveLength(2);
    expect(seps[0]).toHaveAttribute("data-orientation", "horizontal");
    expect(seps[1]).toHaveAttribute("data-orientation", "vertical");
  });
});
