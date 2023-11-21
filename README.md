utools
======

utools


Tools
=====

* https://black.readthedocs.io
* https://poetry.eustace.io
* https://pytest.org
    * https://pypi.org/project/pytest-cov/
* https://ruff.rs
* https://pyup.io/safety


Usage
=====

This project uses [poetry](https://poetry.eustace.io) and a `Makefile` to glue some tasks
together.


Make targets
------------

* all (default: run the other task in the listed order)
* test ([pytest](https://pytest.org))
* check-code-format ([black](https://black.readthedocs.io))
* check-code-quality ([ruff](https://ruff.rs))
* check-dependencies ([safety](https://pyup.io/safety))
