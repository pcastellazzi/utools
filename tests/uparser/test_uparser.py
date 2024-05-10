# cSpell:ignoreRegExp A+B+
# cSpell:ignoreRegExp A+C+

from collections.abc import Generator
from typing import Any, cast

from utools import uparser as p
from utools.uparser import assert_failure, assert_success


def test_failure():
    assert_failure(p.failure("apple")(0, ""), 0, "apple")


def test_success():
    assert_success(p.success("apple")(0, ""), 0, "apple")


def test_eof():
    assert_failure(p.eof()(0, "1234"), 0, "EOF")
    assert_success(p.eof()(0, ""), 0, None)


def test_literal():
    assert_failure(p.literal("A")(0, "1234"), 0, "A")
    assert_success(p.literal("A")(0, "AAAA"), 1, "A")


def test_pattern():
    digits = p.pattern(r"\d+")
    assert_failure(digits(0, "AAAA"), 0, r"\d+")
    assert_success(digits(0, "1234"), 4, "1234")

    digits = p.pattern(r"(\d+)", groups=1)
    assert_success(digits(0, "1234"), 4, "1234")

    digits = p.pattern(r"(?P<digits>\d+)", groups="digits")
    assert_success(digits(0, "1234"), 4, "1234")

    digits = p.pattern(r"(?P<digits>\d+)", groups=("digits",))
    assert_success(digits(0, "1234"), 4, "1234")

    digits = p.pattern(r"(\d{2})(\d{2})", groups=(1, 2))
    assert_success(digits(0, "1234"), 4, ("12", "34"))


def test_optional():
    digits = p.pattern(r"\d+")

    pattern = p.optional(digits, default="9999")
    assert_success(pattern(0, ""), 0, "9999")
    assert_success(pattern(0, "1234"), 4, "1234")

    pattern = p.optional(digits, default=lambda: "8888")
    assert_success(pattern(0, ""), 0, "8888")
    assert_success(pattern(0, "1234"), 4, "1234")


def test_one():
    parser = p.one(of=[p.literal("A"), p.literal("B")])
    assert_failure(parser(0, "CCCC"), 0, ["A", "B"])
    assert_success(parser(0, "BBBB"), 1, "B")
    assert_success(parser(0, "AAAA"), 1, "A")

    parser = p.one(of=[parser, p.literal("C")])
    assert_failure(parser(0, "DDDD"), 0, ["A", "B", "C"])
    assert_success(parser(0, "CCCC"), 1, "C")
    assert_success(parser(0, "BBBB"), 1, "B")
    assert_success(parser(0, "AAAA"), 1, "A")


def test_repeat():
    parser = p.repeat(p.literal("A"), 2, 3)
    assert_failure(parser(0, "BBBB"), 0, "A")
    assert_failure(parser(0, "ABBB"), 1, "A")
    assert_success(parser(0, "AABB"), 2, ["A", "A"])
    assert_success(parser(0, "AAAB"), 3, ["A", "A", "A"])
    assert_success(parser(0, "AAAA"), 3, ["A", "A", "A"])


def test_sequence():
    parser = p.sequence(of=[p.literal("A"), p.literal("B")])
    assert_failure(parser(0, "CCCC"), 0, "A")
    assert_failure(parser(0, "ACCC"), 1, "B")
    assert_success(parser(0, "ABCD"), 2, ["A", "B"])

    spaces = p.pattern(r"\s+")
    parser = p.sequence(of=[p.literal("A"), p.literal("B")], separator=spaces)
    assert_failure(parser(0, " C C C C "), 0, "A")
    assert_failure(parser(0, "A C C C "), 2, "B")
    assert_success(parser(0, "A B C D"), 3, ["A", "B"])
    assert_success(parser(0, "A B"), 3, ["A", "B"])


def test_bind():
    digits = p.pattern(r"\d+")
    alphas = p.pattern(r"\w+")
    parser = p.bind(digits, lambda _: alphas)

    assert_success(parser(0, "11AA//"), 4, "AA")
    assert_failure(parser(0, "11//AA"), 2, r"\w+")
    assert_failure(parser(0, "//11AA"), 0, r"\d+")


def test_err():
    failure = p.err(p.failure(1), lambda _: 2)
    success = p.err(p.success(1), lambda _: 2)
    assert_failure(failure(0, ""), 0, 2)
    assert_success(success(0, ""), 0, 1)


def test_map():
    failure = p.map(p.failure(1), lambda _: 2)
    success = p.map(p.success(1), lambda _: 2)
    assert_failure(failure(0, ""), 0, 1)
    assert_success(success(0, ""), 0, 2)


def test_peek():
    parser = p.peek(p.literal("1"))
    assert_failure(parser(0, "0"), 0, "1")
    assert_success(parser(0, "1"), 0, "1")


def test_contextual():
    digits = p.pattern(r"\d+")
    alphas = p.pattern(r"\w+")

    @p.contextual
    def parser() -> Generator[p.Parser, Any, Any]:
        d = yield digits
        a = yield alphas
        return p.success((d, a))

    assert_success(parser(0, "1234ABCD"), 8, ("1234", "ABCD"))
    assert_failure(parser(0, "ABCD1234"), 0, r"\d+")


def test_forward_declaration():
    nested = p.ForwardDeclaration()
    assert_failure(nested(0, ""), 0, "forward reference not set")

    nested_decl = p.sequence(
        of=[
            p.literal("("),
            p.one(of=[p.pattern(r"\d+"), nested]),
            p.literal(")"),
        ]
    )
    nested.set(nested_decl)

    assert_success(nested(0, "(0)"), 3, ["(", "0", ")"])
    assert_success(nested(0, "((0))"), 5, ["(", ["(", "0", ")"], ")"])


def test_array0():
    digits = p.pattern(r"\d+")
    comma = p.pattern(r",\s*")
    parser = p.array0(of=digits, separator=comma)

    assert_success(parser(0, ""), 0, [])
    assert_success(parser(0, "1"), 1, ["1"])
    assert_success(parser(0, "1, 2"), 4, ["1", "2"])

    s1 = cast(p.Success, parser(0, ""))
    s2 = cast(p.Success, parser(0, ""))
    assert id(s1.value) != id(s2.value)


def test_array1():
    digits = p.pattern(r"\d+")
    comma = p.pattern(r",\s*")
    parser = p.array1(of=digits, separator=comma)

    assert_failure(parser(0, ""), 0, r"\d+")
    assert_success(parser(0, "1"), 1, ["1"])
    assert_success(parser(0, "1, 2"), 4, ["1", "2"])


def test_many0():
    parser = p.many0(p.literal("A"))
    assert_success(parser(0, ""), 0, [])
    assert_success(parser(0, "A"), 1, ["A"])
    assert_success(parser(0, "AAAB"), 3, ["A", "A", "A"])


def test_many1():
    parser = p.many1(p.literal("A"))
    assert_failure(parser(0, ""), 0, "A")
    assert_success(parser(0, "A"), 1, ["A"])
    assert_success(parser(0, "AAAB"), 3, ["A", "A", "A"])
