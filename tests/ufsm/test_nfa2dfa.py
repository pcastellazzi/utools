from utools.ufsm import NFA, PHI

from .symbols import AB, ABC, AC, BC, L_01, S_AB, S_AC, A, B, C, Z, fz


def test_starts_with_0():
    n: NFA[L_01, S_AB] = NFA(
        start_state=A,
        final_states={B},
        transitions={
            A: {0: {B}},
            B: {0: {B}, 1: {B}},
        },
    )
    d = n.as_dfa()

    assert d.start_state == fz(A)
    assert d.final_states == {fz(B)}
    assert d.transitions == {
        fz(A): {0: {fz(B)}, 1: {PHI}},
        fz(B): {0: {fz(B)}, 1: {fz(B)}},
        PHI: {0: {PHI}, 1: {PHI}},
    }


def test_ends_with_1():
    n: NFA[L_01, S_AB] = NFA(
        start_state=A,
        final_states={B},
        transitions={
            A: {0: {A}, 1: {A, B}},
            B: {},
        },
    )
    d = n.as_dfa()

    assert d.start_state == fz(A)
    assert d.final_states == {fz(A, B)}
    assert d.transitions == {
        fz(A): {0: {fz(A)}, 1: {fz(A, B)}},
        fz(A, B): {0: {fz(A)}, 1: {fz(A, B)}},
    }


def test_ends_with_01():
    n: NFA[L_01, S_AC] = NFA(
        start_state=A,
        final_states={C},
        transitions={
            A: {0: {A, B}, 1: {A}},
            B: {1: {C}},
            C: {},
        },
    )
    d = n.as_dfa()

    assert d.start_state == fz(A)
    assert d.final_states == {fz(A,C)}
    assert d.transitions == {
            fz(A): {0: {fz(A,B)}, 1: {fz(A)}},
            fz(A,B): {0: {fz(A,B)}, 1: {fz(A,C)}},
            fz(A,C): {0: {fz(A,B)}, 1: {fz(A)}},
        }


def test_ends_with_odd_number_of_b():
    n: NFA[str, str] = NFA(
        start_state=A,
        final_states={C},
        transitions={
            A: {"a": {A, B}, "b": {C}},
            B: {"a": {A}, "b": {B}},
            C: {"b": {A, B}},
        },
    )
    d = n.as_dfa()

    assert d.start_state == fz(A)
    assert d.final_states == {fz(B,C), fz(C)}
    assert d.transitions == {
            fz(A): {"a": {fz(A,B)}, "b": {fz(C)}},
            fz(A,B): {"a": {fz(A,B)}, "b": {fz(B, C)}},
            fz(B,C): {"a": {fz(A)}, "b": {fz(A,B)}},
            fz(C): {"a": {PHI}, "b": {fz(A,B)}},
            PHI: {"a": {PHI}, "b": {PHI}},
        }


def test_second_to_last_is_always_1():
    n: NFA[int, str] = NFA(
        start_state=A,
        final_states={C},
        transitions={
            A: {0: {A}, 1: {A, B}},
            B: {0: {C}, 1: {C}},
            C: {},
        },
    )
    d = n.as_dfa()

    assert d.start_state == fz(A)
    assert d.final_states == {fz(A,C), fz(A,B,C)}
    assert d.transitions == {
            fz(A): {0: {fz(A)}, 1: {fz(A,B)}},
            fz(A,B): {0: {fz(A,C)}, 1: {fz(A,B,C)}},
            fz(A,C): {0: {fz(A)}, 1: {fz(A,B)}},
            fz(A,B,C): {0: {fz(A,C)}, 1: {fz(A,B,C)}},
        }
