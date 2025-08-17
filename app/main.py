# =============================================================================
# MAIN.PY - APPLICATION ENTRY POINT
# =============================================================================
# This is the main FastAPI application file that brings together all modules.
# 
# What this file does:
# 1. Creates the main FastAPI application instance
# 2. Sets up database tables (auto-creation)
# 3. Includes all route modules (auth, bills, trips)
# 4. Configures the application settings
# 
# User Types Supported:
# 1. Hotels: Register, upload utility bills, calculate carbon footprints
# 2. Travel Agents: Register, create trips, calculate trip carbon footprints
# 
# How FastAPI applications work:
# - main.py is the entry point that ties everything together
# - Individual modules (auth.py, routes.py) define specific functionality
# - Routers from modules are included in the main app
# - The app can be run with: uvicorn app.main:app --reload
# =============================================================================

from fastapi import FastAPI
from . import auth, routes, database

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================
# Create all database tables based on the models defined in models.py
# This happens automatically when the application starts
# If tables already exist, this does nothing (safe to run multiple times)
database.Base.metadata.create_all(bind=database.engine)

# =============================================================================
# FASTAPI APPLICATION SETUP
# =============================================================================
# Create the main FastAPI application instance
# This is the core object that handles all HTTP requests
app = FastAPI(
    title="Carbon Emission Calculator API",
    description="API for hotels and travel agents to track and calculate carbon footprints",
    version="2.0.0",
    docs_url="/docs",      # Swagger UI available at http://localhost:8000/docs
    redoc_url="/redoc"     # ReDoc documentation at http://localhost:8000/redoc
)

# =============================================================================
# ROUTER INCLUSION
# =============================================================================
# Include authentication routes from auth.py
# All routes in auth.py will be available under /auth prefix
# Available endpoints:
# - POST /auth/register - Hotel registration
# - POST /auth/login - Hotel login
# - POST /auth/register-agent - Travel agent registration
# - POST /auth/login-agent - Travel agent login
app.include_router(auth.router)

# Include utility bill management routes from routes.py  
# All routes in routes.py will be available under /bills prefix
# Available endpoints:
# - POST /bills/upload - Upload utility bill
# - GET /bills/my-bills - Get hotel's bills
# - POST /bills/calculate-footprint - Calculate carbon footprint
app.include_router(routes.router)

# Include trip management routes for travel agents
# All routes will be available under /trips prefix
# Available endpoints:
# - POST /trips/create - Create new trip with carbon calculation
# - GET /trips/my-trips - Get agent's trips
# - GET /trips/{trip_id}/carbon - Get trip carbon details
app.include_router(routes.trip_router)

# =============================================================================
# ROOT ENDPOINT (OPTIONAL)
# =============================================================================
@app.get("/")
async def root():
    """
    Root endpoint - provides basic API information.
    
    Purpose: Simple health check and API information endpoint.
    Useful for verifying the API is running.
    
    Returns:
        dict: Basic API information and available endpoints
    
    Example:
        GET http://localhost:8000/
        
        Response:
        {
            "message": "Hotel Carbon Tracking API",
            "version": "1.0.0",
            "docs": "/docs",
            "endpoints": {
                "auth": "/auth",
                "bills": "/bills"
            }
        }
    """
    return {
        "message": "Carbon Emission Calculator API",
        "version": "2.0.0",
        "docs": "/docs",
        "user_types": {
            "hotels": "Upload utility bills and track carbon consumption",
            "travel_agents": "Create trips and calculate carbon footprints"
        },
        "endpoints": {
            "auth": "/auth (registration and login for both user types)",
            "bills": "/bills (hotel utility bill management)",
            "trips": "/trips (travel agent trip management)"
        }
    }

# =============================================================================
# APPLICATION STARTUP
# =============================================================================
# To run this application:
# 1. Install dependencies: pip install -r requirements.txt
# 2. Set environment variables (see .env.example)
# 3. Run with: uvicorn app.main:app --reload
# 4. Access API documentation at: http://localhost:8000/docs
# 
# The application will be available at: http://localhost:8000
# =============================================================================