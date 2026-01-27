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

**Important**: This buildpack does **not** set a default start command (it does not parse `Procfile`).

You must specify the start command in your container configuration (e.g., Kubernetes Deployment).

**Recommendation**: Use `args` in Kubernetes to pass arguments to the default entrypoint (CNB Launcher).

```yaml
spec:
  containers:
  - name: my-app
    image: my-registry/my-app:latest
    # Use args so the CNB Launcher runs first and sets up PATH
    args:
      - uv
      - run
      - uvicorn
      - main:app
      - --host
      - 0.0.0.0
```

If you use `command`, you override the Launcher, and `uv` will not be found in the PATH unless you manually set it.
