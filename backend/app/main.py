from fastapi import FastAPI

app = FastAPI(title="QualityTube OS API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
