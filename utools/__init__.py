# cspell:words newhlen oldhlen

import contextlib
import logging
import os
import pathlib
import readline
import time
from collections.abc import Generator
from typing import Any

__all__ = ["DEBUG", "configure_logging", "history"]

DEBUG = "DEBUG" in os.environ


def configure_logging() -> None:
    old_record_factory = logging.getLogRecordFactory()
    epoch = time.monotonic()

    def new_record_factory(
        *args: tuple[Any], **kwargs: dict[str, Any]
    ) -> logging.LogRecord:
        record = old_record_factory(*args, **kwargs)
        record.monotonic = round(time.monotonic() - epoch, 2)
        return record

    logging.setLogRecordFactory(new_record_factory)
    logging.basicConfig(
        datefmt="%Y-%m-%d %H:%M:%S",
        format="%(monotonic)012.2F [%(levelname)s] %(name)s: %(message)s",
        level=logging.DEBUG if DEBUG else logging.INFO,
    )


@contextlib.contextmanager
def history(history_file: pathlib.Path) -> Generator[None, None, None]:
    with contextlib.suppress(FileNotFoundError, PermissionError):
        readline.read_history_file(history_file)
    oldhlen = readline.get_current_history_length()

    with contextlib.suppress(EOFError, KeyboardInterrupt):
        yield

    if hasattr(readline, "append_history_file"):
        newhlen = readline.get_current_history_length()
        readline.set_history_length(1000)
        readline.append_history_file(newhlen - oldhlen, history_file)
    else:
        readline.write_history_file(history_file)
