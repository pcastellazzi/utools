from utools.ufsm import DFA, PHI

from .symbols import A, B, C, D, E


def test_starts_with_0():
    d = DFA(
        start_state=A,
        final_states={B},
        transitions={
            A: {0: {B}, 1: {C}},
            B: {0: {B}, 1: {B}},
            C: {0: {C}, 1: {C}},
        },
    )

    assert d([0, 0, 1]) == (B, True)
    assert d([1, 0, 1]) == (C, False)


def test_length_2():
    d = DFA(
        start_state=A,
        final_states={C},
        transitions={
            A: {0: {B}, 1: {B}},
            B: {0: {C}, 1: {C}},
            C: {0: {D}, 1: {D}},
            D: {0: {D}, 1: {D}},
        },
    )

    assert d([0, 0]) == (C, True)
    assert d([1, 0]) == (C, True)
    assert d([0, 0, 1]) == (D, False)


def test_does_not_contain_aabb():
    d = DFA(
        start_state=A,
        final_states={E},
        transitions={
            A: {"a": {B}, "b": {A}},
            B: {"a": {C}, "b": {A}},
            C: {"a": {C}, "b": {D}},
            D: {"a": {B}, "b": {E}},
            E: {"a": {E}, "b": {E}},
        },
    )
    d = d.negate()

    assert d(["a", "a", "a"]) == (C, True)
    assert d(["b", "b", "b"]) == (A, True)
    assert d(["a", "a", "b", "b"]) == (E, False)


def test_01_or_1n0():
    d = DFA(
        start_state=A,
        final_states={D, E},
        transitions={
            A: {0: {C}, 1: {B}},
            B: {0: {D}, 1: {B}},
            C: {1: {E}},
            D: {},
            E: {},
        },
    )

    assert d([1, 0]) == (D, True)
    assert d([1, 1, 0]) == (D, True)
    assert d([0, 1]) == (E, True)

    assert d([0, 0, 1]) == (PHI, False)
    assert d([0, 1, 0]) == (PHI, False)
    assert d([0, 1, 1]) == (PHI, False)
    assert d([1, 1, 0, 0]) == (PHI, False)
    assert d([1, 1, 0, 1]) == (PHI, False)
