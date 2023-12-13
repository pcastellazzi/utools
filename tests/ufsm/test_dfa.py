from typing import Literal

from utools.ufsm import DFA, PHI

from .symbols import L_01, S_AC, S_AD, S_AE, A, B, C, D, E


def test_starts_with_0():
    d: DFA[L_01, S_AC] = DFA(
        start_state=A,
        final_states={B},
        transitions={
            A: {0: {B}, 1: {C}},
            B: {0: {B}, 1: {B}},
            C: {0: {C}, 1: {C}},
        },
    )
    assert ({B}, True) == d([0, 0, 1])
    assert ({C}, False) == d([1, 0, 1])


def test_length_2():
    d: DFA[L_01, S_AD] = DFA(
        start_state=A,
        final_states={C},
        transitions={
            A: {0: {B}, 1: {B}},
            B: {0: {C}, 1: {C}},
            C: {0: {D}, 1: {D}},
            D: {0: {D}, 1: {D}},
        },
    )

    assert ({C}, True) == d([0, 0])
    assert ({C}, True) == d([1, 0])
    assert ({D}, False) == d([0, 0, 1])


def test_does_not_contain_aabb():
    d: DFA[Literal["a", "b"], S_AE] = DFA(
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

    assert ({C}, True) == d(["a", "a", "a"])
    assert ({A}, True) == d(["b", "b", "b"])
    assert ({E}, False) == d(["a", "a", "b", "b"])


def test_01_or_1n0():
    d: DFA[L_01, S_AE] = DFA(
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

    assert ({D}, True) == d([1, 0])
    assert ({D}, True) == d([1, 1, 0])
    assert ({E}, True) == d([0, 1])

    assert ({PHI}, False) == d([0, 0, 1])
    assert ({PHI}, False) == d([0, 1, 0])
    assert ({PHI}, False) == d([0, 1, 1])
    assert ({PHI}, False) == d([1, 1, 0, 0])
    assert ({PHI}, False) == d([1, 1, 0, 1])
