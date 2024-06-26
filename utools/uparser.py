import re
import sys
from collections.abc import Callable, Generator, Iterable
from dataclasses import dataclass
from itertools import chain
from typing import Any

INFINITY = sys.maxsize


@dataclass(eq=False, frozen=True, slots=True)
class Failure:
    index: int
    error: Any


@dataclass(eq=False, frozen=True, slots=True)
class Success:
    index: int
    value: Any


State = Failure | Success
Parser = Callable[[int, str], State]


def failure(error: Any) -> Parser:
    return lambda index, _: Failure(index, error)


def success(value: Any) -> Parser:
    return lambda index, _: Success(index, value)


def eof() -> Parser:
    def parser(index: int, actual: str) -> State:
        if index >= len(actual):
            return Success(index, None)
        return Failure(index, "EOF")

    return parser


def literal(expected: str) -> Parser:
    def parser(index: int, actual: str) -> State:
        if actual.startswith(expected, index):
            return Success(index + len(expected), expected)
        return Failure(index, expected)

    return parser


def pattern(expected: str, groups: int | str | Iterable[int | str] = 0) -> Parser:
    pattern = re.compile(expected)
    if isinstance(groups, int | str):
        groups = (groups,)

    def parser(index: int, actual: str) -> State:
        match = pattern.match(actual, index)
        if match:
            return Success(match.end(), match.group(*groups))
        return Failure(index, expected)

    return parser


def optional(a: Parser, *, default: Any) -> Parser:
    def default_value():
        return default() if callable(default) else default

    return map(
        repeat(a, 0, 1),
        lambda items: items[0] if items else default_value(),
    )


def one(*, of: list[Parser]) -> Parser:
    def parser(index: int, actual: str) -> State:
        failures: list[str] = []

        for a in of:
            match a(index, actual):
                case Success() as success:
                    return success
                case Failure(_, error):
                    if isinstance(error, str):
                        failures.append(error)
                    else:
                        failures.extend(error)

        return Failure(index, failures)

    return parser


def repeat(a: Parser, minimum: int, maximum: int | None) -> Parser:
    maximum = maximum or minimum

    def parser(index: int, actual: str) -> State:
        current_index = index
        iterations = 0
        values: list[Any] = []

        while iterations < maximum:
            match a(current_index, actual):
                case Success(index, value):
                    current_index = index
                    iterations += 1
                    values.append(value)
                case Failure() as failure:
                    if iterations >= minimum:
                        break
                    return failure

        return Success(index, values)

    return parser


def sequence(*, of: list[Parser], separator: None | Parser = None) -> Parser:
    def parser(index: int, actual: str) -> State:
        last_known_position = index
        values: list[Any] = []

        if separator:
            parsers = [separator] * ((len(of) * 2) - 1)
            parsers[0::2] = of
        else:
            parsers = of

        for p in parsers:
            match p(last_known_position, actual):
                case Success(index, value):
                    last_known_position = index
                    if p != separator:
                        values.append(value)
                case Failure() as failure:
                    return failure

        return Success(last_known_position, values)

    return parser


def bind(a: Parser, fn: Callable[[Any], Parser]) -> Parser:
    def parser(index: int, actual: str) -> State:
        match a(index, actual):
            case Failure() as failure:
                return failure
            case Success(index, value):
                return fn(value)(index, actual)

    return parser


def err(a: Parser, fn: Callable[[Any], Any]) -> Parser:
    def parser(index: int, actual: str) -> State:
        match a(index, actual):
            case Failure(index, error):
                return Failure(index, fn(error))
            case Success() as success:
                return success

    return parser


def map(a: Parser, fn: Callable[[Any], Any]) -> Parser:  # noqa: A001
    def parser(index: int, actual: str) -> State:
        match a(index, actual):
            case Failure() as failure:
                return failure
            case Success(index, value):
                return Success(index, fn(value))

    return parser


def peek(a: Parser) -> Parser:
    def parser(index: int, actual: str) -> State:
        match a(index, actual):
            case Success(_, value):
                return Success(index, value)
            case Failure() as failure:
                return failure

    return parser


def contextual(generator: Callable[[], Generator[Parser, Any, Parser]]) -> Parser:
    def parser(index: int, actual: str) -> State:
        iterator = generator()
        value = None
        try:
            while True:
                next_parser = iterator.send(value)
                match next_parser(index, actual):
                    case Success(last_index, last_value):
                        index = last_index
                        value = last_value
                    case Failure() as failure:
                        return failure
        except StopIteration as exc:
            return exc.value(index, actual)

    return parser


class ForwardDeclaration:
    def __init__(self) -> None:
        self.parser = failure("forward reference not set")

    def __call__(self, index: int, actual: str) -> State:
        return self.parser(index, actual)

    def set(self, parser: Parser) -> None:
        self.parser = parser


def array0(*, of: Parser, separator: Parser) -> Parser:
    return optional(array1(of=of, separator=separator), default=list)


def array1(*, of: Parser, separator: Parser) -> Parser:
    el0 = map(of, lambda e: [e])
    el1 = map(sequence(of=[separator, of]), lambda s: s[1])
    arr = sequence(of=[el0, many0(el1)])
    return map(arr, lambda a: list(chain(*a)))


def many0(a: Parser) -> Parser:
    return repeat(a, 0, INFINITY)


def many1(a: Parser) -> Parser:
    return repeat(a, 1, INFINITY)


def assert_failure(state: State, index: int, error: Any):
    assert isinstance(state, Failure)
    assert state.index == index
    assert state.error == error


def assert_success(state: State, index: int, value: Any):
    assert isinstance(state, Success)
    assert state.index == index
    assert state.value == value
