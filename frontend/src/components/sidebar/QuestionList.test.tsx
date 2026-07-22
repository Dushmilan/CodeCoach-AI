import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QuestionList } from "./QuestionList";
import { QuestionSummary } from "@/types";

const questions: QuestionSummary[] = [
  {
    id: "1",
    title: "Two Sum",
    difficulty: "easy",
    category: "arrays",
    company_tags: [],
  },
  {
    id: "2",
    title: "Add Two Numbers",
    difficulty: "medium",
    category: "linked-list",
    company_tags: [],
  },
];

describe("QuestionList", () => {
  const defaultProps = {
    questions,
    selectedQuestion: null,
    currentIndex: 0,
    userProgress: {},
    onSelectQuestion: vi.fn(),
  };

  it("renders all questions", () => {
    render(<QuestionList {...defaultProps} />);
    expect(screen.getByText("Two Sum")).toBeInTheDocument();
    expect(screen.getByText("Add Two Numbers")).toBeInTheDocument();
  });

  it("shows no questions message when empty", () => {
    render(<QuestionList {...defaultProps} questions={[]} />);
    expect(screen.getByText("No questions found")).toBeInTheDocument();
  });

  it("highlights selected question", () => {
    render(<QuestionList {...defaultProps} selectedQuestion={questions[0]} />);
    const items = screen.getAllByText("Two Sum");
    const container = items[0].closest('[class*="border-b"]');
    expect(container?.className).toContain("border-l-primary/60");
  });

  it("calls onSelectQuestion with question and index when clicked", async () => {
    const onSelectQuestion = vi.fn();
    const user = userEvent.setup();
    render(
      <QuestionList {...defaultProps} onSelectQuestion={onSelectQuestion} />,
    );

    await user.click(screen.getByText("Two Sum"));
    expect(onSelectQuestion).toHaveBeenCalledWith(questions[0], 0);

    await user.click(screen.getByText("Add Two Numbers"));
    expect(onSelectQuestion).toHaveBeenCalledWith(questions[1], 1);
  });

  it("passes user progress to items", () => {
    render(<QuestionList {...defaultProps} userProgress={{ "1": "solved" }} />);
    const twoSum = screen.getByText("Two Sum");
    expect(twoSum).toBeInTheDocument();
  });
});
