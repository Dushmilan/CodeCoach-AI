"""AlgorithmAnimation spec — IR between optimal solution and visual design system.

Decoupled from student code: Problem → Solution repo/Groq → AlgorithmAnimation
→ Scene Planner → Visual Design System → Motion Canvas / Remotion.

The spec is semantic (highlight midpoint, discard left), not pixel coordinates.
The Scene Planner converts semantics into motion beats; the Design System owns
how each beat looks (typography, camera, primitives).
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Complexity(BaseModel):
    time: str = Field(..., max_length=32, description="e.g. O(log n)")
    space: str = Field(..., max_length=32, description="e.g. O(1)")


class InitialState(BaseModel):
    """Visualization-specific initial state (array, graph, tree, etc.)."""

    array: Optional[List[Any]] = None
    target: Optional[Any] = None
    # Generic bucket for graph/tree variants — validators accept any JSON.
    extra: Dict[str, Any] = Field(default_factory=dict)


class AnimationStepSpec(BaseModel):
    """One semantic step — NOT a pixel frame."""

    action: Literal[
        "set_bounds",
        "inspect_mid",
        "discard_left",
        "discard_right",
        "found",
        "not_found",
        "compare",
        "swap",
        "partition",
        "visit",
        "relax_edge",
        "push",
        "pop",
        "choose",
        "backtrack",
        "write",
        "window",
        "edge",
        "dp_update",
        "mark",
        "read",
        "pointer",
        "custom",
    ] = Field(..., description="Semantic action for the planner")
    # Action params — optional per action, validated by planner not schema.
    low: Optional[int] = None
    high: Optional[int] = None
    index: Optional[int] = None
    until: Optional[int] = None
    indices: Optional[List[int]] = None
    values: Optional[List[Any]] = None
    label: Optional[str] = Field(None, max_length=120)


class AlgorithmAnimation(BaseModel):
    """Decoupled animation spec — what to teach, not how it looks."""

    algorithm: str = Field(..., max_length=64, description="e.g. binary-search")
    visualization: Literal[
        "sorted-array",
        "bars",
        "array",
        "graph",
        "tree",
        "stack",
        "queue",
        "linked_list",
        "grid",
        "intervals",
        "backtrack",
    ] = Field(..., description="Which visual family renders this")
    initialState: InitialState = Field(...)
    steps: List[AnimationStepSpec] = Field(..., min_length=1)
    complexity: Complexity = Field(...)
    title: Optional[str] = Field(None, max_length=120)
