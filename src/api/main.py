"""FastAPI main application with health check."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Oil & Gas Futures Analysis API",
    description="API for futures and options data analysis",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker containers."""
    return {"status": "healthy", "service": "oil-gas-futures-api"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Oil & Gas Futures Analysis API", "version": "1.0.0"}
