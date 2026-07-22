import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { EmptyState } from "./EmptyState";

const TestIcon = () => <svg data-testid="test-icon" />;

describe("EmptyState", () => {
  it("renders title", () => {
    render(<EmptyState title="No items found" />);
    expect(screen.getByText("No items found")).toBeInTheDocument();
  });

  it("renders description when provided", () => {
    render(
      <EmptyState title="No items" description="Try adjusting your filters" />,
    );
    expect(screen.getByText("Try adjusting your filters")).toBeInTheDocument();
  });

  it("renders icon when provided", () => {
    render(<EmptyState icon={TestIcon} title="Empty" />);
    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
  });

  it("renders action button when actionLabel and onAction provided", () => {
    const onAction = vi.fn();
    render(
      <EmptyState title="No data" actionLabel="Refresh" onAction={onAction} />,
    );
    const button = screen.getByRole("button", { name: /refresh/i });
    expect(button).toBeInTheDocument();
    button.click();
    expect(onAction).toHaveBeenCalledOnce();
  });

  it("does not render button when onAction is missing", () => {
    render(<EmptyState title="No data" actionLabel="Refresh" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(
      <EmptyState title="Test" className="custom-class" />,
    );
    expect(container.firstChild).toHaveClass("custom-class");
  });
});
