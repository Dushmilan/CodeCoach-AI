import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MessageList } from "./MessageList";
import { ChatMessage } from "@/types";

const baseMessage: ChatMessage = {
  id: "1",
  role: "user",
  content: "Hello",
  timestamp: new Date("2024-01-01T12:00:00"),
};

describe("MessageList", () => {
  it("renders user messages aligned to the right", () => {
    render(<MessageList messages={[baseMessage]} isTyping={false} />);
    const container = screen.getByText("Hello").closest(".flex");
    expect(container?.className).toContain("justify-end");
  });

  it("renders assistant messages aligned to the left", () => {
    const assistantMsg: ChatMessage = {
      ...baseMessage,
      id: "2",
      role: "assistant",
      content: "Hi there",
    };
    render(<MessageList messages={[assistantMsg]} isTyping={false} />);
    const container = screen.getByText("Hi there").closest(".flex");
    expect(container?.className).toContain("justify-start");
  });

  it("renders multiple messages", () => {
    const msgs: ChatMessage[] = [
      baseMessage,
      { ...baseMessage, id: "2", role: "assistant", content: "Reply" },
    ];
    render(<MessageList messages={msgs} isTyping={false} />);
    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Reply")).toBeInTheDocument();
  });

  it("shows typing indicator when isTyping is true", () => {
    const { container } = render(<MessageList messages={[]} isTyping />);
    const dots = container.querySelectorAll(".animate-bounce");
    expect(dots.length).toBe(3);
  });

  it("does not show typing indicator when isTyping is false", () => {
    const { container } = render(
      <MessageList messages={[]} isTyping={false} />,
    );
    expect(container.querySelector(".animate-bounce")).not.toBeInTheDocument();
  });

  it("renders structured response for assistant messages with structured data", () => {
    const structuredMsg: ChatMessage = {
      ...baseMessage,
      id: "3",
      role: "assistant",
      content: "Here is help",
      structured: {
        summary: "Great work",
        hints: ["Try X"],
        code_review: null,
        complexity_analysis: null,
        suggestions: [],
        edge_cases: [],
        explanation: null,
        debug_help: null,
      },
      timestamp: new Date(),
    };
    render(<MessageList messages={[structuredMsg]} isTyping={false} />);
    expect(screen.getByText("Great work")).toBeInTheDocument();
  });
});
