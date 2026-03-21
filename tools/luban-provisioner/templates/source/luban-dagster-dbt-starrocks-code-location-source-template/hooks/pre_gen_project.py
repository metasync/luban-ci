def main() -> None:
    default_env = "{{ cookiecutter.default_env }}".strip()

    supported = {"development", "sandbox", "production"}

    if not default_env:
        raise ValueError("cookiecutter.default_env must be non-empty")

    if default_env not in supported:
        raise ValueError(
            f"Unsupported cookiecutter.default_env ({default_env}). Supported: {sorted(supported)}"
        )


if __name__ == "__main__":
    main()
