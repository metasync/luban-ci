from __future__ import annotations

from pathlib import Path

import os


def load_dotenv(*, path: str | os.PathLike[str] = ".env", override: bool = False) -> None:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return

    for raw_line in p.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
            value = value[1:-1]

        if not override and key in os.environ:
            continue

        os.environ[key] = value
