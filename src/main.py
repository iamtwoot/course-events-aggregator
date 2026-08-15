from fastapi import FastAPI

app = FastAPI(title="Events Aggregator")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
