from fastapi import FastAPI
import sys

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "message": "Hello from Luban CI Sample App!",
        "python_version": sys.version
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
