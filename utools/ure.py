"""
Toy regular expression engine

.   match any character
\\x character literal
()  grouping
?   zero or one quantifier
*   zero or more quantifier
+   one or more quantifier
"""

from dataclasses import dataclass, replace
from typing import Literal


@dataclass(slots=True)
class State:
    kind: Literal["group", "element", "wildcard"]
    quantifier: Literal["exactlyOne", "zeroOrMore", "zeroOrOne"]
    value: list["State"] | str | None = None


def _check_state(state: State, text: str, index: int) -> tuple[bool, int]:
    if index >= len(text):
        return (False, 0)

    match state.kind:
        case "wildcard":
            return (True, 1)
        case "element":
            return (True, 1) if state.value == text[index] else (False, 0)
        case "group":  # pragma: no branch
            return match(state.value, text[index:])  # type: ignore noqa: PGH003


def compile(expr: str) -> list[State]:  # noqa: A001
    stack: list[list[State]] = [[]]
    index = 0

    while index < len(expr):
        match expr[index]:
            case ".":
                stack[-1].append(State("wildcard", "exactlyOne"))
            case "\\":
                stack[-1].append(State("element", "exactlyOne", expr[index + 1]))
                index += 1  # consume the escaped character
            case "(":
                stack.append([])
            case ")":
                states = stack.pop()
                stack[-1].append(State("group", "exactlyOne", states))
            case "?":
                assert stack[-1][-1].quantifier == "exactlyOne"
                stack[-1][-1].quantifier = "zeroOrOne"
            case "*":
                assert stack[-1][-1].quantifier == "exactlyOne"
                stack[-1][-1].quantifier = "zeroOrMore"
            case "+":
                assert stack[-1][-1].quantifier == "exactlyOne"
                stack[-1].append(replace(stack[-1][-1], quantifier="zeroOrMore"))
            case _ as literal:
                stack[-1].append(State("element", "exactlyOne", literal))
        index += 1

    return stack[0]


def match(states: list[State], text: str) -> tuple[bool, int]:
    index = 0

    for state in states:
        match state.quantifier:
            case "exactlyOne":
                res, consumed = _check_state(state, text, index)
                if not res:
                    return (False, index)
                index += consumed
            case "zeroOrOne":
                if index < len(text):
                    res, consumed = _check_state(state, text, index)
                    index += consumed
            case "zeroOrMore":  # pragma: no branch
                while index < len(text):
                    res, consumed = _check_state(state, text, index)
                    if not res or consumed == 0:
                        break
                    index += consumed

    return (True, index)
