from fastapi import FastAPI

app = FastAPI(title="Searcher API")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
