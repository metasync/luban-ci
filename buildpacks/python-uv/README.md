# Luban CI Python uv Buildpack

This is a custom Cloud Native Buildpack (CNB) for Python applications, utilizing `uv` for ultra-fast dependency management.

## Features

- **Fast Dependency Installation**: Uses `uv sync` to install dependencies.
- **Python Version Management**: Supports specifying Python version via `.uv-version` or `pyproject.toml`.
- **Runtime Environment**: Sets up the environment so `uv` and Python are available in the PATH.

## Usage

### Prerequisites

Your application repository should have:
1.  `pyproject.toml`: Defining your project and dependencies.
2.  `uv.lock` (Recommended): For reproducible builds.
3.  `.uv-version` (Optional): To pin a specific `uv` version (e.g., `0.5.21`).

### Detection

The buildpack detects a Python application if any of the following exist:
- `pyproject.toml`
- `uv.lock`
- `.python-version`

### Build Process

1.  **Install uv**: Downloads and installs `uv` (version specified or default).
2.  **Install Python**: `uv` automatically manages the Python toolchain.
3.  **Install Dependencies**: Runs `uv sync --frozen` (if lockfile exists) or `uv sync`.
4.  **Launch Configuration**: Sets up the environment variables (PATH) for the runtime.

### Runtime Configuration

The buildpack attempts to automatically detect the start command from `pyproject.toml`.

1.  **Automatic Detection**: If `[project.scripts]` is defined in `pyproject.toml`, the buildpack will use one of the scripts as the default `web` process.
    -   It prioritizes scripts named `app`, `start`, `main`, or `run`.
    -   If none of these are found, it uses the first script defined.
    -   The command will be: `uv run <script-name>`.

2.  **Manual Configuration**: If no script is detected, or if you want to override the default, you must specify the start command in your container configuration (e.g., Kubernetes Deployment).

**Recommendation**: Use `args` in Kubernetes to pass arguments to the default entrypoint (CNB Launcher). This ensures the CNB Launcher runs first and sets up the environment (PATH, etc.).

```yaml
spec:
  containers:
  - name: my-app
    image: my-registry/my-app:latest
    # Override the default command or set one if not detected
    args:
      - uv
      - run
      - uvicorn
      - main:app
      - --host
      - 0.0.0.0
```

**Note**: This buildpack does **not** support `Procfile`.
