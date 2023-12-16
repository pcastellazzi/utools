from contextlib import suppress
from dataclasses import dataclass, field
from typing import Generic, TypeVar

A = TypeVar("A")
S = TypeVar("S")


class DeadState:
    instance = None

    def __new__(cls):
        if not cls.instance:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __iter__(self):
        yield self

    def __repr__(self):
        return "DeadState"


PHI = DeadState()


@dataclass
class FiniteStateMachine(Generic[A, S]):
    start_state: S
    final_states: set[S]
    transitions: dict[S, dict[A, set[S]]]

    inputs: set[A] = field(init=False)
    states: set[S] = field(init=False)

    def __post_init__(self) -> None:
        self.inputs = set()
        self.states = set()

        for state, inputs in self.transitions.items():
            self.inputs.update(inputs.keys())
            self.states.add(state)

    calculate_properties = __post_init__


class DFA(FiniteStateMachine[A, S]):
    def __call__(self, inputs: list[A]) -> tuple[S | DeadState, bool]:
        state: S | DeadState
        try:
            state = next(iter(self.transitions[self.start_state][inputs[0]]))
            for symbol in inputs[1:]:
                state = next(iter(self.transitions[state][symbol]))
        except (IndexError, KeyError):
            state = PHI

        return (state, state in self.final_states)

    def minimize(self) -> "DFA[A, frozenset[S]]":
        dfa: DFA[A, frozenset[S]] = DFA(
            start_state=frozenset({self.start_state}),
            final_states=set(),
            transitions={},
        )

        equivalences = [frozenset(e) for e in self._get_equivalence_table()]
        print(equivalences)
        for state in equivalences:
            dfa.transitions[state] = {}
            for symbol in self.inputs:
                next_state: set[S] = set()
                for prev_state in state:
                    next_state.update(self.transitions[prev_state][symbol])
                target = next(s for s in equivalences if next_state <= s)
                dfa.transitions[state][symbol] = {target}

        dfa.calculate_properties()
        dfa.start_state = next(s for s in equivalences if self.start_state in s)
        dfa.final_states.update(
            combined_state
            for combined_state in dfa.states
            for single_state in combined_state
            if single_state in self.final_states
        )

        return dfa

    def negate(self) -> "DFA[A, S]":
        return self.__class__(
            start_state=self.start_state,
            final_states=set(self.transitions.keys()) - self.final_states,
            transitions=self.transitions,
        )

    def _get_equivalence_table(self) -> list[set[S]]:
        previous = [self.states - self.final_states, self.final_states]

        while True:
            current: list[set[S]] = []
            for subset in previous:
                pending = subset.copy()
                while pending:
                    s1 = pending.pop()
                    set_s1 = next((s for s in current if s1 in s), None)
                    if not set_s1:
                        set_s1 = {s1}
                        current.append(set_s1)
                    for s2 in pending:
                        if self._state_compare(s1, s2, previous):
                            set_s1.add(s2)
            if self._list_compare(previous, current):
                break
            previous = current

        return current

    def _list_compare(self, a: list[set[S]], b: list[set[S]]) -> bool:
        if len(a) != len(b):
            return False
        return all(a[i] == b[i] for i in range(len(a)))

    def _state_compare(self, s1: S, s2: S, table: list[set[S]]) -> bool:
        for sym in self.inputs:
            a = self.transitions[s1][sym]
            b = self.transitions[s2][sym]
            if a == b:
                continue

            set_a = next(s for s in table if a <= s)
            set_b = next(s for s in table if b <= s)
            if set_a != set_b:
                return False

        return True


class NFA(FiniteStateMachine[A, S]):
    def __call__(self, inputs: list[A]) -> tuple[set[S | DeadState], bool]:
        threads = [(self.start_state, inputs)]
        results: set[S | DeadState] = set()

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

    def as_dfa(self):
        dfa: FiniteStateMachine[A, frozenset[S] | DeadState] = FiniteStateMachine(
            start_state=frozenset({self.start_state}),
            final_states=set(),
            transitions={},
        )

        pending: set[frozenset[S] | DeadState] = {dfa.start_state}
        visited: set[frozenset[S] | DeadState] = set()

        while pending:
            states = pending.pop()
            if states in visited:
                continue

            if isinstance(states, DeadState):
                dfa.transitions[PHI] = {symbol: {PHI} for symbol in self.inputs}
                continue

            dfa.transitions[states] = {}

            for symbol in self.inputs:
                next_state: set[S] = set()
                for state in states:
                    with suppress(KeyError):
                        next_state.update(self.transitions[state][symbol])

                frozen_state = frozenset(next_state) if next_state else PHI
                dfa.transitions[states][symbol] = set({frozen_state})
                pending.add(frozen_state)

            visited.add(states)

        dfa.calculate_properties()
        dfa.final_states.update(
            combined_state
            for combined_state in dfa.states
            for single_state in combined_state
            if single_state in self.final_states
        )

        return dfa
