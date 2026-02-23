import sys
import os

# Try to import tomllib (Python 3.11+)
try:
    import tomllib
except ImportError:
    print("Error: tomllib not found. Ensure Python 3.11+ is used.", file=sys.stderr)
    sys.exit(1)

def parse_pyproject():
    if not os.path.exists("pyproject.toml"):
        print("No pyproject.toml found.", file=sys.stderr)
        return

    try:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
            
        # Get Execution Mode
        mode = "standard"
        tool_luban = data.get("tool", {}).get("luban", {})
        if "bp-execution-mode" in tool_luban:
            mode = tool_luban["bp-execution-mode"]
            
        print(f"MODE={mode}")
        
        # Get Scripts
        script_name = ""
        scripts = data.get("project", {}).get("scripts", {})
        if scripts:
            # Heuristic: look for common names
            common_names = ["app", "start", "main", "run"]
            for name in common_names:
                if name in scripts:
                    script_name = name
                    break
            
            # Fallback to first one
            if not script_name and len(scripts) > 0:
                script_name = list(scripts.keys())[0]
                
        print(f"SCRIPT_NAME={script_name}")
        
    except Exception as e:
        print(f"Error parsing pyproject.toml: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parse_pyproject()
