# utools

utools

##  Tools

- <https://docs.astral.sh/uv/>
- <https://pytest.org>
- <https://pytest-cov.readthedocs.io/en/latest/index.html>
- <https://ruff.rs>
- <https://google.github.io/osv-scanner/>

## Usage

This project uses [uv](https://docs.astral.sh/uv/) and a `Makefile` to glue
some tasks together.

##  Make targets

- all (default: runs install, check and test)
- clean (remove files not under version control)
- install (create or update the project venv)
- check (runs ruff and osv-scanner)
- test (runs pytest with code coverage)
- integration (run tests against the 3 latest minor python versions)
