from dataclasses import dataclass

import pytest

from hueify.shared.fuzzy import find_all_matches


@dataclass
class Room:
    name: str
    id: str


@pytest.fixture
def rooms() -> list[Room]:
    return [
        Room(name="Wohnzimmer", id="1"),
        Room(name="Schlafzimmer", id="2"),
        Room(name="Arbeitszimmer", id="3"),
        Room(name="Badezimmer", id="4"),
        Room(name="Küche", id="5"),
    ]


def test_exact_match_returns_single_result(rooms: list[Room]) -> None:
    matches = find_all_matches(
        query="Wohnzimmer",
        items=rooms,
        text_extractor=lambda r: r.name,
        min_similarity=0.8,
    )

    assert len(matches) == 1
    assert matches[0].name == "Wohnzimmer"


def test_typo_finds_similar_matches(rooms: list[Room]) -> None:
    matches = find_all_matches(
        query="Wonzimmer",
        items=rooms,
        text_extractor=lambda r: r.name,
        min_similarity=0.6,
    )

    assert len(matches) >= 1
    assert matches[0].name == "Wohnzimmer"


def test_partial_match_finds_all_containing_substring(rooms: list[Room]) -> None:
    matches = find_all_matches(
        query="zimmer", items=rooms, text_extractor=lambda r: r.name, min_similarity=0.5
    )

    zimmer_rooms = [m for m in matches if "zimmer" in m.name.lower()]
    assert len(zimmer_rooms) == 4


def test_case_insensitive_matching(rooms: list[Room]) -> None:
    matches = find_all_matches(
        query="WOHNZIMMER",
        items=rooms,
        text_extractor=lambda r: r.name,
        min_similarity=0.8,
    )

    assert len(matches) == 1
    assert matches[0].name == "Wohnzimmer"


def test_no_matches_returns_empty_list(rooms: list[Room]) -> None:
    matches = find_all_matches(
        query="Garage", items=rooms, text_extractor=lambda r: r.name, min_similarity=0.8
    )

    assert len(matches) == 0


def test_high_similarity_threshold_filters_weak_matches(rooms: list[Room]) -> None:
    matches_low = find_all_matches(
        query="Wohn", items=rooms, text_extractor=lambda r: r.name, min_similarity=0.3
    )

    matches_high = find_all_matches(
        query="Wohn", items=rooms, text_extractor=lambda r: r.name, min_similarity=0.9
    )

    assert len(matches_low) > len(matches_high)


def test_results_are_sorted_by_similarity(rooms: list[Room]) -> None:
    matches = find_all_matches(
        query="zimmer", items=rooms, text_extractor=lambda r: r.name, min_similarity=0.4
    )

    if len(matches) >= 2:
        similarities = []
        for i in range(len(matches) - 1):
            from hueify.shared.fuzzy import _calculate_similarity

            sim1 = _calculate_similarity("zimmer", matches[i].name)
            sim2 = _calculate_similarity("zimmer", matches[i + 1].name)
            similarities.append((sim1, sim2))

        for sim1, sim2 in similarities:
            assert sim1 >= sim2


def test_empty_query_returns_no_matches(rooms: list[Room]) -> None:
    matches = find_all_matches(
        query="", items=rooms, text_extractor=lambda r: r.name, min_similarity=0.5
    )

    assert len(matches) == 0


def test_empty_items_returns_no_matches() -> None:
    matches = find_all_matches(
        query="Wohnzimmer",
        items=[],
        text_extractor=lambda r: r.name,
        min_similarity=0.5,
    )

    assert len(matches) == 0


def test_whitespace_is_stripped_before_comparison(rooms: list[Room]) -> None:
    matches = find_all_matches(
        query="  Wohnzimmer  ",
        items=rooms,
        text_extractor=lambda r: r.name,
        min_similarity=0.8,
    )

    assert len(matches) == 1
    assert matches[0].name == "Wohnzimmer"
