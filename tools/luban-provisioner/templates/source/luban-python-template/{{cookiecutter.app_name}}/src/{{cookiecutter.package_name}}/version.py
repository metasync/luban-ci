import importlib.metadata
import tomllib
from pathlib import Path


def get_version() -> str:
    # 1. Try to get version from installed package metadata
    try:
        return importlib.metadata.version("{{cookiecutter.app_name}}")
    except importlib.metadata.PackageNotFoundError:
        pass

    # 2. Fallback: Read from pyproject.toml (for local development)
    # Since we require Python >= 3.12, tomllib is always available
    try:
        # pyproject.toml is 2 levels up from src/luban_hello_world_py/
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)
                return data.get("project", {}).get("version", "0.0.0")
    except Exception:
        pass

    return "0.0.0"


__version__ = get_version()
