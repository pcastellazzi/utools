from utools.ufsm import NFA, PHI

from .symbols import L_01, S_AB, S_AC, A, B, C


def test_ends_with_0():
    n = NFA[L_01, S_AB](
        start_state=A,
        final_states={B},
        transitions={
            A: {0: {A, B}, 1: {A}},
            B: {},
        },
    )

    assert ({A, B, PHI}, True) == n([1, 0, 0])
    assert ({A, PHI}, False) == n([0, 1])


def test_ends_with_1():
    n = NFA[L_01, S_AB](
        start_state=A,
        final_states={B},
        transitions={
            A: {0: {A}, 1: {A, B}},
            B: {},
        },
    )

    assert ({A, PHI}, False) == n([1, 0, 0])
    assert ({A, B}, True) == n([0, 1])


def test_ends_with_11():
    n = NFA[L_01, S_AC](
        start_state=A,
        final_states={C},
        transitions={
            A: {0: {A}, 1: {A, B}},
            B: {1: {C}},
            C: {},
        },
    )

    assert ({A}, False) == n([0, 0])
    assert ({A, B}, False) == n([0, 1])
    assert ({C, B, A}, True) == n([1, 1])
    assert ({C, B, A}, True) == n([0, 1, 1])


def test_starts_with_0():
    n = NFA[L_01, S_AB](
        start_state=A,
        final_states={B},
        transitions={
            A: {0: {B}},
            B: {0: {B}, 1: {B}},
        },
    )

    assert ({B}, True) == n([0, 0, 1])
    assert ({PHI}, False) == n([1, 0, 1])


def test_starts_with_01():
    n = NFA[L_01, S_AC](
        start_state=A,
        final_states={C},
        transitions={
            A: {0: {A, B}, 1: {A}},
            B: {1: {C}},
            C: {0: {C}, 1: {C}},
        },
    )

    assert ({A}, False) == n([1, 1])
    assert ({C, A}, True) == n([0, 1])
    assert ({C, A}, True) == n([1, 0, 1])


def test_starts_with_10():
    n = NFA[L_01, S_AC](
        start_state=A,
        final_states={C},
        transitions={
            A: {1: {B}},
            B: {0: {C}},
            C: {0: {C}, 1: {C}},
        },
    )

    assert ({PHI}, False) == n([0])
    assert ({B}, False) == n([1])
    assert ({C}, True) == n([1, 0])
    assert ({C}, True) == n([1, 0, 1])
    assert ({PHI}, False) == n([1, 1, 1])


def test_length_2():
    n = NFA[L_01, S_AC](
        start_state=A,
        final_states={C},
        transitions={
            A: {0: {B}, 1: {B}},
            B: {0: {C}, 1: {C}},
            C: {},
        },
    )

    assert ({A}, False) == n([])
    assert ({B}, False) == n([0])
    assert ({C}, True) == n([0, 0])
    assert ({PHI}, False) == n([0, 0, 1])


def test_contains_0():
    n = NFA[L_01, S_AB](
        start_state=A,
        final_states={B},
        transitions={
            A: {0: {A, B}, 1: {A}},
            B: {0: {B}, 1: {B}},
        },
    )

    assert ({A}, False) == n([])
    assert ({A, B}, True) == n([0])
    assert ({A}, False) == n([1, 1])
