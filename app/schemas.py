# =============================================================================
# SCHEMAS.PY - DATA VALIDATION AND SERIALIZATION
# =============================================================================
# This module defines Pydantic schemas for data validation and serialization.
# 
# What are schemas?
# - Schemas define the structure and validation rules for data
# - They ensure incoming data meets requirements before processing
# - They control what data is returned in API responses
# - They provide automatic API documentation
# 
# Pydantic vs SQLAlchemy Models:
# - SQLAlchemy Models: Define database structure (tables, columns, relationships)
# - Pydantic Schemas: Define API data structure (request/response format, validation)
# 
# Data Flow:
# 1. Client sends JSON → Pydantic Schema validates → Python object
# 2. Python object → SQLAlchemy Model → Database
# 3. Database → SQLAlchemy Model → Pydantic Schema → JSON response
# 
# Schema Categories:
# - Hotel schemas: Registration, bill uploads, carbon calculations
# - Travel Agent schemas: Registration, trip management, carbon calculations
# =============================================================================

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# =============================================================================
# HOTEL-RELATED SCHEMAS
# =============================================================================

class HotelCreate(BaseModel):
    """
    Schema for hotel registration requests.
    
    Purpose: Validates data when a new hotel wants to create an account.
    Ensures all required fields are present and properly formatted.
    
    Used by: POST /auth/register endpoint
    
    Validation Rules:
    - name: Required, must be a string
    - email: Required, must be a valid email format  
    - password: Required, must be a string
    
    Request Body Example:
        {
            "name": "Grand Resort Hotel",
            "email": "admin@grandresort.com",
            "password": "securepassword123"
        }
    """
    name: str = Field(..., min_length=1, max_length=255, description="Hotel name")
    email: str = Field(..., description="Hotel email address for login")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")

class HotelLogin(BaseModel):
    """
    Schema for hotel login requests.
    
    Purpose: Validates login credentials submitted by hotels.
    
    Used by: POST /auth/login endpoint
    
    Validation Rules:
    - email: Required, must be a valid email format
    - password: Required, must be a string
    
    Request Body Example:
        {
            "email": "admin@grandresort.com",
            "password": "securepassword123"
        }
    """
    email: str = Field(..., description="Hotel email address")
    password: str = Field(..., description="Hotel password")

# =============================================================================
# TRAVEL AGENT-RELATED SCHEMAS
# =============================================================================

class TravelAgentCreate(BaseModel):
    """
    Schema for travel agent registration requests.
    
    Purpose: Validates data when a new travel agent wants to create an account.
    
    Used by: POST /auth/register-agent endpoint
    """
    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    email: str = Field(..., description="Agent email address for login")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    company: Optional[str] = Field(None, max_length=255, description="Company/agency name")

class TravelAgentLogin(BaseModel):
    """
    Schema for travel agent login requests.
    
    Purpose: Validates login credentials submitted by travel agents.
    
    Used by: POST /auth/login-agent endpoint
    """
    email: str = Field(..., description="Agent email address")
    password: str = Field(..., description="Agent password")

# =============================================================================
# TRIP-RELATED SCHEMAS
# =============================================================================

class FlightSegmentCreate(BaseModel):
    """Schema for creating flight segments within a trip"""
    departure_airport: str = Field(..., min_length=3, max_length=10, description="Departure airport code")
    arrival_airport: str = Field(..., min_length=3, max_length=10, description="Arrival airport code")
    transit_airports: Optional[str] = Field(None, description="Comma-separated transit airport codes")

class LocalTransportCreate(BaseModel):
    """Schema for creating local transport records within a trip"""
    vehicle_type: str = Field(..., description="Vehicle type (bus, car, train, taxi)")
    distance_km: float = Field(..., gt=0, description="Distance traveled in kilometers")

class HotelStayCreate(BaseModel):
    """Schema for creating hotel stay records within a trip"""
    hotel_id: int = Field(..., description="ID of the hotel where tourists stayed")
    number_of_nights: int = Field(..., gt=0, description="Number of nights stayed")
    check_in_date: datetime = Field(..., description="Check-in date")
    check_out_date: datetime = Field(..., description="Check-out date")

class TripCreate(BaseModel):
    """
    Schema for creating new trips.
    
    Purpose: Validates comprehensive trip data submitted by travel agents.
    Includes all flight, transport, and hotel information.
    
    Used by: POST /trips/create endpoint
    """
    trip_name: str = Field(..., min_length=1, max_length=255, description="Trip name")
    trip_description: Optional[str] = Field(None, description="Trip description")
    number_of_tourists: int = Field(..., gt=0, description="Number of tourists")
    start_date: datetime = Field(..., description="Trip start date")
    end_date: datetime = Field(..., description="Trip end date")
    
    # Trip components
    flight_segments: List[FlightSegmentCreate] = Field(default=[], description="Flight segments")
    local_transports: List[LocalTransportCreate] = Field(default=[], description="Local transportation")
    hotel_stays: List[HotelStayCreate] = Field(default=[], description="Hotel accommodations")

class TripCarbonResponse(BaseModel):
    """
    Schema for trip carbon footprint calculation responses.
    
    Purpose: Returns detailed carbon footprint breakdown for a complete trip.
    
    Used by: POST /trips/create and GET /trips/{trip_id}/carbon endpoints
    """
    trip_id: int = Field(..., description="Unique trip identifier")
    trip_name: str = Field(..., description="Trip name")
    number_of_tourists: int = Field(..., description="Number of tourists")
    
    # Carbon breakdown
    total_carbon_kg: float = Field(..., description="Total trip carbon footprint in kg CO2")
    carbon_per_tourist_kg: float = Field(..., description="Carbon footprint per tourist in kg CO2")
    
    # Detailed breakdown
    flights_carbon_kg: float = Field(..., description="Total carbon from flights")
    transport_carbon_kg: float = Field(..., description="Total carbon from local transport")
    hotels_carbon_kg: float = Field(..., description="Total carbon from hotel stays")
    
    # Component details
    flight_details: List[dict] = Field(default=[], description="Flight carbon breakdown")
    transport_details: List[dict] = Field(default=[], description="Transport carbon breakdown")
    hotel_details: List[dict] = Field(default=[], description="Hotel carbon breakdown")

class BillUploadResponse(BaseModel):
    """
    Schema for bill upload success responses.
    
    Purpose: Defines what data is returned immediately after a successful
    bill upload. Provides confirmation and essential information.
    
    Used by: POST /bills/upload endpoint response
    
    Response Example:
        {
            "id": 123,
            "bill_type": "electricity",
            "bill_month": 3,
            "bill_year": 2024,
            "file_url": "https://bucket.s3.amazonaws.com/bill.pdf",
            "message": "Bill uploaded successfully"
        }
    """
    id: int = Field(..., description="Unique identifier of uploaded bill")
    bill_type: str = Field(..., description="Type of bill uploaded")
    bill_month: int = Field(..., description="Month of uploaded bill")
    bill_year: int = Field(..., description="Year of uploaded bill")
    file_url: str = Field(..., description="URL where uploaded file is stored")
    message: str = Field(..., description="Success message")

# =============================================================================
# UTILITY BILL-RELATED SCHEMAS
# =============================================================================

class UtilityBillBase(BaseModel):
    """
    Base schema containing common utility bill fields.
    
    Purpose: Defines common fields that are shared across different
    utility bill schemas. Other schemas inherit from this.
    
    Why use inheritance?
    - Reduces code duplication
    - Ensures consistency across related schemas
    - Makes maintenance easier
    """
    bill_type: str = Field(..., description="Type of bill (electricity, water, etc.)")
    bill_month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    bill_year: int = Field(..., ge=2020, le=2030, description="Year")
    bill_amount: str = Field(..., description="Consumption amount from the bill (e.g., '450', '1250.5')")
    unit: str = Field(..., description="Unit of measurement (e.g., 'kWh', 'liters', 'gallons')")

class UtilityBillCreate(UtilityBillBase):
    """
    Schema for creating new utility bills.
    
    Purpose: Validates data when hotels upload new utility bills.
    Inherits common fields from UtilityBillBase and adds amount/unit validation.
    
    Used by: POST /bills/upload endpoint (along with file upload)
    
    Note: This schema is used for form data validation.
    The actual file is handled separately by FastAPI's UploadFile.
    
    Important Fields for Carbon Calculation:
    - bill_amount: The exact consumption amount from the bill
    - unit: The measurement unit (kWh for electricity, liters for water, etc.)
    
    Example:
        bill_type: "electricity"
        bill_month: 3
        bill_year: 2024
        bill_amount: "1450.75"  # 1,450.75 kWh consumed
        unit: "kWh"
    """
    pass  # Inherits all fields from UtilityBillBase

class UtilityBill(UtilityBillBase):
    """
    Schema for utility bill responses.
    
    Purpose: Defines what data is returned when querying utility bills.
    Includes all fields that should be visible to API clients.
    
    Used by: GET endpoints that return bill information
    
    Additional fields beyond UtilityBillBase:
    - id: Database primary key
    - hotel_id: Which hotel owns this bill
    - hotel_name: Name of the hotel (for convenience)
    - file_url: Where the bill file is stored
    - uploaded_at: When the bill was uploaded
    
    Response Example:
        {
            "id": 123,
            "bill_type": "electricity",
            "bill_month": 3,
            "bill_year": 2024,
            "bill_amount": "1450.75",
            "unit": "kWh",
            "hotel_id": 456,
            "hotel_name": "Grand Resort Hotel",
            "file_url": "https://bucket.s3.amazonaws.com/bill.pdf",
            "uploaded_at": "2024-03-15T10:30:00"
        }
    """
    id: int = Field(..., description="Unique bill identifier")
    hotel_id: int = Field(..., description="ID of hotel that owns this bill")
    hotel_name: str = Field(..., description="Name of hotel that owns this bill")
    file_url: str = Field(..., description="URL where bill file is stored")
    uploaded_at: datetime = Field(..., description="When bill was uploaded")

    class Config:
        """
        Pydantic configuration for this schema.
        
        from_attributes=True: Allows creating Pydantic objects from SQLAlchemy models
        This enables: UtilityBill.from_orm(sqlalchemy_bill_object)
        """
        from_attributes = True

class BillUploadResponse(BaseModel):
    """
    Schema for bill upload success responses.
    
    Purpose: Defines what data is returned immediately after a successful
    bill upload. Provides confirmation and essential information including
    the consumption amount for verification.
    
    Used by: POST /bills/upload endpoint response
    
    Response Example:
        {
            "id": 123,
            "bill_type": "electricity",
            "bill_month": 3,
            "bill_year": 2024,
            "bill_amount": "1450.75",
            "unit": "kWh",
            "file_url": "https://bucket.s3.amazonaws.com/bill.pdf",
            "message": "Bill uploaded successfully"
        }
    """
    id: int = Field(..., description="Unique identifier of uploaded bill")
    bill_type: str = Field(..., description="Type of bill uploaded")
    bill_month: int = Field(..., description="Month of uploaded bill")
    bill_year: int = Field(..., description="Year of uploaded bill")
    bill_amount: str = Field(..., description="Consumption amount from the bill")
    unit: str = Field(..., description="Unit of measurement")
    file_url: str = Field(..., description="URL where uploaded file is stored")
    message: str = Field(..., description="Success message")

# =============================================================================
# SCHEMA USAGE PATTERNS
# =============================================================================
#
# 1. REQUEST VALIDATION:
#    @router.post("/register")
#    def register(hotel: HotelCreate):  # Automatically validates incoming JSON
#        # hotel.name, hotel.email, hotel.password are guaranteed to be valid
#
# 2. RESPONSE SERIALIZATION:
#    @router.get("/bills", response_model=List[UtilityBill])
#    def get_bills():
#        bills = db.query(UtilityBillModel).all()  # SQLAlchemy models
#        return bills  # Automatically converted to UtilityBill schema format
#
# 3. MANUAL CONVERSION:
#    db_bill = UtilityBillModel(...)  # SQLAlchemy model
#    response_bill = UtilityBill.from_orm(db_bill)  # Convert to Pydantic schema
#
# =============================================================================
