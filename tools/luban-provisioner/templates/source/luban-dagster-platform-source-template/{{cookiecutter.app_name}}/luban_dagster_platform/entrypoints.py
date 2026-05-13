import sys

from luban_dagster_platform.otel import configure_otel


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("expected subcommand: webserver|daemon")

    mode = sys.argv[1]
    configure_otel()

    if mode == "webserver":
        from dagster_webserver.cli import main as dagster_webserver_main

        sys.argv = ["dagster-webserver", *sys.argv[2:]]
        dagster_webserver_main()
        return

    if mode == "daemon":
        from dagster.daemon.cli import main as dagster_daemon_main

        sys.argv = ["dagster-daemon", *sys.argv[2:]]
        dagster_daemon_main()
        return

    raise SystemExit(f"unknown subcommand: {mode}")


if __name__ == "__main__":
    main()
