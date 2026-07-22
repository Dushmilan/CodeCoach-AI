import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ThemeProvider, useTheme } from "./ThemeProvider";

vi.mock("next-themes", () => ({
  ThemeProvider: ({ children, ...props }: any) => {
    return (
      <div data-testid="theme-provider" data-props={JSON.stringify(props)}>
        {children}
      </div>
    );
  },
  useTheme: () => ({ theme: "dark", setTheme: vi.fn(), resolvedTheme: "dark" }),
}));

function TestConsumer() {
  const { theme } = useTheme();
  return <span data-testid="theme-value">{theme}</span>;
}

describe("ThemeProvider", () => {
  it("renders children", () => {
    render(
      <ThemeProvider attribute="class" defaultTheme="dark">
        <div>child</div>
      </ThemeProvider>,
    );
    expect(screen.getByText("child")).toBeInTheDocument();
  });

  it("passes props to next-themes ThemeProvider", () => {
    render(
      <ThemeProvider attribute="class" defaultTheme="dark">
        <div>child</div>
      </ThemeProvider>,
    );
    const provider = screen.getByTestId("theme-provider");
    const props = JSON.parse(provider.dataset.props || "{}");
    expect(props.attribute).toBe("class");
    expect(props.defaultTheme).toBe("dark");
  });

  it("provides theme context to consumers", () => {
    render(
      <ThemeProvider attribute="class" defaultTheme="dark">
        <TestConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("theme-value")).toHaveTextContent("dark");
  });
});
