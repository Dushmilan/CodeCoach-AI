from fastapi import APIRouter, HTTPException
from typing import List
import json
import os
from app.models.question import Question, QuestionList

router = APIRouter()

# Load questions from JSON file
QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "questions", "questions.json")


def load_questions() -> List[Question]:
    """Load questions from JSON file."""
    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Convert the nested structure to match our Pydantic models
            questions = []
            for q in data.get("questions", []):
                # Handle test cases
                test_cases = []
                for tc in q.get("testCases", []):
                    test_case = {
                        "input": tc["input"],
                        "expected": tc["expected"],
                        "function_name": tc["functionName"],
                        "python_function_name": tc["pythonFunctionName"],
                        "java_function_name": tc["javaFunctionName"],
                        "in_place": tc.get("inPlace", False)
                    }
                    test_cases.append(test_case)
                
                # Handle examples
                examples = []
                for ex in q.get("examples", []):
                    examples.append({
                        "input": ex["input"],
                        "output": ex["output"]
                    })
                
                question = {
                    "id": q["id"],
                    "title": q["title"],
                    "difficulty": q["difficulty"],
                    "category": q["category"],
                    "description": q["description"],
                    "starter": q["starter"],
                    "test_cases": test_cases,
                    "examples": examples,
                    "hints": q.get("hints", []),
                    "solution": q.get("solution", ""),
                    "time_complexity": q.get("timeComplexity", ""),
                    "space_complexity": q.get("spaceComplexity", "")
                }
                questions.append(Question(**question))
            return questions
    except FileNotFoundError:
        # Return sample questions if file doesn't exist
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading questions: {str(e)}")


@router.get("/", response_model=List[Question])
async def get_questions():
    """Get all questions."""
    return load_questions()


@router.get("/{question_id}", response_model=Question)
async def get_question(question_id: str):
    """Get specific question by ID."""
    questions = load_questions()
    for question in questions:
        if question.id == question_id:
            return question
    raise HTTPException(status_code=404, detail="Question not found")