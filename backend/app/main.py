from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import dashboard, works, work_detail, risk, ai_integration, inspection, anomalies, vendors

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MPLADS Intelligence Platform",
    description="AI-powered anomaly detection and inspection prioritization for MPLADS",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router)
app.include_router(works.router)
app.include_router(work_detail.router)
app.include_router(risk.router)
app.include_router(ai_integration.router)
app.include_router(inspection.router)
app.include_router(anomalies.router)
app.include_router(vendors.router)

@app.get("/")
async def root():
    return {
        "name": "MPLADS Intelligence Platform",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
