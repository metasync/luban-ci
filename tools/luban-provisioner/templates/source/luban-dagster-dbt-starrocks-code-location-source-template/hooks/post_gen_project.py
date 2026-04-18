from __future__ import annotations

from pathlib import Path


def _remove_output_block(lines: list[str], output_name: str) -> list[str]:
    header = f"    {output_name}:"
    start = None
    for i, line in enumerate(lines):
        if line.rstrip("\n") == header:
            start = i
            break

    if start is None:
        return lines

    end = len(lines)
    for j in range(start + 1, len(lines)):
        line = lines[j]
        if line.startswith("    ") and not line.startswith("      ") and line.rstrip("\n").endswith(":"):
            end = j
            break

    kept = lines[:start] + lines[end:]

    while len(kept) >= 2 and kept[start - 1].strip() == "" and kept[start].strip() == "":
        kept.pop(start)

    return kept


def _replace_default_target(text: str, default_env: str) -> str:
    needle = "env_var('DBT_TARGET', 'development')"
    replacement = f"env_var('DBT_TARGET', '{default_env}')"
    return text.replace(needle, replacement)


def _set_env_var(lines: list[str], key: str, value: str) -> list[str]:
    prefix = f"{key}="
    replacement = f"{prefix}{value}\n"
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = replacement
            return lines
    return lines + [replacement]


def main() -> None:
    default_env = "{{ cookiecutter.default_env }}".strip()

    pyproject_in = Path("pyproject.toml.in")
    pyproject_out = Path("pyproject.toml")
    if pyproject_in.exists() and not pyproject_out.exists():
        pyproject_in.rename(pyproject_out)

    env_example = Path(".env.example")
    if env_example.exists():
        lines = env_example.read_text(encoding="utf-8").splitlines(keepends=True)
        lines = _set_env_var(lines, "DAGSTER_HOME", str((Path.cwd() / "dagster_home").resolve()))
        lines = _set_env_var(lines, "LUBAN_REPO_ROOT", str(Path.cwd().resolve()))
        env_example.write_text("".join(lines), encoding="utf-8")

    profiles_path = Path("dbt_project") / "profiles.yml"
    if not profiles_path.exists():
        return

    text = profiles_path.read_text(encoding="utf-8")
    text = _replace_default_target(text, default_env)

    if default_env in {"sandbox", "production"}:
        lines = text.splitlines(keepends=True)
        lines = _remove_output_block(lines, "development")
        text = "".join(lines)

    profiles_path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
