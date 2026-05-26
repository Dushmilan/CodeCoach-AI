## Graphify-First Codebase Exploration

When any skill or instruction tells you to explore, walk, or read the codebase to understand its structure, you MUST use graphify commands instead of Agent-based exploration or raw file reads:

1. `graphify query "<focused question>"` — returns a scoped subgraph of relevant nodes and edges
2. `graphify path "<A>" "<B>"` — shortest path between modules when investigating coupling
3. `graphify explain "<concept>"` — explains a node and its neighbours in plain language
4. Only read raw source files when graphify output lacks sufficient detail

This overrides any skill's exploration instructions within this project.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
