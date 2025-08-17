from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import boto3
import psycopg2
import os
import jwt
from datetime import datetime
from typing import Optional

app = FastAPI()

# 🔹 JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
security = HTTPBearer()

# 🔹 Authentication helper function
def get_current_hotel(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        hotel_id = payload.get("hotel_id")
        hotel_name = payload.get("hotel_name")
        
        if not hotel_id or not hotel_name:
            raise HTTPException(status_code=401, detail="Invalid token: missing hotel information")
            
        return {"hotel_id": hotel_id, "hotel_name": hotel_name}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# 🔹 AWS S3 setup
S3_BUCKET = "your-s3-bucket-name"
s3 = boto3.client("s3",
                  aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                  aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                  region_name="ap-south-1")   # change to your region

# 🔹 Database connection (RDS)
conn = psycopg2.connect(
    dbname="yourdbname",
    user="yourdbuser",
    password="yourdbpassword",
    host="yourdbhost",   # RDS endpoint
    port="5432"
)
cursor = conn.cursor()

# 🔹 Upload endpoint
@app.post("/upload-bill/")
async def upload_bill(
    bill_type: str = Form(...),       # electricity, water, etc.
    bill_month: int = Form(...),      # 1-12
    bill_year: int = Form(...),       # 2023, 2024...
    file: UploadFile = File(...),
    current_hotel: dict = Depends(get_current_hotel)  # 🔹 Added authentication
):
    try:
        # Validate inputs
        if bill_type not in ["electricity", "water"]:
            raise HTTPException(status_code=400, detail="Invalid bill type")

        # Extract hotel information from JWT token
        hotel_id = current_hotel["hotel_id"]
        hotel_name = current_hotel["hotel_name"]

        # Generate unique filename with hotel identifier
        filename = f"{hotel_id}_{bill_type}_{bill_year}_{bill_month}_{datetime.now().timestamp()}_{file.filename}"

        # Upload file to S3
        s3.upload_fileobj(file.file, S3_BUCKET, filename)

        # S3 URL
        file_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{filename}"

        # Save metadata + URL into DB with hotel information
        cursor.execute(
            "INSERT INTO utility_bills (hotel_id, hotel_name, bill_type, bill_month, bill_year, file_url) VALUES (%s, %s, %s, %s, %s, %s)",
            (hotel_id, hotel_name, bill_type, bill_month, bill_year, file_url)
        )
        conn.commit()

        return {"message": "Bill uploaded successfully", "file_url": file_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
