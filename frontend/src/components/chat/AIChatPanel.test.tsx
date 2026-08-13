import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AIChatPanel } from "./AIChatPanel";

describe("AIChatPanel", () => {
  const defaultProps = {
    messages: [],
    onSendMessage: vi.fn(),
    isTyping: false,
    selectedQuestion: "1",
    currentCode: "",
    language: "python",
  };

  it("renders AI Coach header", () => {
    render(<AIChatPanel {...defaultProps} />);
    expect(screen.getByText("AI COACH")).toBeInTheDocument();
    expect(screen.getByText("Real-time coding assistance")).toBeInTheDocument();
  });

  it("renders MessageList with messages", () => {
    const messages = [
      {
        id: "1",
        role: "user" as const,
        content: "help me",
        timestamp: new Date(),
      },
    ];
    render(<AIChatPanel {...defaultProps} messages={messages} />);
    expect(screen.getByText("help me")).toBeInTheDocument();
  });

  it("renders QuickActions and ChatInput", () => {
    render(<AIChatPanel {...defaultProps} />);
    expect(screen.getByRole("button", { name: /hint/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /review/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /explain/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /debug/i })).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /animate/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(
        "Ask a question or describe your approach...",
      ),
    ).toBeInTheDocument();
  });

  it("calls onSendMessage with input value and clears after send", async () => {
    const onSendMessage = vi.fn();
    const user = userEvent.setup();
    render(<AIChatPanel {...defaultProps} onSendMessage={onSendMessage} />);

    const textarea = screen.getByPlaceholderText(
      "Ask a question or describe your approach...",
    );
    await user.type(textarea, "how does recursion work");

    const buttons = screen.getAllByRole("button");
    const sendButton = buttons[buttons.length - 1];
    await user.click(sendButton);

    expect(onSendMessage).toHaveBeenCalledWith(
      "how does recursion work",
      "freeform",
    );
    expect(textarea).toHaveValue("");
  });

  it("calls onSendMessage with quick action mode", async () => {
    const onSendMessage = vi.fn();
    const user = userEvent.setup();
    render(<AIChatPanel {...defaultProps} onSendMessage={onSendMessage} />);

    await user.click(screen.getByRole("button", { name: /explain/i }));
    expect(onSendMessage).toHaveBeenCalledWith("", "explain");
  });

  it("does not send animate messages through the chat", async () => {
    const onSendMessage = vi.fn();
    const user = userEvent.setup();
    render(<AIChatPanel {...defaultProps} onSendMessage={onSendMessage} />);

    expect(
      screen.queryByRole("button", { name: /animate/i }),
    ).not.toBeInTheDocument();
    expect(onSendMessage).not.toHaveBeenCalled();
  });

  it("disables inputs when isTyping", () => {
    render(<AIChatPanel {...defaultProps} isTyping />);
    expect(
      screen.getByPlaceholderText(
        "Ask a question or describe your approach...",
      ),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: /explain/i })).toBeDisabled();
  });

  it("does not send empty messages", async () => {
    const onSendMessage = vi.fn();
    const user = userEvent.setup();
    render(<AIChatPanel {...defaultProps} onSendMessage={onSendMessage} />);

    const buttons = screen.getAllByRole("button");
    const sendButton = buttons[buttons.length - 1];
    expect(sendButton).toBeDisabled();
    await user.click(sendButton);
    expect(onSendMessage).not.toHaveBeenCalled();
  });
});
