from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/api/python/status")
def status() -> dict[str, str]:
    return {"service": "python-api", "status": "ok"}


if __name__ == "__main__":
    # Bind to localhost only; use 0.0.0.0 when running inside a container.
    uvicorn.run(app, host="127.0.0.1", port=8000)
