"""
Calculator example using Polish Notation.
https://en.wikipedia.org/wiki/Polish_notation
"""

import pytest

from utools import uparser as p

number = p.pattern(r"\d+")
number = p.map(number, lambda n: int(n))

whitespace = p.pattern(r"\s*")
whitespace = p.map(whitespace, lambda _: "whitespace")

operator = p.one(
    of=[
        p.map(p.literal("+"), lambda _: "add"),
        p.map(p.literal("-"), lambda _: "sub"),
        p.map(p.literal("*"), lambda _: "mul"),
        p.map(p.literal("/"), lambda _: "div"),
    ]
)

expression = p.ForwardDeclaration()
expression_decl = p.sequence(
    of=[
        operator,
        whitespace,
        p.one(of=[number, expression]),
        whitespace,
        p.one(of=[number, expression]),
    ],
)

expression_decl = p.map(
    expression_decl,
    lambda seq: list(filter(lambda ele: ele != "whitespace", seq)),
)

expression.set(expression_decl)

expr_t = list["str | int | expr_t"]


def evaluator(expr: expr_t) -> int:
    stack: list[int] = []

    for el in reversed(expr):
        match el:
            case list():
                stack.append(evaluator(el))
            case int():
                stack.append(el)
            case "add":
                stack.append(stack.pop() + stack.pop())
            case "sub":
                stack.append(stack.pop() - stack.pop())
            case "mul":
                stack.append(stack.pop() * stack.pop())
            case "div":
                stack.append(stack.pop() // stack.pop())
            case _:
                msg = f"Unknown element {el!r}"
                raise TypeError(msg)

    return stack.pop()


def calculator(expr: str) -> int:
    state = expression(0, expr)
    match state:
        case p.Success(_, value):
            return evaluator(value)
        case _:
            pytest.fail(f"unexpected failure {state!r}")


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        ("+ 3 3", 6),
        ("- 3 3", 0),
        ("* 3 3", 9),
        ("/ 3 3", 1),
        ("+ + 1 1 1", 3),
        ("- - 1 1 1", -1),
        ("* * 2 2 2", 8),
        ("/ / 9 3 3", 1),
        ("+ 1 + 2 2", 5),
    ],
)
def test_calculator(expr: str, expected: int):
    assert calculator(expr) == expected
