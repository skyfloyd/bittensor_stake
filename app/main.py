from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.router import api_router
from .core.middleware import TokenVerificationMiddleware

app = FastAPI(
    title="Bittensor Stake API",
    description="API service for querying Tao dividends and managing stake operations",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add token verification middleware
app.add_middleware(TokenVerificationMiddleware)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Bittensor Stake API"}
