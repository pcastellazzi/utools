import pytest

from utools.ure import compile, match


def re(expr: str, text: str) -> tuple[bool, int]:
    return match(compile(expr), text)


@pytest.mark.parametrize(
    ("expr", "text", "expected"),
    [
        ("(a)", "", (False, 0)),
        ("(a)", "b", (False, 0)),
        ("(a)", "a", (True, 1)),
        ("(a)?", "", (True, 0)),
        ("(a)?", "a", (True, 1)),
        ("(a)?", "aa", (True, 1)),
        ("(a)*", "", (True, 0)),
        ("(a)*", "a", (True, 1)),
        ("(a)*", "aa", (True, 2)),
        ("(a)+", "", (False, 0)),
        ("(a)+", "a", (True, 1)),
        ("(a)+", "aa", (True, 2)),
    ],
)
def test_group(expr: str, text: str, expected: tuple[bool, int]):
    assert re(expr, text) == expected


@pytest.mark.parametrize(
    ("expr", "text", "expected"),
    [
        ("a", "", (False, 0)),
        ("a", "b", (False, 0)),
        ("a", "a", (True, 1)),
        ("a?", "", (True, 0)),
        ("a?", "a", (True, 1)),
        ("a?", "aa", (True, 1)),
        ("a*", "", (True, 0)),
        ("a*", "a", (True, 1)),
        ("a*", "aa", (True, 2)),
        ("a+", "", (False, 0)),
        ("a+", "a", (True, 1)),
        ("a+", "aa", (True, 2)),
    ],
)
def test_element(expr: str, text: str, expected: tuple[bool, int]):
    assert re(expr, text) == expected


@pytest.mark.parametrize(
    ("expr", "text", "expected"),
    [
        (".", "", (False, 0)),
        (".", "a", (True, 1)),
        (".?", "", (True, 0)),
        (".?", "a", (True, 1)),
        (".*", "", (True, 0)),
        (".*", "a", (True, 1)),
        (".*", "aa", (True, 2)),
        (".+", "", (False, 0)),
        (".+", "a", (True, 1)),
        (".+", "aa", (True, 2)),
    ],
)
def test_wildcard(expr: str, text: str, expected: tuple[bool, int]):
    assert re(expr, text) == expected


@pytest.mark.parametrize(
    ("expr", "text", "expected"),
    [
        ("a(b.)*cd", "ab!b$cd", (True, 7)),
        ("a(b.)*cd", "ab!cd", (True, 5)),
        ("a(b.)*cd", "acd", (True, 3)),
        (r"\.\?\*\+", ".?*+", (True, 4)),
    ],
)
def test_expression(expr: str, text: str, expected: tuple[bool, int]):
    assert re(expr, text) == expected
