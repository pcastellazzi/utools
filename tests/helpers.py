from typing import Any

from utools import uparser as p


def assert_failure(state: p.State, index: int, error: Any):
    assert isinstance(state, p.Failure)
    assert state.index == index
    assert state.error == error


def assert_success(state: p.State, index: int, value: Any):
    assert isinstance(state, p.Success)
    assert state.index == index
    assert state.value == value
