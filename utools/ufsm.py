"""
A finite state machine is represented by a tuple of 5 elements:

* A non empty input alphabet
* A non empty set of states
* An initial state
* A non empty set of final states
* A transition function

For a deterministic automata, the transition function is defined as:

    fn(s: States, a: Alphabet) -> State

For non-deterministic automata, the transition function is defined as:

    fn(s: States, a: Alphabet) -> set[States]

In this implementation this transition function is implemented as a:

    dict[States, dict[Alphabet, set[States]]]

PHI is used to represent the dead state.
"""

from contextlib import suppress
from dataclasses import dataclass, field
from typing import Generic, TypeVar

Alphabet = TypeVar("Alphabet")
States = TypeVar("States")


class DeadState:
    def __iter__(self):
        yield self

    def __repr__(self):
        return "DeadState"


PHI = DeadState()


@dataclass
class FiniteStateMachine(Generic[Alphabet, States]):
    start_state: States
    final_states: set[States]
    transitions: dict[States, dict[Alphabet, set[States]]]

    inputs: set[Alphabet] = field(init=False)
    states: set[States] = field(init=False)

    def __post_init__(self):
        self.inputs = set()
        self.states = set()
        for state, inputs in self.transitions.items():
            self.inputs.update(inputs.keys())
            self.states.add(state)

    def __call__(self, inputs: list[Alphabet]) -> tuple[set[States | DeadState], bool]:
        threads = [(self.start_state, inputs)]
        results: set[States | DeadState] = set()

        while threads:
            state, inputs = threads.pop()
            try:
                for index, symbol in enumerate(inputs):
                    transitions = self.transitions[state][symbol].copy()
                    state = transitions.pop()
                    threads.extend((t, inputs[index + 1 :]) for t in transitions)
            except (IndexError, KeyError):
                state = PHI
            results.add(state)

        return (results, bool(results & self.final_states))

    def minimize(self) -> DFA[A, S]:
        def cmp(a: list[set[S]], b: list[set[S]]) -> bool:
            if len(a) != len(b):
                return False

            for i in range(0, len(a)):
                if a[i] != b[i]:
                    return False

            return True

        def eq(s1: S, s2: S, table: list[set[S]]) -> bool:
            for sym in dfa.inputs:
                a = dfa.transitions[s1][sym]
                b = dfa.transitions[s2][sym]
                if a == b:
                    continue

                set_a = next(s for s in table if a in s)
                set_b = next(s for s in table if b in s)
                if set_a != set_b:
                    return False

            return True

        previous = [dfa.states - dfa.final_states, dfa.final_states]
        while True:
            current: list[set[S]] = []
            for subset in previous:
                pending = subset.copy()
                s1 = pending.pop()
                current.append({s1})

                while pending:
                    for s2 in pending:
                        if eq(s1, s2, previous):
                            set_s1 = next(s for s in current if s1 in s)
                            set_s1.add(s2)
                        else:
                            set_s2 = next((s for s in current if s2 in s), None)
                            if set_s2 is None:
                                current.append({s2})
                    s1 = pending.pop()

            if cmp(previous, current):
                break
            previous = current

        return dfa


    def negate(self) -> "FiniteStateMachine[Alphabet, States]":
        return self.__class__(
            start_state=self.start_state,
            final_states=self.states - self.final_states,
            transitions=self.transitions,
        )

    def as_dfa(self):
        dfa = FiniteStateMachine[Alphabet, frozenset[States] | DeadState](
            start_state=frozenset({self.start_state}),
            final_states=set(),
            transitions={},
        )

        pending: set[frozenset[States] | DeadState] = {frozenset({self.start_state})}
        visited: set[frozenset[States] | DeadState] = set()

        while pending:
            states = pending.pop()
            if states in visited:
                continue

            # state is PHI does not guard the union type
            if isinstance(states, DeadState):
                dfa.transitions[PHI] = {symbol: {PHI} for symbol in self.inputs}
                continue

            dfa.transitions[states] = {}
            for symbol in self.inputs:
                next_state: set[States] = set()
                for state in states:
                    with suppress(KeyError):
                        next_state.update(self.transitions[state][symbol])

                frozen_state = frozenset(next_state) if next_state else PHI
                dfa.transitions[states][symbol] = set({frozen_state})
                pending.add(frozen_state)

            visited.add(states)

        dfa.__post_init__()
        dfa.final_states.update(
            combined_state
            for combined_state in dfa.states
            for single_state in combined_state
            if single_state in self.final_states
        )

        return dfa


FSM = FiniteStateMachine
DFA = FiniteStateMachine
NFA = FiniteStateMachine

d: DFA[int, str] = DFA(
    initial_state="A",
    final_states={"E"},
    transitions={
        "A": {0: "B", 1: "C"},
        "B": {0: "B", 1: "D"},
        "C": {0: "B", 1: "C"},
        "D": {0: "B", 1: "E"},
        "E": {0: "B", 1: "C"},
    },
)
