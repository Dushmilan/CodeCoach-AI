from app.services import scene_planner


def test_tree_layout_matches_compiler_math():
    pos = scene_planner.tree_layout(3)
    assert len(pos) == 3
    assert pos[0]["y"] < pos[1]["y"]  # root above children
    assert pos[1]["x"] < pos[2]["x"]  # left before right
    assert all(abs(p["x"]) <= 960 and abs(p["y"]) <= 540 for p in pos)
