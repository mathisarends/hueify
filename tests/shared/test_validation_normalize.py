from hueify.shared.validation import normalize_percentage_input


def test_integer_input_returns_same_value():
    assert normalize_percentage_input(50) == 50
    assert normalize_percentage_input(0) == 0
    assert normalize_percentage_input(100) == 100


def test_float_between_zero_and_one_converts_to_percentage():
    assert normalize_percentage_input(0.72) == 72
    assert normalize_percentage_input(0.5) == 50
    assert normalize_percentage_input(0.0) == 0
    assert normalize_percentage_input(1.0) == 100


def test_float_above_one_converts_to_int():
    assert normalize_percentage_input(50.7) == 50
    assert normalize_percentage_input(99.9) == 99
    assert normalize_percentage_input(75.2) == 75


def test_edge_cases():
    assert normalize_percentage_input(0.01) == 1
    assert normalize_percentage_input(0.99) == 99
    assert normalize_percentage_input(0.001) == 0
