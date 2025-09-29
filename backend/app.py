from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import data_routes, suggestion_engine
from database import engine
import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Data Visualization Dashboard API",
    description="Backend API for data visualization dashboard with upload and suggestion capabilities",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(data_routes.router, prefix="/api/data", tags=["data"])
app.include_router(suggestion_engine.router, prefix="/api/suggestions", tags=["suggestions"])

@app.get("/")
async def root():
    """Root endpoint returning API information"""
    return {
        "message": "Data Visualization Dashboard API",
        "version": "1.0.0",
        "endpoints": {
            "/api/data/upload": "POST - Upload data files",
            "/api/data/summary": "GET - Get data summary",
            "/api/data/data": "GET - Get processed data",
            "/api/suggestions/suggestions": "GET - Get chart suggestions"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}