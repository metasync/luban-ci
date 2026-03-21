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


def main() -> None:
    default_env = "{{ cookiecutter.default_env }}".strip()

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

