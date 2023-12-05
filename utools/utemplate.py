from collections import deque
from collections.abc import Callable, Generator, Iterable
from contextlib import suppress
from dataclasses import dataclass
from re import compile, escape
from types import TracebackType
from typing import Any, Literal, assert_never

ATTRIBUTE_SEPARATOR = "."
FILTER_SEPARATOR = "|"
IDENTIFIER_SEPARATOR = ","

L_BLOCK = "{%"
R_BLOCK = "%}"
L_COMMENT = "{#"
R_COMMENT = "#}"
L_VARIABLE = "{{"
R_VARIABLE = "}}"

KEYWORD_FOR = "for"
KEYWORD_IF = "if"
KEYWORD_END = "end"

RE_TAGS = compile(
    rf"({L_BLOCK}.*?{R_BLOCK}|{L_COMMENT}.*?{R_COMMENT}|{L_VARIABLE}.*?{R_VARIABLE})"
)

RE_IDENTIFIER = compile(r"[_a-zA-Z][_a-zA-Z0-9]*")
RE_IDENTIFIER_EXPR = compile(
    rf"{RE_IDENTIFIER.pattern}({escape(ATTRIBUTE_SEPARATOR)}{RE_IDENTIFIER.pattern})*"
)
RE_IDENTIFIER_LIST = compile(
    rf"{RE_IDENTIFIER.pattern}(\s*{escape(IDENTIFIER_SEPARATOR)}\s*{RE_IDENTIFIER.pattern})*"
)
RE_VARIABLE_EXPR = compile(
    rf"{RE_IDENTIFIER_EXPR.pattern}(\s*{escape(FILTER_SEPARATOR)}\s*{RE_IDENTIFIER_EXPR.pattern})*"
)

RE_IF_STMT = compile(rf"\s*if\s+({RE_IDENTIFIER_EXPR.pattern})")
RE_FOR_STMT = compile(
    rf"\s*for\s+({RE_IDENTIFIER_LIST.pattern})\s+in\s+({RE_IDENTIFIER_EXPR.pattern})"
)
RE_END_STMT = compile(r"end(for|if)")

UNDEFINED = object()


class TemplateError(Exception):
    @classmethod
    def python_error(cls, source: str) -> "TemplateError":
        from sys import exc_info
        from traceback import extract_tb

        lines = source.split("\n")
        lno = extract_tb(exc_info()[2])[-1][1]
        first = max(1, lno - 2)
        last = min(lno + 3, len(lines))

        src = "\n".join(
            f"{'->' if n == lno else '  '}{n:4d} {lines[n-1]}"
            for n in range(first, last)
        )
        msg = f"at line {lno}:\n{src}"

        return cls(msg)


class TemplateSyntaxError(TemplateError):
    pass


class VariableNotFoundError(TemplateError):
    pass


class CodeGenerator:
    def __init__(self):
        self.blocks = 0
        self.buffer: list[str] = []

    def __enter__(self):
        self.append("def render(context):")
        self.append("result = []")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.append("return ''.join(result)")

    def append(self, line: str):
        self.buffer.append(f"{' ' * 4 * self.blocks}{line}\n")
        if line.endswith(":"):
            self.indent()

    def result(self, line: str):
        self.append(f"result.append({line})")

    def dedent(self):
        self.blocks -= 1

    def indent(self):
        self.blocks += 1

    def __str__(self):
        return "".join(self.buffer)


class Context:
    def __init__(self, context: dict[str, Any] | None = None):
        self.context = context or {}

    def copy(self) -> "Context":
        return Context(dict(self.context))

    def merge(self, other: dict[str, Any]) -> "Context":
        self.context.update(other)
        return self

    def get(self, value: Any, name: str) -> Any:
        has_value = False

        with suppress(AttributeError):
            value = getattr(value, name)
            has_value = True

        if not has_value:
            with suppress(KeyError, TypeError):
                value = value[name]
                has_value = True

        if not has_value:
            err = f"Attribute/Item not found {name!r} in {value!r}"
            raise VariableNotFoundError(err)

        return value

    def filter(self, dotted_expression: str, initial_value: Any = UNDEFINED) -> Any:  # noqa: A003
        fragments = dotted_expression.split(ATTRIBUTE_SEPARATOR)

        if initial_value is UNDEFINED:
            value = self.context
        else:
            value = initial_value
            fragments = fragments[1:]

        last = len(fragments) - 1
        for i, name in enumerate(fragments):
            value = self.get(value, name)
            if i != last and callable(value):
                value = value()

        return value

    def variable(self, dotted_expression: str, initial_value: Any = UNDEFINED) -> Any:
        fragments = dotted_expression.split(ATTRIBUTE_SEPARATOR)

        if initial_value is UNDEFINED:
            value = self.context
        else:
            value = initial_value
            fragments = fragments[1:]

        for name in fragments:
            value = self.get(value, name)
            if callable(value):
                value = value()

        return value


class StackFrame:
    def __init__(self):
        self.stack_frame: dict[str, int] = {}

    def __contains__(self, name: str) -> bool:
        return name in self.stack_frame

    def pop(self, names: Iterable[str]):
        for name in names:
            self.stack_frame[name] -= 1
            if self.stack_frame[name] == 0:
                del self.stack_frame[name]

    def push(self, names: Iterable[str]):
        for name in names:
            if name not in self.stack_frame:
                self.stack_frame[name] = 0
            self.stack_frame[name] += 1


@dataclass(eq=False, frozen=True, slots=True)
class Token:
    kind: Literal["block", "comment", "variable", "text"]
    text: str
    line: int

    @staticmethod
    def tokenize(text: str) -> Generator["Token", None, None]:
        lineno = 1

        for token in RE_TAGS.split(text):
            if not token:
                continue

            # while the RE captures the start and end tags, it does not fail
            # if the input is incomplete ie: a template missing and end tag
            if token.startswith(L_BLOCK) and token.endswith(R_BLOCK):
                yield Token("block", token[2:-2].strip(), lineno)
            elif token.startswith(L_COMMENT) and token.endswith(R_COMMENT):
                yield Token("comment", token[2:-2].strip(), lineno)
            elif token.startswith(L_VARIABLE) and token.endswith(R_VARIABLE):
                yield Token("variable", token[2:-2].strip(), lineno)
            else:
                yield Token("text", token, lineno)

            lineno += token.count("\n")


class Template:
    renderer: Callable[[Context], str]

    def __init__(self, template: str, context: dict[str, Any] | None = None):
        self._context = Context(context or {})
        self._blocks: deque[tuple[str, tuple[str, ...]]] = deque()
        self._stack_frame = StackFrame()
        self.source = self.transpile(template)
        self.compile()

    def compile(self):  # noqa: A003
        namespace = {}
        try:
            exec(self.source, namespace)  # noqa: S102
            self.renderer = namespace["render"]
        except SyntaxError as exc:
            raise TemplateError.python_error(self.source) from exc

    def transpile(self, template: str) -> str:
        with CodeGenerator() as cg:
            for token in Token.tokenize(template):
                match token.kind:
                    case "block":
                        stmt, result = self.transpile_block(token)
                        if result:
                            cg.append(result)
                        else:
                            if not self._blocks:
                                err = f"Unexpected end{stmt} at {token!r}"
                                raise TemplateSyntaxError(err)

                            expected, names = self._blocks.pop()
                            if stmt != expected:
                                err = (
                                    f"Expected end{expected} got end{stmt} at {token!r}"
                                )
                                raise TemplateSyntaxError(err)

                            self._stack_frame.pop(names)
                            cg.dedent()
                    case "comment":
                        pass  # remove comments from the output
                    case "text":
                        cg.result(repr(token.text))
                    case "variable":
                        cg.result(self.transpile_variable_expression(token))
                    case _:  # pragma: no branch
                        assert_never(token.kind)
        return str(cg)

    def transpile_block(self, token: Token) -> tuple[str, str]:
        if m := RE_END_STMT.fullmatch(token.text):
            return (m.group(1), "")

        if m := RE_IF_STMT.fullmatch(token.text):
            variable = m.group(1).strip()
            self._blocks.append((KEYWORD_IF, ()))
            return (KEYWORD_IF, f"if context.variable({variable!r}):")

        if m := RE_FOR_STMT.fullmatch(token.text):
            variables = tuple(v.strip() for v in m.group(1).split(IDENTIFIER_SEPARATOR))
            self._blocks.append((KEYWORD_FOR, variables))
            self._stack_frame.push(variables)
            source = self.transpile_variable(m.group(3))
            return (KEYWORD_FOR, f"for {', '.join(variables)} in {source}:")

        err = f"Invalid statement {token!r}"
        raise TemplateSyntaxError(err)

    def transpile_filter(self, name: str) -> str:
        identifier, *_ = name.split(ATTRIBUTE_SEPARATOR)
        if identifier in self._stack_frame:
            return f"context.filter({name!r}, {identifier})"
        return f"context.filter({name!r})"

    def transpile_variable(self, name: str) -> str:
        identifier, *_ = name.split(ATTRIBUTE_SEPARATOR)
        if identifier in self._stack_frame:
            return f"context.variable({name!r}, {identifier})"
        return f"context.variable({name!r})"

    def transpile_variable_expression(self, token: Token) -> str:
        m = RE_VARIABLE_EXPR.fullmatch(token.text)
        if not m:
            err = f"Invalid variable expression {token!r}"
            raise TemplateSyntaxError(err)

        if FILTER_SEPARATOR in token.text:
            variable, *fragments = token.text.split(FILTER_SEPARATOR)
            variable = variable.strip()
            fragments = (f.strip() for f in fragments)

            code = self.transpile_variable(variable)
            for fragment in fragments:
                code = f"{self.transpile_filter(fragment)}({code})"
        else:
            code = self.transpile_variable(token.text)

        return f"str({code})"

    def render(self, context: dict[str, Any] | None = None) -> str:
        try:
            return self.renderer(self._context.copy().merge(context or {}))
        except TemplateError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise TemplateError.python_error(self.source) from exc
