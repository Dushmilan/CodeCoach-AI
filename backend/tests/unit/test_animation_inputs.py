"""Unit tests for example-input normalization.

DB question examples store inputs in many shapes:
`nums = [2,7,11,15], target = 9`, bare arrays, bare strings, matrices,
level-order tree arrays, multiline test inputs. The normalizer turns any of
these into the kwargs dict a canonical traced solution expects, using JSON /
literal parsing first (so `null`/`true` and Python values both work) and a
raw-string fallback for values that are not evaluable (e.g. bit-string args).
"""

from app.services.animation_inputs import parse_input_kwargs


class TestParseInputKwargs:
    def test_assignments_becomes_kwargs(self):
        out = parse_input_kwargs("nums = [2,7,11,15], target = 9", ["nums", "target"])
        assert out == {"nums": [2, 7, 11, 15], "target": 9}

    def test_bare_array_maps_to_first_signature_param(self):
        assert parse_input_kwargs("[5,1,4,2,8]", ["values"]) == {
            "values": [5, 1, 4, 2, 8]
        }

    def test_bare_string_maps_to_first_signature_param(self):
        assert parse_input_kwargs('"()"', ["s"]) == {"s": "()"}

    def test_bare_number_maps_to_first_signature_param(self):
        assert parse_input_kwargs("19", ["n"]) == {"n": 19}

    def test_nested_brackets_are_not_split(self):
        out = parse_input_kwargs("root = [3,1,4,null,2], k = 1", ["root", "k"])
        assert out == {"root": [3, 1, 4, None, 2], "k": 1}

    def test_json_true_null_literals(self):
        out = parse_input_kwargs(
            'board = [["1","1","0"]], word = "11"', ["board", "word"]
        )
        assert out == {"board": [["1", "1", "0"]], "word": "11"}

    def test_two_arrays_from_assignments(self):
        out = parse_input_kwargs("l1 = [2,4,3], l2 = [5,6,4]", ["l1", "l2"])
        assert out == {"l1": [2, 4, 3], "l2": [5, 6, 4]}

    def test_multiline_input_maps_lines_to_signature(self):
        out = parse_input_kwargs("[2,4,3]\n[5,6,4]", ["l1", "l2"])
        assert out == {"l1": [2, 4, 3], "l2": [5, 6, 4]}

    def test_multiline_assignments_are_parsed(self):
        out = parse_input_kwargs(
            'operations = ["push","pop"],\nvalues = [[-2],[]]',
            ["operations", "values"],
        )
        assert out == {"operations": ["push", "pop"], "values": [[-2], []]}

    def test_multiline_assignments_without_comma(self):
        out = parse_input_kwargs(
            'operations = ["push"]\nvalues = [[-2]]',
            ["operations", "values"],
        )
        assert out == {"operations": ["push"], "values": [[-2]]}

    def test_raw_string_fallback_when_not_evaluable(self):
        out = parse_input_kwargs("n = 00000000000000000000000000001011", ["n"])
        assert out == {"n": "00000000000000000000000000001011"}

    def test_strings_with_commas_inside_quotes(self):
        out = parse_input_kwargs('strs = ["eat","tea","tan"], k = 1', ["strs", "k"])
        assert out == {"strs": ["eat", "tea", "tan"], "k": 1}

    def test_dict_input_passes_through(self):
        assert parse_input_kwargs({"values": [1, 2]}, ["values"]) == {"values": [1, 2]}

    def test_empty_input_returns_empty_kwargs(self):
        assert parse_input_kwargs("", ["s"]) == {}
        assert parse_input_kwargs(None, ["s"]) == {}

    def test_unknown_key_is_kept(self):
        out = parse_input_kwargs("n = 5, extra = [1]", ["n"])
        assert out == {"n": 5, "extra": [1]}

    def test_operator_syntax_without_space_after_equals(self):
        out = parse_input_kwargs("n=2", ["n"])
        assert out == {"n": 2}
