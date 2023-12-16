from utools.ufsm import PHI, DeadState


def test_phi_repr():
    assert repr(PHI) == "DeadState"


def test_phi_singleton():
    a = DeadState()
    b = DeadState()

    assert id(a) == id(b)
    assert id(a) == id(PHI)
