import { describe, it, expect, vi, afterEach } from "vitest";
import {
  render,
  screen,
  act,
  renderHook,
  cleanup,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { showToast, ToastContainer, useToast } from "./Toast";
import { ToastProvider } from "@/providers/ToastProvider";

afterEach(() => {
  cleanup();
});

describe("showToast", () => {
  it("renders a toast with the given message when ToastContainer is mounted", () => {
    render(<ToastContainer />);
    act(() => {
      showToast("Hello world", "info");
    });
    expect(screen.getByText("Hello world")).toBeInTheDocument();
  });

  it("defaults to info variant", () => {
    render(<ToastContainer />);
    act(() => {
      showToast("Default variant");
    });
    expect(screen.getByText("Default variant")).toBeInTheDocument();
  });
});

describe("ToastContainer", () => {
  it("renders nothing when no toasts are shown", () => {
    const { container } = render(<ToastContainer />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders a toast when showToast is called", () => {
    render(<ToastContainer />);
    act(() => {
      showToast("Task completed", "success");
    });
    expect(screen.getByText("Task completed")).toBeInTheDocument();
  });

  it("renders all three variants", () => {
    render(<ToastContainer />);
    act(() => {
      showToast("Success!", "success");
    });
    act(() => {
      showToast("Error!", "error");
    });
    act(() => {
      showToast("Info!", "info");
    });

    expect(screen.getByText("Success!")).toBeInTheDocument();
    expect(screen.getByText("Error!")).toBeInTheDocument();
    expect(screen.getByText("Info!")).toBeInTheDocument();
  });

  it("stacks multiple toasts", () => {
    render(<ToastContainer />);
    act(() => {
      showToast("Toast one", "info");
    });
    act(() => {
      showToast("Toast two", "info");
    });
    act(() => {
      showToast("Toast three", "info");
    });

    const container = screen
      .getByText("Toast one")
      .closest('div[class*="fixed"]');
    expect(container?.children).toHaveLength(3);
  });

  it("dismisses a toast when the close button is clicked", async () => {
    const user = userEvent.setup();
    render(<ToastContainer />);
    act(() => {
      showToast("Dismiss me", "info");
    });

    expect(screen.getByText("Dismiss me")).toBeInTheDocument();

    const closeButton = screen.getByRole("button");
    await user.click(closeButton);

    expect(screen.queryByText("Dismiss me")).not.toBeInTheDocument();
  });

  it("auto-dismisses a toast after 4 seconds", () => {
    vi.useFakeTimers();
    render(<ToastContainer />);

    act(() => {
      showToast("Auto dismiss", "info");
    });
    expect(screen.getByText("Auto dismiss")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(4000);
    });
    expect(screen.queryByText("Auto dismiss")).not.toBeInTheDocument();

    vi.useRealTimers();
  });

  it("dismisses only the clicked toast", async () => {
    const user = userEvent.setup();
    render(<ToastContainer />);
    act(() => {
      showToast("Keep me", "info");
    });
    act(() => {
      showToast("Remove me", "info");
    });

    const buttons = screen.getAllByRole("button");
    await user.click(buttons[1]);

    expect(screen.queryByText("Remove me")).not.toBeInTheDocument();
    expect(screen.getByText("Keep me")).toBeInTheDocument();
  });
});

describe("ToastProvider", () => {
  it("renders children", () => {
    render(
      <ToastProvider>
        <div>Child content</div>
      </ToastProvider>,
    );
    expect(screen.getByText("Child content")).toBeInTheDocument();
  });

  it("renders toasts through the provider", () => {
    render(
      <ToastProvider>
        <div>Child</div>
      </ToastProvider>,
    );
    act(() => {
      showToast("Provider toast", "success");
    });
    expect(screen.getByText("Provider toast")).toBeInTheDocument();
  });
});

describe("useToast", () => {
  it("returns showToast function", () => {
    const { result } = renderHook(() => useToast());
    expect(result.current.showToast).toBe(showToast);
  });

  it("returned showToast renders a toast when container is mounted", () => {
    render(<ToastContainer />);
    const { result } = renderHook(() => useToast());
    act(() => {
      result.current.showToast("Via hook", "info");
    });
    expect(screen.getByText("Via hook")).toBeInTheDocument();
  });
});
