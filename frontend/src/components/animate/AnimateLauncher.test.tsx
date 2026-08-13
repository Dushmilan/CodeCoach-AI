import { describe, it, expect, vi, afterEach } from "vitest";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  AnimateLauncher,
  ANIMATION_MESSAGE_TYPE,
  ANIMATION_ERROR_MESSAGE_TYPE,
} from "./AnimateLauncher";
import { HttpError } from "@/lib/fetch-client";

const mockGenerateAnimation = vi.hoisted(() => vi.fn());

vi.mock("@/features/animation/animation.service", async (importOriginal) => {
  const actual =
    await importOriginal<
      typeof import("@/features/animation/animation.service")
    >();
  return {
    ...actual,
    animationService: { generateAnimation: mockGenerateAnimation },
  };
});

const animationFixture = {
  type: "linear_search",
  title: "Searching for 4",
  data: { values: [5, 1, 2, 3, 4, 6], target: 4 },
  steps: [],
};

describe("AnimateLauncher", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    mockGenerateAnimation.mockReset();
  });

  const defaultProps = {
    problem: "Find the target",
    code: "def search(arr, t):\n    pass",
    language: "python",
    initialCode: "def search(arr, t):\n    pass",
  };

  function renderLauncher(
    overrides: Partial<Parameters<typeof AnimateLauncher>[0]> = {},
  ) {
    return render(<AnimateLauncher {...defaultProps} {...overrides} />);
  }

  async function openAndGetIframe(
    overrides: Partial<Parameters<typeof AnimateLauncher>[0]> = {},
  ) {
    const user = userEvent.setup();
    const view = renderLauncher(overrides);
    await user.click(screen.getByRole("button", { name: /animate solution/i }));
    const dialog = await screen.findByRole("dialog");
    const iframe = within(dialog).getByTitle(
      "Animation viewer",
    ) as HTMLIFrameElement;
    return { view, dialog, iframe };
  }

  it("renders an Animate button", () => {
    renderLauncher();
    expect(
      screen.getByRole("button", { name: /animate solution/i }),
    ).toBeInTheDocument();
  });

  it("opens a viewer modal (no popup window) and posts the animation on iframe load", async () => {
    mockGenerateAnimation.mockResolvedValue(animationFixture);
    const openSpy = vi.spyOn(window, "open");
    const { iframe } = await openAndGetIframe();

    expect(openSpy).not.toHaveBeenCalled();
    expect(iframe.getAttribute("src")).toMatch(/viewer\.html\?token=/);
    const token = new URL(iframe.getAttribute("src")!).searchParams.get(
      "token",
    );
    expect(token).toBeTruthy();

    const postMessage = vi
      .spyOn(iframe.contentWindow!, "postMessage")
      .mockImplementation(() => {});
    fireEvent.load(iframe);

    await waitFor(() => expect(postMessage).toHaveBeenCalledTimes(1));
    const [payload, targetOrigin] = postMessage.mock.calls[0];

    expect(payload.type).toBe(ANIMATION_MESSAGE_TYPE);
    expect(payload.token).toBe(token);
    expect(payload.animation.type).toBe("linear_search");
    expect(targetOrigin).toBe("http://localhost:9000");
    expect(mockGenerateAnimation).toHaveBeenCalledWith(
      expect.objectContaining({
        problem: "Find the target",
        language: "python",
      }),
    );
  });

  it("passes the linked question to the animation request", async () => {
    mockGenerateAnimation.mockResolvedValue(animationFixture);
    const question = {
      id: "q1",
      title: "Two Sum",
      difficulty: "medium" as const,
      category: "hash_map",
      company_tags: [],
      description: "Find two numbers that add to target.",
      starter: {
        python: "def f(): pass",
        javascript: "",
        java: "",
        cpp: "",
        c: "",
        go: "",
        rust: "",
        typescript: "",
      },
      examples: [{ input: "[2,7,11,15], 9", output: "[0,1]" }],
      test_cases: [{ input: "[3,3], 6", expected_output: "[0,1]" }],
      hints: [],
      solution: "",
      time_complexity: "",
      space_complexity: "",
    };
    const { iframe } = await openAndGetIframe({ question });
    const postMessage = vi
      .spyOn(iframe.contentWindow!, "postMessage")
      .mockImplementation(() => {});
    fireEvent.load(iframe);
    await waitFor(() => expect(postMessage).toHaveBeenCalledTimes(1));

    expect(mockGenerateAnimation).toHaveBeenCalledWith(
      expect.objectContaining({
        question: expect.objectContaining({
          title: "Two Sum",
          category: "hash_map",
          description: "Find two numbers that add to target.",
        }),
      }),
    );
  });

  it("posts an error message to the viewer when generation fails", async () => {
    mockGenerateAnimation.mockRejectedValue(new Error("boom"));
    const { dialog } = await openAndGetIframe();
    const iframe = within(dialog).getByTitle(
      "Animation viewer",
    ) as HTMLIFrameElement;
    const postMessage = vi
      .spyOn(iframe.contentWindow!, "postMessage")
      .mockImplementation(() => {});
    fireEvent.load(iframe);

    await waitFor(() => expect(postMessage).toHaveBeenCalled());
    const [payload] = postMessage.mock.calls[0];
    expect(payload.type).toBe(ANIMATION_ERROR_MESSAGE_TYPE);
    expect(payload.message).toBeTruthy();

    expect(await within(dialog).findByRole("alert")).toBeInTheDocument();
  });

  it("posts friendly copy instead of the raw 502 when the backend cannot animate", async () => {
    mockGenerateAnimation.mockRejectedValue(
      new HttpError("Request failed: 502 Bad Gateway", 502, "{}"),
    );
    const { dialog } = await openAndGetIframe();
    const iframe = within(dialog).getByTitle(
      "Animation viewer",
    ) as HTMLIFrameElement;
    const postMessage = vi
      .spyOn(iframe.contentWindow!, "postMessage")
      .mockImplementation(() => {});
    fireEvent.load(iframe);

    await waitFor(() => expect(postMessage).toHaveBeenCalled());
    const [payload] = postMessage.mock.calls[0];
    expect(payload.type).toBe(ANIMATION_ERROR_MESSAGE_TYPE);
    expect(payload.message).toBe("Couldn't animate this problem. Try again.");

    expect(await within(dialog).findByRole("alert")).toHaveTextContent(
      "Couldn't animate this problem",
    );
  });

  it("closes the modal from the close button", async () => {
    mockGenerateAnimation.mockResolvedValue(animationFixture);
    const user = userEvent.setup();
    const { dialog } = await openAndGetIframe();
    await user.click(within(dialog).getByRole("button", { name: /close/i }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
  });

  it("is disabled when there is no code to animate", () => {
    render(<AnimateLauncher {...defaultProps} code="" />);
    expect(
      screen.getByRole("button", { name: /animate solution/i }),
    ).toBeDisabled();
  });

  it("shows the problem title in the dialog header", async () => {
    mockGenerateAnimation.mockResolvedValue(animationFixture);
    const { dialog } = await openAndGetIframe();
    expect(within(dialog).getByText("Find the target")).toBeInTheDocument();
  });

  it("shows a live generation status while loading", async () => {
    mockGenerateAnimation.mockResolvedValue(animationFixture);
    const user = userEvent.setup();
    const view = renderLauncher();
    await user.click(screen.getByRole("button", { name: /animate solution/i }));
    const dialog = await screen.findByRole("dialog");
    const iframe = within(dialog).getByTitle(
      "Animation viewer",
    ) as HTMLIFrameElement;
    const postMessage = vi
      .spyOn(iframe.contentWindow!, "postMessage")
      .mockImplementation(() => {});

    fireEvent.load(iframe);

    const status = within(dialog).getByRole("status");
    expect(status.textContent).toMatch(/compiling|running|rendering/i);

    await waitFor(() =>
      expect(within(dialog).queryByRole("status")).not.toBeInTheDocument(),
    );
    expect(postMessage).toHaveBeenCalledTimes(1);
    expect(view).toBeTruthy();
  });

  it("retries generation from the error state", async () => {
    mockGenerateAnimation
      .mockRejectedValueOnce(new Error("boom"))
      .mockResolvedValueOnce(animationFixture);
    const user = userEvent.setup();
    const { dialog } = await openAndGetIframe();
    let iframe = within(dialog).getByTitle(
      "Animation viewer",
    ) as HTMLIFrameElement;
    const postMessage = vi
      .spyOn(iframe.contentWindow!, "postMessage")
      .mockImplementation(() => {});

    fireEvent.load(iframe);

    await waitFor(() =>
      expect(within(dialog).getByRole("alert")).toBeInTheDocument(),
    );
    expect(mockGenerateAnimation).toHaveBeenCalledTimes(1);
    expect(postMessage).toHaveBeenCalledTimes(1);

    await user.click(
      within(dialog).getByRole("button", { name: /try again/i }),
    );

    await waitFor(() =>
      expect(within(dialog).queryByRole("alert")).not.toBeInTheDocument(),
    );

    iframe = within(dialog).getByTitle("Animation viewer") as HTMLIFrameElement;
    const retryPostMessage = vi
      .spyOn(iframe.contentWindow!, "postMessage")
      .mockImplementation(() => {});
    fireEvent.load(iframe);

    await waitFor(() => expect(retryPostMessage).toHaveBeenCalledTimes(1));
    expect(mockGenerateAnimation).toHaveBeenCalledTimes(2);
    const [payload] = retryPostMessage.mock.calls[0];
    expect(payload.type).toBe(ANIMATION_MESSAGE_TYPE);
  });
});
