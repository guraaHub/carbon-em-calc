# =============================================================================
# AUTH.PY - AUTHENTICATION MODULE
# =============================================================================
# This module handles all authentication-related functionality including:
# - Hotel registration and login (for bill uploads and carbon tracking)
# - Travel agent registration and login (for trip management)
# - JWT token generation and validation
# - Authentication middleware for protecting routes
# 
# Two Types of Users:
# 1. Hotels: Upload utility bills, track their carbon consumption
# 2. Travel Agents: Create trips, calculate trip carbon footprints
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from . import models, schemas, database
from passlib.hash import bcrypt  # For password hashing
import jwt  # For creating and verifying JSON Web Tokens
import os
from datetime import datetime, timedelta

# Create a FastAPI router for authentication endpoints
# All routes in this module will be prefixed with "/auth"
router = APIRouter(prefix="/auth", tags=["Auth"])

# HTTP Bearer token security scheme for JWT authentication
# This tells FastAPI to expect "Authorization: Bearer <token>" headers
security = HTTPBearer()

# =============================================================================
# JWT (JSON Web Token) Configuration
# =============================================================================
# JWT tokens are used to maintain user sessions securely
# They contain encrypted hotel information that proves identity
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"  # Algorithm used for signing JWT tokens

def create_access_token(data: dict):
    """
    Creates a JWT access token containing hotel information.
    
    Purpose: When a hotel logs in successfully, we create a token that contains
    their hotel_id and hotel_name. This token serves as proof of identity for
    future API requests.
    
    Args:
        data (dict): Dictionary containing hotel information (hotel_id, hotel_name)
    
    Returns:
        str: Encoded JWT token that expires in 24 hours
    
    Example:
        token = create_access_token({"hotel_id": 123, "hotel_name": "Grand Hotel"})
    """
    to_encode = data.copy()  # Copy the data to avoid modifying original
    expire = datetime.utcnow() + timedelta(hours=24)  # Token expires in 24 hours
    to_encode.update({"exp": expire})  # Add expiration time to token
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_current_hotel(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Authentication dependency function that validates JWT tokens.
    
    Purpose: This function is used to protect routes that require authentication.
    It extracts and validates the JWT token from the request header, then
    returns the hotel information if the token is valid.
    
    How it works:
    1. Extracts token from "Authorization: Bearer <token>" header
    2. Decodes and validates the JWT token
    3. Extracts hotel_id and hotel_name from token payload
    4. Returns hotel information if valid, raises error if invalid
    
    Args:
        credentials: Automatically injected by FastAPI from Authorization header
    
    Returns:
        dict: {"hotel_id": int, "hotel_name": str} - Information about authenticated hotel
    
    Raises:
        HTTPException: 401 error if token is invalid, expired, or missing hotel info
    
    Usage:
        @app.get("/protected-route")
        def protected(current_hotel: dict = Depends(get_current_hotel)):
            hotel_id = current_hotel["hotel_id"]  # Get the authenticated hotel's ID
    """
    try:
        # Extract the actual token from "Bearer <token>"
        token = credentials.credentials
        
        # Decode and verify the JWT token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Extract hotel information from token payload
        hotel_id = payload.get("hotel_id")
        hotel_name = payload.get("hotel_name")
        
        # Ensure both hotel_id and hotel_name are present
        if not hotel_id or not hotel_name:
            raise HTTPException(status_code=401, detail="Invalid token: missing hotel information")
            
        return {"hotel_id": hotel_id, "hotel_name": hotel_name}
    
    except jwt.ExpiredSignatureError:
        # Token has expired (older than 24 hours)
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        # Token is malformed, has wrong signature, or other JWT error
        raise HTTPException(status_code=401, detail="Invalid token")

# =============================================================================
# AUTHENTICATION API ENDPOINTS
# =============================================================================

@router.post("/register")
def register(hotel: schemas.HotelCreate, db: Session = Depends(database.get_db)):
    """
    Hotel Registration Endpoint
    
    Purpose: Allows new hotels to create accounts in the system.
    
    How it works:
    1. Receives hotel registration data (name, email, password)
    2. Checks if email is already registered (prevents duplicates)
    3. Hashes the password for security (never store plain passwords!)
    4. Creates new hotel record in database
    5. Returns success message
    
    Args:
        hotel (HotelCreate): Contains name, email, password from request body
        db (Session): Database connection automatically injected by FastAPI
    
    Returns:
        dict: Success message confirming registration
    
    Raises:
        HTTPException: 400 error if email is already registered
    
    Request Body Example:
        {
            "name": "Grand Resort Hotel",
            "email": "admin@grandresort.com", 
            "password": "securepassword123"
        }
    
    Response Example:
        {"message": "Hotel registered successfully"}
    """
    # Check if a hotel with this email already exists
    existing_hotel = db.query(models.Hotel).filter(models.Hotel.email == hotel.email).first()
    if existing_hotel:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password using bcrypt (secure one-way encryption)
    # We NEVER store plain text passwords in the database
    hashed_pw = bcrypt.hash(hotel.password)
    
    # Create new hotel object with hashed password
    db_hotel = models.Hotel(name=hotel.name, email=hotel.email, password=hashed_pw)
    
    # Add to database and save changes
    db.add(db_hotel)       # Stage the new hotel for insertion
    db.commit()            # Save to database
    db.refresh(db_hotel)   # Refresh to get auto-generated ID
    
    return {"message": "Hotel registered successfully"}

@router.post("/login")
def login(hotel: schemas.HotelLogin, db: Session = Depends(database.get_db)):
    """
    Hotel Login Endpoint
    
    Purpose: Authenticates hotel credentials and provides JWT access token.
    
    How it works:
    1. Receives login credentials (email, password)
    2. Looks up hotel by email in database
    3. Verifies password against stored hash
    4. If valid, creates JWT token containing hotel information
    5. Returns token that can be used for future authenticated requests
    
    Args:
        hotel (HotelLogin): Contains email and password from request body
        db (Session): Database connection automatically injected by FastAPI
    
    Returns:
        dict: Contains access token, token type, and hotel information
    
    Raises:
        HTTPException: 400 error if email doesn't exist or password is wrong
    
    Request Body Example:
        {
            "email": "admin@grandresort.com",
            "password": "securepassword123"
        }
    
    Response Example:
        {
            "message": "Login successful",
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "token_type": "bearer",
            "hotel_id": 123,
            "hotel_name": "Grand Resort Hotel"
        }
    
    How to use the token:
        Include in future requests as: "Authorization: Bearer <access_token>"
    """
    # Find hotel by email address
    db_hotel = db.query(models.Hotel).filter(models.Hotel.email == hotel.email).first()
    
    # Check if hotel exists and password is correct
    # bcrypt.verify() compares plain password with hashed password
    if not db_hotel or not bcrypt.verify(hotel.password, db_hotel.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    # Create JWT token containing hotel identification information
    # This token will be sent with future requests to prove identity
    access_token = create_access_token(
        data={"hotel_id": db_hotel.id, "hotel_name": db_hotel.name}
    )
    
    # Return token and hotel information
    return {
        "message": "Login successful", 
        "access_token": access_token,          # JWT token for authentication
        "token_type": "bearer",                # Type of token (standard for JWT)
        "hotel_id": db_hotel.id,              # Hotel's unique ID
        "hotel_name": db_hotel.name           # Hotel's name
    }

# =============================================================================
# TRAVEL AGENT AUTHENTICATION FUNCTIONS
# =============================================================================

def get_current_travel_agent(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(database.get_db)
):
    """
    Middleware function to get currently authenticated travel agent.
    
    Purpose: This function is used as a dependency in protected routes.
    It verifies the JWT token and returns the travel agent information.
    
    Process:
    1. Extract token from Authorization header
    2. Decode and verify the JWT token
    3. Extract travel agent information from token
    4. Fetch travel agent details from database
    5. Return travel agent object or raise error if invalid
    
    Args:
        credentials: HTTP Authorization header containing JWT token
        db: Database session for querying travel agent information
    
    Returns:
        models.TravelAgent: The authenticated travel agent object
    
    Raises:
        HTTPException: If token is invalid, expired, or travel agent not found
    
    Usage in route:
        @router.get("/protected-endpoint")
        def protected_route(current_agent: models.TravelAgent = Depends(get_current_travel_agent)):
            return {"agent_id": current_agent.id}
    """
    try:
        # Extract the Bearer token from Authorization header
        token = credentials.credentials
        
        # Decode the JWT token using secret key and algorithm
        # This verifies the token signature and extracts the payload
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Extract travel agent information from token payload
        agent_id: int = payload.get("agent_id")
        if agent_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: missing agent_id")
        
        # Query database to get travel agent details
        # This ensures the travel agent still exists and hasn't been deleted
        db_agent = db.query(models.TravelAgent).filter(models.TravelAgent.id == agent_id).first()
        if db_agent is None:
            raise HTTPException(status_code=401, detail="Travel agent not found")
        
        return db_agent
        
    except jwt.ExpiredSignatureError:
        # Token has expired (older than 24 hours)
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        # Token is malformed or signature is invalid
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/register-agent")
def register_travel_agent(agent: schemas.TravelAgentCreate, db: Session = Depends(database.get_db)):
    """
    Register a new travel agent account.
    
    Purpose: Creates a new travel agent account in the system.
    Travel agents can register to manage trips and calculate carbon footprints.
    
    Process:
    1. Check if email already exists
    2. Hash the password for security
    3. Create new travel agent record in database
    4. Return confirmation message
    
    Args:
        agent (schemas.TravelAgentCreate): Agent registration data (name, email, password, company)
        db (Session): Database session for creating new agent record
    
    Returns:
        dict: Success message with agent information
    
    Example Request:
        POST /auth/register-agent
        {
            "name": "Sarah Travel",
            "email": "sarah@travelagency.com",
            "password": "securepass123",
            "company": "Global Adventures Ltd"
        }
    
    Example Response:
        {
            "message": "Travel agent registered successfully",
            "agent_id": 1,
            "agent_name": "Sarah Travel"
        }
    """
    # Check if travel agent with this email already exists
    existing_agent = db.query(models.TravelAgent).filter(models.TravelAgent.email == agent.email).first()
    if existing_agent:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password before storing in database
    # bcrypt creates a secure hash that can't be reversed
    hashed_password = bcrypt.hash(agent.password)
    
    # Create new travel agent record
    db_agent = models.TravelAgent(
        name=agent.name,
        email=agent.email,
        password=hashed_password,  # Store hashed password, never plain text
        company=agent.company
    )
    
    # Add to database and commit changes
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)  # Refresh to get the assigned ID
    
    return {
        "message": "Travel agent registered successfully",
        "agent_id": db_agent.id,
        "agent_name": db_agent.name
    }

@router.post("/login-agent")
def login_travel_agent(agent: schemas.TravelAgentLogin, db: Session = Depends(database.get_db)):
    """
    Authenticate travel agent and return JWT token.
    
    Purpose: Verifies travel agent credentials and returns a JWT token
    for accessing protected endpoints.
    
    Process:
    1. Find travel agent by email
    2. Verify password using bcrypt
    3. Create JWT token with agent information
    4. Return token and agent details
    
    Args:
        agent (schemas.TravelAgentLogin): Login credentials (email, password)
        db (Session): Database session for querying agent
    
    Returns:
        dict: JWT token and agent information
    
    Example Request:
        POST /auth/login-agent
        {
            "email": "sarah@travelagency.com",
            "password": "securepass123"
        }
    
    Example Response:
        {
            "message": "Login successful",
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "token_type": "bearer",
            "agent_id": 1,
            "agent_name": "Sarah Travel"
        }
    
    How to use the token:
        Include in future requests as: "Authorization: Bearer <access_token>"
    """
    # Find travel agent by email address
    db_agent = db.query(models.TravelAgent).filter(models.TravelAgent.email == agent.email).first()
    
    # Check if agent exists and password is correct
    if not db_agent or not bcrypt.verify(agent.password, db_agent.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    # Create JWT token containing agent identification information
    access_token = create_access_token(
        data={"agent_id": db_agent.id, "agent_name": db_agent.name}
    )
    
    # Return token and agent information
    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "agent_id": db_agent.id,
        "agent_name": db_agent.name
    }
