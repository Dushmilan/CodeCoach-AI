"""Question bank definition package.

Aggregates all question categories into a single ALL_SPECS list consumed by
build_bank.main() to emit backend/questions/sample_questions.json.
"""

from ._arrays import SPECS as ARRAYS
from ._backtrack import SPECS as BACKTRACK
from ._binary import SPECS as BINARY
from ._companies import assign_companies
from ._curriculum import SPECS as CURRICULUM
from ._dp import SPECS as DP
from ._extra import SPECS as EXTRA
from ._graphs import SPECS as GRAPHS
from ._linked import SPECS as LINKED
from ._pointers import SPECS as POINTERS
from ._stack import SPECS as STACK
from ._strings_math import SPECS as STRINGS_MATH
from ._trees import SPECS as TREES

ALL_SPECS = (
    ARRAYS
    + POINTERS
    + BINARY
    + STACK
    + LINKED
    + TREES
    + GRAPHS
    + DP
    + BACKTRACK
    + STRINGS_MATH
    + CURRICULUM
    + EXTRA
)

assign_companies(ALL_SPECS)
