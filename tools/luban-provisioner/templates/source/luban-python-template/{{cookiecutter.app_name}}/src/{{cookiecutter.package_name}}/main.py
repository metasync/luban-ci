from fastapi import FastAPI
import sys
import os
from .version import __version__

app = FastAPI()


@app.get("/")
def read_root():
    greeting = os.environ.get("GREETING", "Hello")
    return {
        "message": f"{greeting} from {{cookiecutter.project_name}}/{{cookiecutter.app_name}}!",
        "python_version": sys.version,
        "version": __version__,
    }


def start():
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("{{cookiecutter.package_name}}.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    start()
