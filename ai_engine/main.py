import sys
from pathlib import Path

# Ensure root is in path before importing routers so internal relative imports work 
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
import uvicorn

from ai_engine.routers import analyze
from ai_engine.routers import sector
from ai_engine.routers import portfolio
from ai_engine.routers import consumer

app = FastAPI(
    title="Market Intelligence AI Engine",
    description="Backend AI service for analyzing Indonesian stocks",
    version="1.0.0"
)

# Include routers
app.include_router(analyze.router)
app.include_router(sector.router)
app.include_router(portfolio.router)
app.include_router(consumer.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
