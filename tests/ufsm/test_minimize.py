from utools.ufsm import DFA

from .symbols import A, B, C, D, E, F, G, H, fz


def test_minimize_1():
    d = DFA(
        start_state=A,
        final_states={E},
        transitions={
            A: {0: {B}, 1: {C}},
            B: {0: {B}, 1: {D}},
            C: {0: {B}, 1: {C}},
            D: {0: {B}, 1: {E}},
            E: {0: {B}, 1: {C}},
        },
    )
    m = d.minimize()

    assert m.start_state == fz(A, C)
    assert m.final_states == {fz(E)}
    assert m.transitions == {
        fz(A, C): {0: {fz(B)}, 1: {fz(A, C)}},
        fz(B): {0: {fz(B)}, 1: {fz(D)}},
        fz(D): {0: {fz(B)}, 1: {fz(E)}},
        fz(E): {0: {fz(B)}, 1: {fz(A, C)}},
    }


def test_minimize_2():
    d = DFA(
        start_state=A,
        final_states={C},
        transitions={
            A: {0: {B}, 1: {F}},
            B: {0: {G}, 1: {C}},
            C: {0: {A}, 1: {C}},
            D: {0: {C}, 1: {G}},
            E: {0: {H}, 1: {F}},
            F: {0: {C}, 1: {G}},
            G: {0: {G}, 1: {E}},
            H: {0: {G}, 1: {C}},
        },
    )
    m = d.minimize()

    assert m.start_state == fz(A, E)
    assert m.final_states == {fz(C)}
    assert m.transitions == {
        fz(A, E): {0: {fz(B, H)}, 1: {fz(D, F)}},
        fz(C): {0: {fz(A, E)}, 1: {fz(C)}},
        fz(G): {0: {fz(G)}, 1: {fz(A, E)}},
        fz(B, H): {0: {fz(G)}, 1: {fz(C)}},
        fz(D, F): {0: {fz(C)}, 1: {fz(G)}},
    }


def test_minimize_3():
    d = DFA(
        start_state=A,
        final_states={B, C, F},
        transitions={
            A: {0: {B}, 1: {C}},
            B: {0: {D}, 1: {E}},
            C: {0: {E}, 1: {D}},
            D: {0: {F}, 1: {F}},
            E: {0: {F}, 1: {F}},
            F: {0: {F}, 1: {F}},
        },
    )
    m = d.minimize()

    assert m.start_state == fz(A)
    assert m.final_states == {fz(B, C), fz(F)}
    assert m.transitions == {
        fz(A): {0: {fz(B, C)}, 1: {fz(B, C)}},
        fz(B, C): {0: {fz(D, E)}, 1: {fz(D, E)}},
        fz(D, E): {0: {fz(F)}, 1: {fz(F)}},
        fz(F): {0: {fz(F)}, 1: {fz(F)}},
    }
