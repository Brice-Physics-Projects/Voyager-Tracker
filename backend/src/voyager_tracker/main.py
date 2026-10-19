from fastapi import FastAPI

app = FastAPI(
    title="Voyager Tracker API",
    description="Explore Voyager spacecraft positions, imagery, and mission history.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}