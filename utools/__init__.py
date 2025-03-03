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


def configure_logging() -> None:  # pragma: no cover
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
def history(
    history_file: pathlib.Path,
) -> Generator[None, None, None]:  # pragma: no cover
    with contextlib.suppress(FileNotFoundError, PermissionError):
        readline.read_history_file(history_file)
    old_history_length = readline.get_current_history_length()

    with contextlib.suppress(EOFError, KeyboardInterrupt):
        yield

    if hasattr(readline, "append_history_file"):
        new_history_length = readline.get_current_history_length()
        readline.set_history_length(1000)
        readline.append_history_file(
            new_history_length - old_history_length, history_file
        )
    else:
        readline.write_history_file(history_file)
