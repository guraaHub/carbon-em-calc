# =============================================================================
# MODELS.PY - DATABASE MODELS
# =============================================================================
# This module defines the database structure using SQLAlchemy ORM.
# 
# What are models?
# - Models represent database tables as Python classes
# - Each class = one table, each attribute = one column
# - SQLAlchemy automatically converts between Python objects and database rows
# 
# Why use ORM instead of raw SQL?
# - Type safety and auto-completion
# - Automatic relationship handling
# - Database-agnostic code (works with PostgreSQL, MySQL, SQLite, etc.)
# - Protection against SQL injection attacks
# =============================================================================

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Text
from sqlalchemy.orm import relationship
from .database import Base  # Base class for all database models
from datetime import datetime

class Hotel(Base):
    """
    Hotel Model - Represents hotel accounts in the system
    
    Purpose: Stores information about hotels that use the carbon tracking system.
    Each hotel has a unique account and can upload multiple utility bills.
    
    Database Table: 'hotels'
    
    Relationships:
    - One hotel can have many utility bills (one-to-many)
    """
    __tablename__ = "hotels"  # Actual table name in database

    # Primary key - unique identifier for each hotel
    id = Column(Integer, primary_key=True, index=True)
    
    # Hotel name (e.g., "Grand Resort Hotel")
    name = Column(String(255), nullable=False)
    
    # Email address - used for login (must be unique)
    email = Column(String(255), unique=True, nullable=False)
    
    # Encrypted password - NEVER stored as plain text
    password = Column(String(255), nullable=False)
    
    # When the hotel account was created
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship: Links to all utility bills uploaded by this hotel
    # 'back_populates' creates a two-way relationship
    bills = relationship("UtilityBill", back_populates="hotel")
    
    # When you access hotel.bills, you get a list of all UtilityBill objects
    # When you access bill.hotel, you get the Hotel object that owns the bill

class TravelAgent(Base):
    """
    Travel Agent Model - Represents travel agent accounts in the system
    
    Purpose: Stores information about travel agents who create trips and calculate
    carbon footprints for entire tours including flights, transportation, and hotels.
    
    Database Table: 'travel_agents'
    
    Relationships:
    - One travel agent can create many trips (one-to-many)
    """
    __tablename__ = "travel_agents"  # Actual table name in database

    # Primary key - unique identifier for each travel agent
    id = Column(Integer, primary_key=True, index=True)
    
    # Travel agent/company name (e.g., "Adventure Tours Inc")
    name = Column(String(255), nullable=False)
    
    # Email address - used for login (must be unique)
    email = Column(String(255), unique=True, nullable=False)
    
    # Encrypted password - NEVER stored as plain text
    password = Column(String(255), nullable=False)
    
    # Company/agency name
    company = Column(String(255), nullable=True)
    
    # When the travel agent account was created
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship: Links to all trips created by this travel agent
    trips = relationship("Trip", back_populates="travel_agent")

class Trip(Base):
    """
    Trip Model - Represents travel trips created by travel agents
    
    Purpose: Stores information about complete trips including flights, local transport,
    and hotel stays. Used to calculate total carbon footprint for the entire journey.
    
    Database Table: 'trips'
    
    Relationships:
    - Many trips belong to one travel agent (many-to-one)
    - One trip can have many flight segments (one-to-many)
    - One trip can have many local transport segments (one-to-many)
    - One trip can have many hotel stays (one-to-many)
    """
    __tablename__ = "trips"  # Actual table name in database

    # Primary key - unique identifier for each trip
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key - links to the Travel Agent who created this trip
    travel_agent_id = Column(Integer, ForeignKey("travel_agents.id"), nullable=False)
    
    # Trip identification and details
    trip_name = Column(String(255), nullable=False)  # e.g., "Europe Adventure Tour"
    trip_description = Column(Text, nullable=True)   # Detailed description
    
    # Number of tourists on this trip
    number_of_tourists = Column(Integer, nullable=False)
    
    # Trip dates
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Total carbon footprint for the trip (calculated)
    total_carbon_kg = Column(Float, default=0.0)
    
    # When this trip was created
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    travel_agent = relationship("TravelAgent", back_populates="trips")
    flight_segments = relationship("FlightSegment", back_populates="trip")
    local_transports = relationship("LocalTransport", back_populates="trip")
    hotel_stays = relationship("HotelStay", back_populates="trip")

class FlightSegment(Base):
    """
    Flight Segment Model - Represents individual flight legs in a trip
    
    Purpose: Stores flight information for carbon footprint calculations.
    Each flight segment contributes to the total trip carbon emissions.
    
    Database Table: 'flight_segments'
    """
    __tablename__ = "flight_segments"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key - links to the Trip this flight belongs to
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    
    # Airport codes (e.g., "LAX", "JFK", "LHR")
    departure_airport = Column(String(10), nullable=False)
    arrival_airport = Column(String(10), nullable=False)
    transit_airports = Column(String(255), nullable=True)  # Comma-separated transit stops
    
    # Flight details
    flight_distance_km = Column(Float, nullable=True)  # Can be calculated from airports
    
    # Carbon emissions for this flight segment (calculated)
    carbon_kg_per_passenger = Column(Float, default=0.0)
    
    # Relationship
    trip = relationship("Trip", back_populates="flight_segments")

class LocalTransport(Base):
    """
    Local Transport Model - Represents ground transportation during the trip
    
    Purpose: Stores local transportation details for carbon calculations.
    Includes buses, cars, trains, etc. used during the trip.
    
    Database Table: 'local_transports'
    """
    __tablename__ = "local_transports"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key - links to the Trip this transport belongs to
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    
    # Transportation details
    vehicle_type = Column(String(50), nullable=False)  # "bus", "car", "train", "taxi"
    distance_km = Column(Float, nullable=False)        # Distance traveled
    
    # Carbon emissions for this transport (calculated)
    carbon_kg_total = Column(Float, default=0.0)
    
    # Relationship
    trip = relationship("Trip", back_populates="local_transports")

class HotelStay(Base):
    """
    Hotel Stay Model - Represents hotel accommodations during the trip
    
    Purpose: Links trips to hotels and calculates carbon footprint based on
    hotel's utility consumption and number of nights stayed.
    
    Database Table: 'hotel_stays'
    """
    __tablename__ = "hotel_stays"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key - links to the Trip this stay belongs to
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    
    # Foreign key - links to the Hotel where tourists stayed
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    
    # Stay details
    number_of_nights = Column(Integer, nullable=False)
    check_in_date = Column(DateTime, nullable=False)
    check_out_date = Column(DateTime, nullable=False)
    
    # Carbon emissions for this hotel stay (calculated)
    carbon_kg_total = Column(Float, default=0.0)
    
    # Relationships
    trip = relationship("Trip", back_populates="hotel_stays")
    hotel = relationship("Hotel")

class UtilityBill(Base):
    """
    Utility Bill Model - Represents uploaded utility bills
    
    Purpose: Stores metadata about utility bills uploaded by hotels.
    The actual files are stored in AWS S3, but this table tracks:
    - Which hotel uploaded the bill
    - What type of bill (electricity, water, etc.)
    - Which month/year the bill is for
    - The exact amount/consumption from the bill (for carbon calculations)
    - Where the file is stored (S3 URL)
    
    Database Table: 'utility_bills'
    
    Relationships:
    - Many bills can belong to one hotel (many-to-one)
    """
    __tablename__ = "utility_bills"  # Actual table name in database

    # Primary key - unique identifier for each bill
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key - links to the Hotel that uploaded this bill
    # This creates the relationship between hotels and their bills
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    
    # Hotel name (stored for convenience/reporting)
    # Note: This is denormalized data (stored in both hotels and utility_bills tables)
    # It makes queries faster but requires careful updating if hotel name changes
    hotel_name = Column(String(255), nullable=False)
    
    # Type of utility bill: "electricity", "water", etc.
    bill_type = Column(String(50), nullable=False)
    
    # Month the bill is for (1-12 for Jan-Dec)
    bill_month = Column(Integer, nullable=False)
    
    # Year the bill is for (e.g., 2023, 2024)
    bill_year = Column(Integer, nullable=False)
    
    # ⚡ IMPORTANT: The actual consumption amount from the bill
    # For electricity: kWh (kilowatt-hours)
    # For water: liters or gallons
    # This is the key value used for carbon footprint calculations
    bill_amount = Column(String(20), nullable=False)
    
    # Unit of measurement for the bill amount
    # Examples: "kWh", "liters", "gallons", "cubic meters"
    unit = Column(String(20), nullable=False)
    
    # AWS S3 URL where the actual bill file is stored
    # Example: "https://my-bucket.s3.amazonaws.com/123_electricity_2024_3_1234567890_bill.pdf"
    file_url = Column(String(500), nullable=False)
    
    # When this bill record was uploaded to the system
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationship: Links back to the Hotel that owns this bill
    # 'back_populates' creates a two-way relationship
    hotel = relationship("Hotel", back_populates="bills")
    
    # Usage examples:
    # bill.hotel.name → Gets the name of the hotel that uploaded this bill
    # bill.hotel.email → Gets the email of the hotel that uploaded this bill

# =============================================================================
# RELATIONSHIP EXPLANATION
# =============================================================================
# 
# The system now has two main user types with their own data:
# 
# HOTELS & UTILITY BILLS (one-to-many):
# - One hotel can upload many utility bills
# - Each bill belongs to exactly one hotel
# 
# TRAVEL AGENTS & TRIPS (one-to-many):
# - One travel agent can create many trips
# - Each trip belongs to exactly one travel agent
# 
# TRIPS & RELATED DATA (one-to-many for each):
# - One trip can have many flight segments
# - One trip can have many local transport records
# - One trip can have many hotel stays
# 
# HOTEL STAYS & HOTELS (many-to-one):
# - Many hotel stays can reference the same hotel
# - Each hotel stay belongs to exactly one hotel
# 
# How it works in code:
# 
# # Get all trips for a travel agent:
# agent = db.query(TravelAgent).filter(TravelAgent.id == 123).first()
# all_trips = agent.trips  # List of Trip objects
# 
# # Get all components of a trip:
# trip = db.query(Trip).filter(Trip.id == 456).first()
# flights = trip.flight_segments      # List of FlightSegment objects
# transports = trip.local_transports  # List of LocalTransport objects
# hotels = trip.hotel_stays          # List of HotelStay objects
# 
# # Calculate total trip carbon footprint:
# total_carbon = (
#     sum(flight.carbon_kg_per_passenger * trip.number_of_tourists for flight in flights) +
#     sum(transport.carbon_kg_total for transport in transports) +
#     sum(stay.carbon_kg_total for stay in hotels)
# )
# 
# =============================================================================
