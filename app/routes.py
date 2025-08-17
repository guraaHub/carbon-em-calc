# =============================================================================
# ROUTES.PY - UTILITY BILL AND TRIP MANAGEMENT ENDPOINTS
# =============================================================================
# This module handles all API endpoints including:
# - Utility bill uploads and management (for hotels)
# - Trip creation and carbon footprint calculation (for travel agents)
# - Carbon emission calculations for both hotels and trips
# - AWS S3 file storage integration
# 
# Key Features:
# - Secure file uploads to AWS S3
# - JWT-based authentication for hotels and travel agents
# - Input validation for bill and trip data
# - Comprehensive carbon footprint calculations
# - Database storage of bills and trip metadata
# =============================================================================

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from . import database, models, schemas
from .auth import get_current_hotel, get_current_travel_agent  # Import authentication dependencies
import boto3  # Amazon Web Services SDK for S3 uploads
import os
from datetime import datetime
from typing import List

# Create FastAPI router for bill-related endpoints
# All routes in this module will be prefixed with "/bills"
router = APIRouter(prefix="/bills", tags=["Bills"])

# =============================================================================
# AWS S3 CONFIGURATION
# =============================================================================
# S3 (Simple Storage Service) is used to store the actual bill files
# The database only stores metadata and URLs pointing to S3 files

# Get S3 configuration from environment variables
S3_BUCKET = os.getenv("S3_BUCKET", "your-s3-bucket-name")

# Create S3 client with credentials
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "ap-south-1")
)

# =============================================================================
# BILL UPLOAD ENDPOINT
# =============================================================================

@router.post("/upload", response_model=schemas.BillUploadResponse)
async def upload_bill(
    bill_type: str = Form(...),        # electricity, water, etc.
    bill_month: int = Form(...),       # 1-12
    bill_year: int = Form(...),        # 2023, 2024...
    bill_amount: str = Form(...),      # Consumption amount from the bill
    unit: str = Form(...),             # Unit of measurement (kWh, liters, etc.)
    file: UploadFile = File(...),      # The actual bill file (PDF, image, etc.)
    current_hotel: dict = Depends(get_current_hotel),  # Authenticated hotel info
    db: Session = Depends(database.get_db),            # Database session
):
    """
    Upload Utility Bill Endpoint
    
    Purpose: Allows authenticated hotels to upload their utility bills with consumption data.
    The system stores the file in AWS S3, saves metadata in the database, and captures
    the exact consumption amounts needed for carbon footprint calculations.
    
    How it works:
    1. Validates JWT token to identify the hotel
    2. Validates input data (bill type, month, year, amount, unit)
    3. Generates unique filename with hotel identification
    4. Uploads file to AWS S3
    5. Saves bill metadata AND consumption data to database
    6. Returns confirmation with file URL and consumption details
    
    Security:
    - Requires valid JWT token (hotel must be logged in)
    - Files are named with hotel ID to prevent conflicts
    - Only authenticated hotel can upload bills for themselves
    
    Args:
        bill_type (str): Type of utility bill ("electricity" or "water")
        bill_month (int): Month the bill is for (1-12)
        bill_year (int): Year the bill is for
        bill_amount (str): Exact consumption amount from the bill (e.g., "1450.75")
        unit (str): Unit of measurement (e.g., "kWh", "liters", "gallons")
        file (UploadFile): The bill file to upload
        current_hotel (dict): Hotel info from JWT token (auto-injected)
        db (Session): Database session (auto-injected)
    
    Returns:
        BillUploadResponse: Contains bill ID, metadata, consumption data, and file URL
    
    Raises:
        HTTPException: 400 for invalid data, 401 for authentication errors, 500 for upload errors
    
    Request Example (multipart/form-data):
        POST /bills/upload
        Headers: Authorization: Bearer <jwt_token>
        Form Data:
            bill_type: "electricity"
            bill_month: 3
            bill_year: 2024
            bill_amount: "1450.75"
            unit: "kWh"
            file: <bill_file.pdf>
    
    Response Example:
        {
            "id": 123,
            "bill_type": "electricity",
            "bill_month": 3,
            "bill_year": 2024,
            "bill_amount": "1450.75",
            "unit": "kWh",
            "file_url": "https://bucket.s3.amazonaws.com/456_electricity_2024_3_1234567890_bill.pdf",
            "message": "Bill uploaded successfully"
        }
    """
    try:
        # =============================================================================
        # INPUT VALIDATION
        # =============================================================================
        
        # Validate bill type - only electricity and water are currently supported
        if bill_type not in ["electricity", "water"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid bill type. Must be 'electricity' or 'water'"
            )
        
        # Validate month - must be 1-12 (January-December)
        if not (1 <= bill_month <= 12):
            raise HTTPException(
                status_code=400, 
                detail="Invalid month. Must be between 1 and 12"
            )
        
        # Validate year - reasonable range to prevent errors
        current_year = datetime.now().year
        if bill_year < 2020 or bill_year > current_year + 1:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid year. Must be between 2020 and {current_year + 1}"
            )

        # Validate bill amount - must be a valid number
        try:
            float_amount = float(bill_amount)
            if float_amount < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Bill amount must be a positive number"
                )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Bill amount must be a valid number (e.g., '450' or '1250.75')"
            )

        # Validate unit - must be appropriate for the bill type
        valid_units = {
            "electricity": ["kWh", "kw", "kwh", "kilowatt-hours", "units"],
            "water": ["liters", "litres", "gallons", "cubic meters", "m3", "l", "gal"]
        }
        
        if unit.lower() not in [u.lower() for u in valid_units.get(bill_type, [])]:
            valid_units_str = ", ".join(valid_units.get(bill_type, []))
            raise HTTPException(
                status_code=400,
                detail=f"Invalid unit for {bill_type}. Valid units: {valid_units_str}"
            )

        # =============================================================================
        # HOTEL IDENTIFICATION
        # =============================================================================
        
        # Extract hotel information from validated JWT token
        # This ensures the bill is associated with the correct hotel
        hotel_id = current_hotel["hotel_id"]
        hotel_name = current_hotel["hotel_name"]

        # =============================================================================
        # FILE UPLOAD TO S3
        # =============================================================================
        
        # Generate unique filename with hotel identification
        # Format: {hotel_id}_{bill_type}_{year}_{month}_{timestamp}_{original_filename}
        # Example: 456_electricity_2024_3_1710234567.89_march_bill.pdf
        timestamp = datetime.now().timestamp()
        filename = f"{hotel_id}_{bill_type}_{bill_year}_{bill_month}_{timestamp}_{file.filename}"

        # Upload file to AWS S3 bucket
        # file.file is the actual file content as a file-like object
        s3.upload_fileobj(file.file, S3_BUCKET, filename)

        # Generate the public URL for the uploaded file
        file_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{filename}"

        # =============================================================================
        # DATABASE STORAGE
        # =============================================================================
        
        # Create new UtilityBill record with all metadata AND consumption data
        db_bill = models.UtilityBill(
            hotel_id=hotel_id,          # Link to hotel that uploaded
            hotel_name=hotel_name,      # Hotel name for convenience
            bill_type=bill_type,        # electricity, water, etc.
            bill_month=bill_month,      # 1-12
            bill_year=bill_year,        # 2023, 2024, etc.
            bill_amount=bill_amount,    # ⚡ Consumption amount for carbon calculations
            unit=unit,                  # 📊 Unit of measurement
            file_url=file_url           # S3 URL where file is stored
            # uploaded_at is automatically set by SQLAlchemy
        )
        
        # Save to database
        db.add(db_bill)         # Stage for insertion
        db.commit()             # Save to database
        db.refresh(db_bill)     # Refresh to get auto-generated ID

        # =============================================================================
        # SUCCESS RESPONSE
        # =============================================================================
        
        # Return success response with bill information including consumption data
        return schemas.BillUploadResponse(
            id=db_bill.id,
            bill_type=db_bill.bill_type,
            bill_month=db_bill.bill_month,
            bill_year=db_bill.bill_year,
            bill_amount=db_bill.bill_amount,    # ⚡ Consumption amount
            unit=db_bill.unit,                  # 📊 Unit of measurement
            file_url=db_bill.file_url,
            message="Bill uploaded successfully"
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        # Catch any other errors (S3 upload failures, database errors, etc.)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# =============================================================================
# BILL RETRIEVAL ENDPOINT
# =============================================================================

@router.get("/my-bills")
async def get_my_bills(
    current_hotel: dict = Depends(get_current_hotel),  # Authenticated hotel info
    db: Session = Depends(database.get_db)             # Database session
):
    """
    Get Hotel's Bills Endpoint
    
    Purpose: Retrieves all utility bills uploaded by the authenticated hotel.
    Hotels can only see their own bills, not bills from other hotels.
    
    How it works:
    1. Validates JWT token to identify the hotel
    2. Queries database for all bills belonging to this hotel
    3. Returns list of bills with metadata
    
    Security:
    - Requires valid JWT token (hotel must be logged in)
    - Only returns bills belonging to the authenticated hotel
    - Other hotels' bills are not accessible
    
    Args:
        current_hotel (dict): Hotel info from JWT token (auto-injected)
        db (Session): Database session (auto-injected)
    
    Returns:
        dict: Contains list of bills with all metadata
    
    Request Example:
        GET /bills/my-bills
        Headers: Authorization: Bearer <jwt_token>
    
    Response Example:
        {
            "bills": [
                {
                    "id": 123,
                    "bill_type": "electricity",
                    "bill_month": 3,
                    "bill_year": 2024,
                    "bill_amount": "1450.75",
                    "unit": "kWh",
                    "hotel_id": 456,
                    "hotel_name": "Grand Resort Hotel",
                    "file_url": "https://bucket.s3.amazonaws.com/file.pdf",
                    "uploaded_at": "2024-03-15T10:30:00"
                },
                {
                    "id": 124,
                    "bill_type": "water",
                    "bill_month": 3,
                    "bill_year": 2024,
                    "bill_amount": "2500",
                    "unit": "liters",
                    "hotel_id": 456,
                    "hotel_name": "Grand Resort Hotel",
                    "file_url": "https://bucket.s3.amazonaws.com/file2.pdf",
                    "uploaded_at": "2024-03-16T11:45:00"
                }
            ]
        }
    """
    # Extract hotel ID from authenticated user
    hotel_id = current_hotel["hotel_id"]
    
    # Query database for all bills belonging to this hotel
    # Filter ensures hotel only sees their own bills
    bills = db.query(models.UtilityBill).filter(
        models.UtilityBill.hotel_id == hotel_id
    ).all()
    
    # Return bills list
    # SQLAlchemy objects are automatically converted to JSON by FastAPI
    return {"bills": bills}

# =============================================================================
# CARBON FOOTPRINT CALCULATION ENDPOINT
# =============================================================================

@router.get("/carbon-footprint")
async def calculate_carbon_footprint(
    year: int = None,  # Optional: Calculate for specific year
    current_hotel: dict = Depends(get_current_hotel),
    db: Session = Depends(database.get_db)
):
    """
    Calculate Carbon Footprint Endpoint
    
    Purpose: Calculates the hotel's carbon footprint based on utility consumption data.
    Uses the bill amounts and standard carbon emission factors to estimate CO2 emissions.
    
    How it works:
    1. Validates JWT token to identify the hotel
    2. Retrieves all bills for the hotel (optionally filtered by year)
    3. Applies carbon emission factors to consumption amounts
    4. Calculates total CO2 emissions
    5. Returns detailed breakdown by utility type and month
    
    Carbon Emission Factors (approximate):
    - Electricity: 0.5 kg CO2 per kWh (varies by region/grid)
    - Water: 0.001 kg CO2 per liter (includes treatment and distribution)
    
    Args:
        year (int, optional): Calculate for specific year only
        current_hotel (dict): Hotel info from JWT token (auto-injected)
        db (Session): Database session (auto-injected)
    
    Returns:
        dict: Carbon footprint calculation with breakdown
    
    Request Example:
        GET /bills/carbon-footprint?year=2024
        Headers: Authorization: Bearer <jwt_token>
    
    Response Example:
        {
            "hotel_name": "Grand Resort Hotel",
            "calculation_year": 2024,
            "total_co2_kg": 725.375,
            "breakdown": {
                "electricity": {
                    "total_consumption": "1450.75 kWh",
                    "co2_emissions_kg": 725.375,
                    "factor_used": "0.5 kg CO2 per kWh"
                },
                "water": {
                    "total_consumption": "0 liters",
                    "co2_emissions_kg": 0,
                    "factor_used": "0.001 kg CO2 per liter"
                }
            },
            "monthly_breakdown": [
                {
                    "month": 3,
                    "electricity_kwh": "1450.75",
                    "water_liters": "0",
                    "total_co2_kg": 725.375
                }
            ]
        }
    """
    # Extract hotel ID from authenticated user
    hotel_id = current_hotel["hotel_id"]
    hotel_name = current_hotel["hotel_name"]
    
    # Build query for hotel's bills
    query = db.query(models.UtilityBill).filter(models.UtilityBill.hotel_id == hotel_id)
    
    # Filter by year if specified
    if year:
        query = query.filter(models.UtilityBill.bill_year == year)
    
    bills = query.all()
    
    # Carbon emission factors (kg CO2 per unit)
    emission_factors = {
        "electricity": 0.5,    # kg CO2 per kWh (varies by region)
        "water": 0.001         # kg CO2 per liter (includes treatment)
    }
    
    # Initialize calculations
    total_co2 = 0.0
    breakdown = {
        "electricity": {"total_consumption": 0.0, "co2_emissions_kg": 0.0, "unit": "kWh"},
        "water": {"total_consumption": 0.0, "co2_emissions_kg": 0.0, "unit": "liters"}
    }
    monthly_data = {}
    
    # Process each bill
    for bill in bills:
        try:
            # Convert amount to float for calculations
            amount = float(bill.bill_amount)
            bill_type = bill.bill_type.lower()
            
            # Get emission factor
            factor = emission_factors.get(bill_type, 0)
            
            # Calculate CO2 emissions for this bill
            co2_emissions = amount * factor
            total_co2 += co2_emissions
            
            # Add to breakdown
            if bill_type in breakdown:
                breakdown[bill_type]["total_consumption"] += amount
                breakdown[bill_type]["co2_emissions_kg"] += co2_emissions
            
            # Add to monthly breakdown
            month_key = f"{bill.bill_year}-{bill.bill_month:02d}"
            if month_key not in monthly_data:
                monthly_data[month_key] = {"month": bill.bill_month, "year": bill.bill_year, "electricity_kwh": 0, "water_liters": 0, "total_co2_kg": 0}
            
            if bill_type == "electricity":
                monthly_data[month_key]["electricity_kwh"] += amount
            elif bill_type == "water":
                monthly_data[month_key]["water_liters"] += amount
                
            monthly_data[month_key]["total_co2_kg"] += co2_emissions
            
        except (ValueError, TypeError):
            # Skip bills with invalid amounts
            continue
    
    # Format breakdown with units and factors
    for bill_type in breakdown:
        unit = breakdown[bill_type]["unit"]
        consumption = breakdown[bill_type]["total_consumption"]
        breakdown[bill_type]["total_consumption"] = f"{consumption} {unit}"
        breakdown[bill_type]["factor_used"] = f"{emission_factors.get(bill_type, 0)} kg CO2 per {unit}"
    
    return {
        "hotel_name": hotel_name,
        "calculation_year": year or "all years",
        "total_co2_kg": round(total_co2, 3),
        "breakdown": breakdown,
        "monthly_breakdown": list(monthly_data.values()),
        "note": "Emission factors are approximate and may vary by region. For precise calculations, consult local grid emission factors."
    }

# =============================================================================
# TRAVEL AGENT ENDPOINTS - TRIP MANAGEMENT
# =============================================================================

# Create separate router for trip-related endpoints
trip_router = APIRouter(prefix="/trips", tags=["Trips"])

@trip_router.post("/create", response_model=schemas.TripCarbonResponse)
def create_trip(
    trip: schemas.TripCreate,
    current_agent: models.TravelAgent = Depends(get_current_travel_agent),
    db: Session = Depends(database.get_db)
):
    """
    Create a new trip and calculate its carbon footprint.
    
    Purpose: Travel agents can create comprehensive trip records that include
    flights, local transportation, and hotel stays. The system automatically
    calculates the total carbon footprint for the entire trip.
    
    Process:
    1. Create trip record in database
    2. Create flight segment records
    3. Create local transport records  
    4. Create hotel stay records
    5. Calculate carbon footprint for each component
    6. Return detailed carbon breakdown
    
    Args:
        trip: Complete trip data including all components
        current_agent: Authenticated travel agent (from JWT token)
        db: Database session
    
    Returns:
        schemas.TripCarbonResponse: Trip details with carbon footprint breakdown
    
    Example Request:
        POST /trips/create
        {
            "trip_name": "European Adventure Tour",
            "number_of_tourists": 15,
            "start_date": "2024-07-01T00:00:00",
            "end_date": "2024-07-15T00:00:00",
            "flight_segments": [
                {
                    "departure_airport": "JFK",
                    "arrival_airport": "LHR"
                }
            ],
            "local_transports": [
                {
                    "vehicle_type": "bus",
                    "distance_km": 250.5
                }
            ],
            "hotel_stays": [
                {
                    "hotel_id": 1,
                    "number_of_nights": 3,
                    "check_in_date": "2024-07-01T15:00:00",
                    "check_out_date": "2024-07-04T11:00:00"
                }
            ]
        }
    """
    
    # Create main trip record
    db_trip = models.Trip(
        trip_name=trip.trip_name,
        trip_description=trip.trip_description,
        number_of_tourists=trip.number_of_tourists,
        start_date=trip.start_date,
        end_date=trip.end_date,
        travel_agent_id=current_agent.id
    )
    
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    
    # Initialize carbon tracking variables
    total_flights_carbon = 0.0
    total_transport_carbon = 0.0
    total_hotels_carbon = 0.0
    
    flight_details = []
    transport_details = []
    hotel_details = []
    
    # Process flight segments
    for flight_data in trip.flight_segments:
        db_flight = models.FlightSegment(
            trip_id=db_trip.id,
            departure_airport=flight_data.departure_airport,
            arrival_airport=flight_data.arrival_airport,
            transit_airports=flight_data.transit_airports
        )
        db.add(db_flight)
        
        # Calculate flight carbon footprint
        flight_carbon = calculate_flight_carbon(
            flight_data.departure_airport,
            flight_data.arrival_airport,
            trip.number_of_tourists
        )
        total_flights_carbon += flight_carbon
        
        flight_details.append({
            "route": f"{flight_data.departure_airport} → {flight_data.arrival_airport}",
            "carbon_kg": flight_carbon,
            "passengers": trip.number_of_tourists
        })
    
    # Process local transportation
    for transport_data in trip.local_transports:
        db_transport = models.LocalTransport(
            trip_id=db_trip.id,
            vehicle_type=transport_data.vehicle_type,
            distance_km=transport_data.distance_km
        )
        db.add(db_transport)
        
        # Calculate transport carbon footprint
        transport_carbon = calculate_transport_carbon(
            transport_data.vehicle_type,
            transport_data.distance_km,
            trip.number_of_tourists
        )
        total_transport_carbon += transport_carbon
        
        transport_details.append({
            "vehicle_type": transport_data.vehicle_type,
            "distance_km": transport_data.distance_km,
            "carbon_kg": transport_carbon,
            "passengers": trip.number_of_tourists
        })
    
    # Process hotel stays
    for hotel_data in trip.hotel_stays:
        db_hotel_stay = models.HotelStay(
            trip_id=db_trip.id,
            hotel_id=hotel_data.hotel_id,
            number_of_nights=hotel_data.number_of_nights,
            check_in_date=hotel_data.check_in_date,
            check_out_date=hotel_data.check_out_date
        )
        db.add(db_hotel_stay)
        
        # Calculate hotel carbon footprint based on hotel's average consumption
        hotel_carbon = calculate_hotel_stay_carbon(
            hotel_data.hotel_id,
            hotel_data.number_of_nights,
            trip.number_of_tourists,
            db
        )
        total_hotels_carbon += hotel_carbon
        
        # Get hotel name for details
        hotel_record = db.query(models.Hotel).filter(models.Hotel.id == hotel_data.hotel_id).first()
        hotel_name = hotel_record.name if hotel_record else "Unknown Hotel"
        
        hotel_details.append({
            "hotel_name": hotel_name,
            "nights": hotel_data.number_of_nights,
            "carbon_kg": hotel_carbon,
            "guests": trip.number_of_tourists
        })
    
    # Commit all trip components
    db.commit()
    
    # Calculate totals
    total_carbon = total_flights_carbon + total_transport_carbon + total_hotels_carbon
    carbon_per_tourist = total_carbon / trip.number_of_tourists if trip.number_of_tourists > 0 else 0
    
    return schemas.TripCarbonResponse(
        trip_id=db_trip.id,
        trip_name=db_trip.trip_name,
        number_of_tourists=trip.number_of_tourists,
        total_carbon_kg=round(total_carbon, 3),
        carbon_per_tourist_kg=round(carbon_per_tourist, 3),
        flights_carbon_kg=round(total_flights_carbon, 3),
        transport_carbon_kg=round(total_transport_carbon, 3),
        hotels_carbon_kg=round(total_hotels_carbon, 3),
        flight_details=flight_details,
        transport_details=transport_details,
        hotel_details=hotel_details
    )

@trip_router.get("/my-trips")
def get_my_trips(
    current_agent: models.TravelAgent = Depends(get_current_travel_agent),
    db: Session = Depends(database.get_db)
):
    """
    Get all trips created by the current travel agent.
    
    Purpose: Travel agents can view all trips they have created,
    with basic information and carbon footprint summaries.
    
    Returns:
        List of trips with carbon footprint information
    """
    trips = db.query(models.Trip).filter(models.Trip.travel_agent_id == current_agent.id).all()
    
    trip_summaries = []
    for trip in trips:
        # Calculate total carbon for this trip
        total_carbon = calculate_trip_total_carbon(trip.id, db)
        carbon_per_tourist = total_carbon / trip.number_of_tourists if trip.number_of_tourists > 0 else 0
        
        trip_summaries.append({
            "trip_id": trip.id,
            "trip_name": trip.trip_name,
            "number_of_tourists": trip.number_of_tourists,
            "start_date": trip.start_date,
            "end_date": trip.end_date,
            "total_carbon_kg": round(total_carbon, 3),
            "carbon_per_tourist_kg": round(carbon_per_tourist, 3),
            "created_at": trip.created_at
        })
    
    return {
        "agent_name": current_agent.name,
        "total_trips": len(trip_summaries),
        "trips": trip_summaries
    }

@trip_router.get("/{trip_id}/carbon")
def get_trip_carbon_details(
    trip_id: int,
    current_agent: models.TravelAgent = Depends(get_current_travel_agent),
    db: Session = Depends(database.get_db)
):
    """
    Get detailed carbon footprint breakdown for a specific trip.
    
    Purpose: Provides comprehensive carbon analysis for a trip,
    including breakdown by flights, transport, and hotels.
    """
    # Verify trip belongs to current agent
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.travel_agent_id == current_agent.id
    ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Get detailed carbon breakdown (reuse logic from create_trip)
    total_carbon = calculate_trip_total_carbon(trip_id, db)
    carbon_breakdown = get_trip_carbon_breakdown(trip_id, db)
    
    return {
        "trip_id": trip.id,
        "trip_name": trip.trip_name,
        "number_of_tourists": trip.number_of_tourists,
        "total_carbon_kg": round(total_carbon, 3),
        "carbon_per_tourist_kg": round(total_carbon / trip.number_of_tourists, 3),
        **carbon_breakdown
    }

# =============================================================================
# CARBON CALCULATION HELPER FUNCTIONS FOR TRIPS
# =============================================================================

def calculate_flight_carbon(departure: str, arrival: str, passengers: int) -> float:
    """
    Calculate carbon emissions for a flight segment.
    
    Uses simplified distance-based calculation.
    In production, you would use actual flight emission APIs.
    """
    # Simplified airport distance mapping (in km)
    airport_distances = {
        ("JFK", "LHR"): 5550,  # New York to London
        ("LHR", "CDG"): 350,   # London to Paris
        ("CDG", "FCO"): 1110,  # Paris to Rome
        ("FCO", "ATH"): 1050,  # Rome to Athens
        # Add more routes as needed
    }
    
    # Try to find distance in both directions
    distance = airport_distances.get((departure, arrival)) or airport_distances.get((arrival, departure))
    
    if not distance:
        # Default estimation: 500km for unknown routes
        distance = 500
    
    # Aviation emission factor: approximately 0.255 kg CO2 per passenger-km
    emission_factor = 0.255
    
    return distance * emission_factor * passengers

def calculate_transport_carbon(vehicle_type: str, distance_km: float, passengers: int) -> float:
    """
    Calculate carbon emissions for local transportation.
    """
    # Emission factors (kg CO2 per passenger-km)
    transport_factors = {
        "bus": 0.089,
        "car": 0.171,
        "train": 0.041,
        "taxi": 0.171,
        "metro": 0.033
    }
    
    factor = transport_factors.get(vehicle_type.lower(), 0.171)  # Default to car
    return distance_km * factor * passengers

def calculate_hotel_stay_carbon(hotel_id: int, nights: int, guests: int, db: Session) -> float:
    """
    Calculate carbon emissions for hotel stays based on hotel's average consumption.
    """
    # Get hotel's average daily consumption from their bills
    hotel_bills = db.query(models.UtilityBill).filter(models.UtilityBill.hotel_id == hotel_id).all()
    
    if not hotel_bills:
        # Default hotel emission: 30 kg CO2 per room-night
        return 30.0 * nights * (guests / 2)  # Assume 2 guests per room
    
    # Calculate average daily consumption from hotel's bills
    total_emissions = 0.0
    total_days = 0
    
    emission_factors = {
        "electricity": 0.708,
        "gas": 2.204,
        "water": 0.298,
        "diesel": 2.687
    }
    
    for bill in hotel_bills:
        if bill.consumption_amount and bill.consumption_amount > 0:
            bill_emissions = bill.consumption_amount * emission_factors.get(bill.bill_type, 0.5)
            
            # Estimate days covered by this bill (assume monthly bills)
            days_in_bill = 30
            daily_emissions = bill_emissions / days_in_bill
            
            total_emissions += daily_emissions
            total_days += 1
    
    if total_days > 0:
        average_daily_emissions = total_emissions / total_days
        return average_daily_emissions * nights * (guests / 2)  # Per room calculation
    else:
        # Fallback to default
        return 30.0 * nights * (guests / 2)

def calculate_trip_total_carbon(trip_id: int, db: Session) -> float:
    """Calculate total carbon footprint for a trip."""
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        return 0.0
    
    total_carbon = 0.0
    
    # Add flight emissions
    flights = db.query(models.FlightSegment).filter(models.FlightSegment.trip_id == trip_id).all()
    for flight in flights:
        total_carbon += calculate_flight_carbon(
            flight.departure_airport,
            flight.arrival_airport,
            trip.number_of_tourists
        )
    
    # Add transport emissions
    transports = db.query(models.LocalTransport).filter(models.LocalTransport.trip_id == trip_id).all()
    for transport in transports:
        total_carbon += calculate_transport_carbon(
            transport.vehicle_type,
            transport.distance_km,
            trip.number_of_tourists
        )
    
    # Add hotel emissions
    hotel_stays = db.query(models.HotelStay).filter(models.HotelStay.trip_id == trip_id).all()
    for stay in hotel_stays:
        total_carbon += calculate_hotel_stay_carbon(
            stay.hotel_id,
            stay.number_of_nights,
            trip.number_of_tourists,
            db
        )
    
    return total_carbon

def get_trip_carbon_breakdown(trip_id: int, db: Session) -> dict:
    """Get detailed carbon breakdown for a trip."""
    # Implementation would provide detailed breakdown by component
    # Similar to the logic in create_trip but for existing trips
    return {
        "flights_breakdown": [],
        "transport_breakdown": [],
        "hotels_breakdown": []
    }

# =============================================================================
# POTENTIAL FUTURE ENDPOINTS
# =============================================================================
#
# You could add additional endpoints like:
#
# @router.get("/bills/{bill_id}")
# def get_bill_details(bill_id: int, current_hotel: dict = Depends(get_current_hotel)):
#     """Get details of a specific bill"""
#
# @router.delete("/bills/{bill_id}")
# def delete_bill(bill_id: int, current_hotel: dict = Depends(get_current_hotel)):
#     """Delete a specific bill"""
#
# @trip_router.put("/{trip_id}")
# def update_trip(trip_id: int, trip_data: schemas.TripUpdate):
#     """Update trip details"""
#
# @trip_router.delete("/{trip_id}")
# def delete_trip(trip_id: int):
#     """Delete a trip"""
#
# =============================================================================
