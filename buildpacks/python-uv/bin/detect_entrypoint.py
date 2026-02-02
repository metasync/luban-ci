#!/usr/bin/env python3
import sys
import os

# Check if tomllib is available (Python 3.11+)
try:
    import tomllib
except ImportError:
    # Fallback for older python versions if needed, but we expect 3.11+
    # Since we are using uv to install python, it should be a modern version.
    sys.stderr.write("Error: tomllib module not found. Python 3.11+ is required.\n")
    sys.exit(1)

def main():
    if not os.path.exists("pyproject.toml"):
        return

    try:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        
        scripts = data.get("project", {}).get("scripts", {})
        if not scripts:
            return
        
        # Heuristic:
        # 1. If only one script, use it.
        # 2. If multiple, look for "start", "run", "main", "app".
        # 3. Otherwise, pick the first one.
        
        keys = list(scripts.keys())
        if len(keys) == 1:
            print(keys[0])
            return
        
        # Check for common names
        for name in ["app", "start"]:
            if name in keys:
                print(name)
                return
        
        # Fallback to first one
        print(keys[0])

    except Exception as e:
        # On error (e.g. invalid toml), just exit silently or print error to stderr
        sys.stderr.write(f"Error parsing pyproject.toml: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
