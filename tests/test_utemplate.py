from types import SimpleNamespace
from typing import Any

import pytest

from utools.utemplate import (
    Template,
    TemplateError,
    TemplateSyntaxError,
    VariableNotFoundError,
)


def filter_error(_: str) -> str:
    return str(1 / 0)


def filter_upper(text: str) -> str:
    return text.upper()


TEST_CONTEXT = {
    "a": "direct lookup",
    "b": lambda: "callable",
    "c": SimpleNamespace(a="attribute lookup", b=lambda: "callable"),
    "d": {"a": "item lookup", "b": lambda: "callable"},
    "e": "python",
    "f": {"upper": filter_upper},
    "g": SimpleNamespace(upper=filter_upper, a=lambda: {"upper": filter_upper}),
    "error": filter_error,
    "upper": filter_upper,
    "true": True,
    "false": False,
    "list_": [1, 2, 3],
    "dict_": {"a": 1, "b": 2, "c": 3},
    "filters": [filter_upper, filter_upper],
}


def tpl(text: str, ctx: dict[str, Any] | None = None) -> str:
    return Template(text, TEST_CONTEXT).render(ctx)


def test_text():
    assert tpl("this is text") == "this is text"


def test_comments():
    assert tpl("{# this is should be text") == "{# this is should be text"
    assert tpl("{# this is a comment #}") == ""


def test_variable_errors():
    with pytest.raises(VariableNotFoundError) as exc:
        tpl("{{ missing }}")
    assert exc.match(r"Attribute/Item not found 'missing' in ")

    with pytest.raises(TemplateSyntaxError) as exc:
        tpl("{{ #invalid# }}")
    assert exc.match(r"Invalid variable expression")

    with pytest.raises(TemplateSyntaxError) as exc:
        tpl("{{ a | #invalid# }}")
    assert exc.match(r"Invalid variable expression")


def test_variables():
    assert tpl("{{ this should be text") == "{{ this should be text"
    assert tpl("{{ a }}") == "direct lookup"
    assert tpl("{{ b }}") == "callable"

    assert tpl("{{ c.a }}") == "attribute lookup"
    assert tpl("{{ c.b }}") == "callable"

    assert tpl("{{ d.a }}") == "item lookup"
    assert tpl("{{ d.b }}") == "callable"

    assert tpl("{{ e.lower.upper.capitalize }}") == "Python"

    assert tpl("{{ e | upper }}") == "PYTHON"
    assert tpl("{{ e | f.upper }}") == "PYTHON"
    assert tpl("{{ e | g.upper }}") == "PYTHON"
    assert tpl("{{ e | f.upper | g.upper }}") == "PYTHON"
    assert tpl("{{ e | g.a.upper }}") == "PYTHON"


def test_block_errors():
    with pytest.raises(TemplateSyntaxError) as exc:
        tpl("{% endfor %}")
    assert exc.match("Unexpected endfor at ")

    with pytest.raises(TemplateSyntaxError) as exc:
        tpl("{% endif %}")
    assert exc.match("Unexpected endif at ")

    with pytest.raises(TemplateSyntaxError) as exc:
        tpl("{% endcase %}")
    assert exc.match(r"Invalid statement.*?endcase")

    with pytest.raises(TemplateSyntaxError) as exc:
        tpl("{% if true %}{{ e }}{% endfor %}")
    assert exc.match(r"Expected endif got endfor at ")

    with pytest.raises(TemplateSyntaxError) as exc:
        tpl("{% if %}{{ x }}{% endif %}")
    assert exc.match("Invalid statement.*?if")

    with pytest.raises(TemplateSyntaxError) as exc:
        tpl("{% for %}{{ x }}{% endfor %}")
    assert exc.match("Invalid statement.*?for")


def test_render_error():
    with pytest.raises(TemplateError) as exc:
        tpl("{{ a | error }}")
    assert exc.match("ZeroDivisionError: division by zero")

    with pytest.raises(TemplateError) as exc:
        tpl("{% for x in true %}{{ x }}{% endfor %}")
    assert exc.match("TypeError: 'bool' object is not iterable")

    with pytest.raises(TemplateError) as exc:
        tpl("{% for x, y in list_ %}{{ x }}{% endfor %}")
    assert exc.match("TypeError: cannot unpack non-iterable int object")


def test_if_statement():
    assert tpl("{% if true %}{{ e }}{% endif %}") == "python"
    assert tpl("{% if false %}{{ e }}{% endif %}") == ""

    with pytest.raises(VariableNotFoundError) as exc:
        tpl("{% if z %}{{ z }}{% endif %}")
    assert exc.match("Attribute/Item not found 'z'")


def test_for_statement():
    assert tpl("{% for x in list_ %}{{ x }}{% endfor %}") == "123"
    assert tpl("{% for x, y in dict_.items %}{{ x }}{{ y }}{% endfor %}") == "a1b2c3"
    assert tpl("{% for z in filters %}{{ e | z }}{% endfor %}") == "PYTHONPYTHON"


def test_nesting():
    assert (
        tpl(
            "{% for x in list_ %}{% for y in list_ %}{{ x }}{{ y }}{% endfor %}{% endfor %}"
        )
        == "111213212223313233"
    )

    assert (
        tpl(
            "{% for x in list_ %}{% for x in list_ %}{{ x }}{{ x }}{% endfor %}{% endfor %}"
        )
        == "112233112233112233"
    )

    assert (
        tpl("{% if true %}{% for x in list_ %}{{ x }}{% endfor %}{% endif %}") == "123"
    )

    assert tpl("{% if false %}{% for x in list_ %}{{ x }}{% endfor %}{% endif %}") == ""

    assert (
        tpl("{% for x in list_ %}{% if true %}{{ x }}{% endif %}{% endfor %}") == "123"
    )

    assert tpl("{% for x in list_ %}{% if false %}{{ x }}{% endif %}{% endfor %}") == ""
