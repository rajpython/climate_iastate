"""Tests for the management-area ↔ board-group crosswalk (E0 foundation for E2)."""
from mhw.econ.areas import BOARD_GROUPS, board_groups, crosswalk


def test_crosswalk_maps_management_areas():
    assert crosswalk("Bering Sea") == "bering"
    assert crosswalk("Aleutian Islands") == "ai"
    assert crosswalk("Gulf of Alaska") == "goa"
    # GOA reporting areas fold into the GOA group
    assert crosswalk("610") == "goa"
    assert crosswalk("Central GOA") == "goa"


def test_crosswalk_is_case_and_space_insensitive():
    assert crosswalk("  bering sea  ") == "bering"
    assert crosswalk("ALEUTIAN ISLANDS") == "ai"


def test_crosswalk_unknown_is_none():
    assert crosswalk("Antarctica") is None
    assert crosswalk(None) is None


def test_board_groups():
    assert board_groups() == BOARD_GROUPS
    assert set(board_groups()) == {"bering", "goa", "ai"}
