import argparse
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
LUBAN_CONFIG = ROOT / "manifests" / "config" / "luban-config.yaml"


def read_default_git_provider() -> str:
    text = LUBAN_CONFIG.read_text(encoding="utf-8")
    m = re.search(r"^\s*default_git_provider:\s*\"(?P<v>[^\"]+)\"\s*$", text, re.M)
    if not m:
        raise SystemExit("default_git_provider not found in manifests/config/luban-config.yaml")
    return m.group("v").strip()


def update_file(path: pathlib.Path, provider: str) -> bool:
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)

    changed = False
    i = 0
    while i < len(lines):
        line = lines[i]

        m = re.match(r"^(?P<indent>\s*)-\s*name:\s*git_provider\s*$", line)
        if not m:
            i += 1
            continue

        base_indent = m.group("indent")
        j = i + 1
        value_line_idx = None
        enum_found = False

        while j < len(lines):
            cur = lines[j]

            if re.match(rf"^{re.escape(base_indent)}-\s*name:\s*\S+", cur):
                break
            if re.match(rf"^{re.escape(base_indent)}-\s*$", cur):
                break

            if re.match(rf"^{re.escape(base_indent)}\s*value:\s*\"(github|azure|ado)\"\s*$", cur):
                value_line_idx = j

            if re.match(rf"^{re.escape(base_indent)}\s*enum:\s*(\[.*\]|$)", cur):
                enum_found = True
            j += 1

        if enum_found and value_line_idx is not None:
            current = lines[value_line_idx]
            new = re.sub(r"\"(github|azure|ado)\"", f"\"{provider}\"", current)
            if new != current:
                lines[value_line_idx] = new
                changed = True

        i = j

    if not changed:
        return False

    path.write_text("".join(lines), encoding="utf-8")
    return True


def iter_target_files() -> list[pathlib.Path]:
    targets: list[pathlib.Path] = []
    targets.extend((ROOT / "manifests" / "workflows").rglob("*.yaml"))
    targets.extend((ROOT / "tools" / "luban-provisioner" / "templates").rglob("*.yaml"))
    return targets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider",
        choices=["github", "azure", "ado"],
        default=None,
        help="Override default_git_provider from manifests/config/luban-config.yaml",
    )
    parser.add_argument("--check", action="store_true", help="Exit non-zero if changes are needed")
    args = parser.parse_args()

    provider = args.provider or read_default_git_provider()
    if provider not in {"github", "azure", "ado"}:
        raise SystemExit(f"Invalid default_git_provider: {provider}")

    changed_files: list[pathlib.Path] = []
    for path in iter_target_files():
        try:
            if update_file(path, provider):
                changed_files.append(path)
        except UnicodeDecodeError:
            continue

    if args.check:
        if changed_files:
            joined = "\n".join(str(p.relative_to(ROOT)) for p in changed_files)
            raise SystemExit(f"Default git_provider is not updated in:\n{joined}")
        return

    if changed_files:
        print(f"Updated {len(changed_files)} file(s) to default_git_provider={provider}.")
    else:
        print(f"No changes needed (default_git_provider={provider}).")


if __name__ == "__main__":
    main()

