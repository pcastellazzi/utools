from types import SimpleNamespace
from typing import Any

import pytest

from utools.utemplate import Template, TemplateSyntaxError, VariableNotFoundError


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


def test_if_statement():
    assert tpl("{% if true %}{{ e }}{% endif %}") == "python"
    assert tpl("{% if false %}{{ e }}{% endif %}") == ""


def test_for_statement():
    assert tpl("{% for x in list_ %}{{ x }}{% endfor %}") == "123"
    assert tpl("{% for x, y in dict_.items %}{{ x }}{{ y }}{% endfor %}") == "a1b2c3"
    assert tpl("{% for z in filters %}{{ e | z }}{% endfor %}") == "PYTHONPYTHON"


# test nested for
# test non iterable
# test variables not matching iterable values (packing)
# test end not for

# test if/for
# test for/if

# test invalid statement
# test invalid variable in if
# test invalid if syntax
# test invalid for syntax

# test attribute error (property exception)
# test callable error
# test filter error

# line numbers in parsing errors
# execute inline
