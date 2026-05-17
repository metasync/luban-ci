import os
from pathlib import Path


def main() -> None:
    dagster_home = os.getenv("DAGSTER_HOME")
    if not dagster_home:
        raise SystemExit("DAGSTER_HOME is not set")

    dagster_home_path = Path(dagster_home)
    if not dagster_home_path.exists():
        raise SystemExit(f"DAGSTER_HOME does not exist: {dagster_home}")

    config_path = dagster_home_path / "dagster.yaml"
    if not config_path.exists():
        raise SystemExit(f"dagster.yaml not found under DAGSTER_HOME: {config_path}")


if __name__ == "__main__":
    main()
