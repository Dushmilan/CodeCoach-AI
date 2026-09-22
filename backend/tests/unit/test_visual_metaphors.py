"""Unit tests for the visual metaphor registry (#240).

The registry must mirror the compiler's current palette exactly so workstream D
can flip family_compilers onto it with zero rendered-output change.
"""

import pytest

from app.services import family_compilers as fc
from app.services.visual_metaphors import metaphor_for

FAMILIES = [
    "array",
    "backtrack",
    "stack",
    "linked_list",
    "tree",
    "graph",
    "grid",
    "intervals",
]


class TestMetaphorRegistry:
    @pytest.mark.parametrize("family", FAMILIES)
    def test_every_family_has_a_metaphor(self, family):
        metaphor = metaphor_for(family)
        assert metaphor is not None
        assert metaphor.family == family
        assert metaphor.base_shape in {"rect", "ellipse", "polygon"}
        assert metaphor.layout
        assert metaphor.metaphor

    def test_colors_mirror_compiler_palette(self):
        colors = metaphor_for("array").colors
        assert colors["idle_fill"] == fc.IDLE_FILL
        assert colors["idle_stroke"] == fc.IDLE_STROKE
        assert colors["highlight_fill"] == fc.CHECK_FILL
        assert colors["highlight_stroke"] == fc.CHECK_STROKE
        assert colors["accent"] == fc.SWAP_STROKE
        assert colors["success_fill"] == fc.DONE_FILL
        assert colors["success_stroke"] == fc.DONE_STROKE
        assert colors["text"] == fc.TEXT_FILL

    def test_unknown_family_is_none(self):
        assert metaphor_for("nope") is None
