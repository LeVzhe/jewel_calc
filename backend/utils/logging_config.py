import logging
from datetime import date
from pathlib import Path


class DailyNamedFileHandler(logging.Handler):
    """Пишет в logs/{prefix}_YYYY-MM-DD.log и открывает новый файл на следующий день."""

    def __init__(
        self,
        directory: Path,
        prefix: str,
        level: int = logging.NOTSET,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__(level)
        self.directory = Path(directory)
        self.prefix = prefix
        self.encoding = encoding
        self._current_day: str | None = None
        self._stream = None
        self.directory.mkdir(parents=True, exist_ok=True)
        self._switch_if_needed()

    def _path_for(self, day: str) -> Path:
        return self.directory / f"{self.prefix}_{day}.log"

    def _switch_if_needed(self) -> None:
        day = date.today().isoformat()
        if day == self._current_day and self._stream is not None:
            return
        if self._stream is not None:
            self._stream.close()
            self._stream = None
        path = self._path_for(day)
        self._stream = path.open("a", encoding=self.encoding)
        self._current_day = day

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._switch_if_needed()
            if self._stream is None:
                return
            self._stream.write(self.format(record) + "\n")
            self._stream.flush()
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        try:
            if self._stream is not None:
                self._stream.close()
                self._stream = None
        finally:
            super().close()


def setup_logging(level: str = "INFO") -> None:
    logs = Path("logs")
    logs.mkdir(exist_ok=True)

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    root.addHandler(console)

    app_file = DailyNamedFileHandler(logs, prefix="app", level=logging.INFO)
    app_file.setFormatter(fmt)
    root.addHandler(app_file)

    err_file = DailyNamedFileHandler(logs, prefix="errors", level=logging.ERROR)
    err_file.setFormatter(fmt)
    root.addHandler(err_file)
