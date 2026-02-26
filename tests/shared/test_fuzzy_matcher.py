from hueify.shared.fuzzy import find_all_matches_sorted


class TestFindAllMatchesSorted:
    def test_returns_exact_match_first(self) -> None:
        items = ["berlin", "münchen", "hamburg"]
        result = find_all_matches_sorted("berlin", items, lambda x: x)
        assert result[0] == "berlin"

    def test_returns_all_items(self) -> None:
        items = ["alpha", "beta", "gamma"]
        result = find_all_matches_sorted("alpha", items, lambda x: x)
        assert len(result) == 3

    def test_sorted_by_similarity_descending(self) -> None:
        items = ["cat", "car", "xyz"]
        result = find_all_matches_sorted("cat", items, lambda x: x)
        assert result[0] == "cat"
        assert result[-1] == "xyz"

    def test_empty_items_returns_empty_list(self) -> None:
        result = find_all_matches_sorted("query", [], lambda x: x)
        assert result == []

    def test_uses_text_extractor(self) -> None:
        items = [{"name": "berlin"}, {"name": "paris"}]
        result = find_all_matches_sorted("berlin", items, lambda x: x["name"])
        assert result[0] == {"name": "berlin"}

    def test_case_insensitive_matching(self) -> None:
        items = ["Berlin", "PARIS", "hamburg"]
        result = find_all_matches_sorted("berlin", items, lambda x: x)
        assert result[0] == "Berlin"

    def test_whitespace_stripped_before_comparison(self) -> None:
        items = ["  berlin  ", "paris"]
        result = find_all_matches_sorted("berlin", items, lambda x: x)
        assert result[0] == "  berlin  "

    def test_single_item_list(self) -> None:
        result = find_all_matches_sorted("hello", ["hello"], lambda x: x)
        assert result == ["hello"]
