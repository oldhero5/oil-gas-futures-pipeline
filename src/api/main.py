"""FastAPI main application with all routes."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from src.api.routes import auth, futures, options, system, users

app = FastAPI(
    title="Oil & Gas Futures Analysis API",
    description="API for futures and options data analysis with authentication",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(futures.router)
app.include_router(options.router)
app.include_router(users.router)
app.include_router(system.router)


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker containers."""
    return {"status": "healthy", "service": "oil-gas-futures-api"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Oil & Gas Futures Analysis API",
        "version": "1.0.0",
        "documentation": "/api/docs",
    }
