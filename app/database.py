# =============================================================================
# DATABASE.PY - DATABASE CONNECTION AND CONFIGURATION
# =============================================================================
# This module handles the database connection setup using SQLAlchemy.
# 
# What does this module do?
# 1. Establishes connection to PostgreSQL database
# 2. Creates a session factory for database transactions
# 3. Provides base class for all database models
# 4. Provides dependency function for FastAPI route injection
# 
# Key Concepts:
# - Engine: The main database connection interface
# - Session: Individual database transaction/conversation
# - Base: Parent class that all models inherit from
# =============================================================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# =============================================================================
# DATABASE CONNECTION CONFIGURATION
# =============================================================================

# Get database connection details from environment variables
# This approach keeps sensitive information out of the code
# The DATABASE_URL should be in format:
# postgresql://username:password@hostname:port/database_name
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://yourdbuser:yourdbpassword@yourdbhost:5432/yourdbname"  # Default/example
)

# Create the database engine
# The engine is the core interface to the database
# It manages the actual database connections and connection pooling
engine = create_engine(DATABASE_URL)

# Create a session factory
# Sessions are individual conversations with the database
# Each session can contain multiple operations (insert, update, delete)
# autocommit=False: Changes aren't saved until explicitly committed
# autoflush=False: Changes aren't sent to DB until explicitly flushed
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for all database models
# All model classes (Hotel, UtilityBill) will inherit from this
# This gives them database functionality like table creation
Base = declarative_base()

# =============================================================================
# DATABASE SESSION DEPENDENCY
# =============================================================================

def get_db():
    """
    Database session dependency for FastAPI routes.
    
    Purpose: Provides a database session to API endpoints and automatically
    handles opening and closing the connection.
    
    How it works:
    1. Creates a new database session
    2. Yields it to the requesting function (via FastAPI's Depends())
    3. Automatically closes the session when the request is done
    4. Ensures database connections are properly cleaned up
    
    Why use dependency injection?
    - Automatic connection management
    - Easy testing (can mock database)
    - Clean separation of concerns
    - Handles connection errors gracefully
    
    Usage in API endpoints:
        @app.post("/some-endpoint")
        def my_endpoint(db: Session = Depends(get_db)):
            # 'db' is automatically provided by FastAPI
            # Use db.query(), db.add(), db.commit(), etc.
            hotels = db.query(Hotel).all()
            return hotels
            # Database session automatically closed after function returns
    
    Yields:
        Session: SQLAlchemy database session for performing queries
    
    Note: This is a generator function (uses 'yield' instead of 'return')
    The 'finally' block ensures cleanup even if an error occurs.
    """
    # Create a new database session
    db = SessionLocal()
    try:
        # Provide the session to the requesting function
        yield db
    finally:
        # Always close the session when done, even if an error occurred
        # This prevents database connection leaks
        db.close()

# =============================================================================
# USAGE EXAMPLES
# =============================================================================
#
# In your API routes, you'll use the database session like this:
#
# @router.post("/create-hotel")
# def create_hotel(hotel_data: dict, db: Session = Depends(get_db)):
#     # Create new hotel
#     new_hotel = Hotel(name=hotel_data["name"], email=hotel_data["email"])
#     
#     # Add to session (stages for insert)
#     db.add(new_hotel)
#     
#     # Save to database
#     db.commit()
#     
#     # Refresh to get auto-generated ID
#     db.refresh(new_hotel)
#     
#     return new_hotel
#     # Session automatically closed by get_db()
#
# @router.get("/hotels")
# def list_hotels(db: Session = Depends(get_db)):
#     # Query all hotels
#     hotels = db.query(Hotel).all()
#     return hotels
#     # Session automatically closed by get_db()
#
# =============================================================================
