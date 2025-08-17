# � Hotel & Travel Carbon Tracking System - A Story-Based Guide

## 📖 The Story: How Hotels Track Their Carbon Footprint

Imagine you're running a hotel, and you want to be environmentally responsible by tracking how much electricity and water you use each month. This application is like having a digital environmental consultant that not only stores your utility bills but also calculates your exact carbon footprint based on your actual consumption!

**🌍 What makes this special?** When you upload a bill, you enter the exact amount you consumed (like "1,450 kWh of electricity" or "2,500 liters of water"), and the system automatically calculates how much CO2 your hotel produced. It's like having a personal carbon footprint calculator that helps you become more environmentally friendly!

---

## 🎭 Meet the Characters in Our Story

### 🏨 **The Hotel Manager (You!)**
- You want to upload your monthly electricity and water bills
- You need to enter the exact consumption amounts from your bills (kWh, liters, etc.)
- You want to see your carbon footprint calculations automatically
- You need to see all your past bills to track your usage trends
- You care about the environment and want to reduce your carbon emissions

### 🔐 **The Security Guard (Authentication System)**
- Makes sure only you can see your hotel's bills and carbon data
- Gives you a special "access card" (JWT token) when you log in
- Protects your sensitive consumption data from other hotels

### 📁 **The Filing Cabinet (Database)**
- Stores information about your hotel account
- Keeps track of all your bill records with consumption amounts
- Remembers when you uploaded each bill and calculates carbon footprint

### ☁️ **The Cloud Storage (AWS S3)**
- Safely stores your actual bill files (PDFs, images)
- Like a secure online vault for your documents
- Gives each file a unique address so you can find it later

### 🧮 **The Carbon Calculator (New!)**
- Automatically calculates CO2 emissions from your consumption data
- Uses scientific emission factors (electricity = 0.5 kg CO2 per kWh)
- Provides monthly and yearly carbon footprint reports
- Helps you track your environmental progress over time

---

## 📚 Chapter 1: The Application Modules (Our Story Characters)

### 📄 `main.py` - The Hotel Reception Desk
**What it does:** This is the main entrance to our hotel system!

```
🏨 Welcome to Carbon Tracking Hotel! 🏨
│
├── 🚪 Front Desk (main.py)
│   ├── "Welcome! How can I help you today?"
│   ├── 📋 Registration Counter (/auth)
│   └── 📄 Bill Management Office (/bills)
│
└── 📊 Information Board
    ├── API Documentation at /docs
    └── System Status: "All systems running!"
```

**The Story:** When you visit our hotel website, you first arrive at the reception desk. The friendly receptionist (main.py) greets you and shows you where to go:
- Need to create an account or log in? → Go to the Registration Counter
- Want to upload or view bills? → Visit the Bill Management Office
- Need help understanding the system? → Check the Information Board

---

### 🔐 `auth.py` - The Registration & Security Office
**What it does:** Handles all the "who are you?" questions!

#### 🏃‍♂️ **Character 1: The Registration Clerk**
```python
def register()  # "Welcome new hotel! Let me create your account"
```
**The Story:** When a new hotel wants to join our system:
1. 📝 Hotel fills out a form: "My name is Grand Resort, email is admin@grandresort.com"
2. 🔒 Clerk securely locks away the password (like putting it in a safe)
3. 📋 Creates a new file in the filing cabinet with hotel details
4. 🎉 "Congratulations! Your account is ready!"

#### 🕵️‍♂️ **Character 2: The Login Validator**
```python
def login()  # "Let me check your credentials and give you an access card"
```
**The Story:** When a hotel wants to log in:
1. 🏨 Hotel says: "I'm admin@grandresort.com, my password is secret123"
2. 🔍 Validator checks: "Let me look up your file... Yes, password matches!"
3. 🎫 Gives hotel a special access card (JWT token): "Here's your day pass!"
4. 💳 "Keep this card safe - you'll need it to access your bills!"

#### 🛡️ **Character 3: The Security Guard**
```python
def get_current_hotel()  # "Show me your access card before entering"
```
**The Story:** Every time a hotel wants to do something:
1. 🚪 Hotel approaches: "I want to upload a bill"
2. 🎫 Guard asks: "Please show your access card"
3. 🔍 Guard examines card: "Valid card! You're Grand Resort, ID #123"
4. ✅ "You may proceed to the Bill Management Office"

---

### 🗃️ `models.py` - The Filing Cabinet Structure
**What it does:** Defines how we organize information in our filing cabinet!

#### 📁 **Cabinet Section 1: Hotel Files**
```python
class Hotel  # The "Hotels" drawer in our filing cabinet
```
**The Story:** Imagine a filing cabinet drawer labeled "HOTELS":
```
📁 HOTELS Drawer
├── 🏨 Grand Resort Hotel
│   ├── 🆔 ID: #123
│   ├── 📧 Email: admin@grandresort.com
│   ├── 🔒 Password: [LOCKED SAFE]
│   └── 📅 Joined: March 1, 2024
│
├── 🏨 Ocean View Inn
│   ├── 🆔 ID: #124
│   └── 📧 Email: info@oceanview.com
```

#### 📋 **Cabinet Section 2: Bill Records**
```python
class UtilityBill  # The "Bills" drawer in our filing cabinet
```
**The Story:** Another drawer labeled "UTILITY BILLS WITH CONSUMPTION DATA":
```
📋 UTILITY BILLS Drawer
├── 📄 Bill #001
│   ├── 🏨 Belongs to: Grand Resort (#123)
│   ├── ⚡ Type: Electricity
│   ├── 📅 For: March 2024
│   ├── 📊 Amount: 1,450.75 kWh  ⚡ NEW!
│   ├── 🧮 CO2 Impact: 725.375 kg ⚡ CALCULATED!
│   └── 🔗 File Location: https://cloud-storage.com/bill001.pdf
│
├── 📄 Bill #002
│   ├── 🏨 Belongs to: Grand Resort (#123)
│   ├── 💧 Type: Water
│   ├── 📅 For: March 2024
│   ├── 📊 Amount: 2,500 liters  ⚡ NEW!
│   ├── 🧮 CO2 Impact: 2.5 kg    ⚡ CALCULATED!
│   └── 🔗 File Location: https://cloud-storage.com/bill002.pdf
```

---

### 🗄️ `database.py` - The Filing Cabinet Manager
**What it does:** Manages the actual filing cabinet and keeps it organized!

#### 🔌 **The Cabinet Connection**
```python
engine  # The main connection to our filing cabinet
```
**The Story:** This is like the electrical connection that powers our filing cabinet. Without it, we can't open any drawers or store any files!

#### 📝 **The Session Manager**
```python
def get_db()  # "Here's a clipboard for your paperwork session"
```
**The Story:** Every time someone wants to use the filing cabinet:
1. 📋 Manager gives them a clipboard: "Use this for your paperwork"
2. ✍️ Person does their work: add files, find files, update files
3. ✅ When done, clipboard is returned: "Thanks! Everything filed properly"
4. 🔒 Cabinet automatically locks: "All secure until next person"

---

### 📊 `schemas.py` - The Form Templates
**What it does:** Provides official forms that everyone must fill out correctly!

#### 📝 **Form 1: New Hotel Registration**
```python
class HotelCreate  # "Please fill out this form to join our system"
```
**The Story:** Like a paper form at a doctor's office:
```
🏨 NEW HOTEL REGISTRATION FORM
├── Hotel Name: [________________]  (Required)
├── Email Address: [_____________]  (Must be valid email)
└── Password: [_________________]  (At least 8 characters)

❌ REJECTED: "abc" - Password too short!
✅ ACCEPTED: "securepassword123" - Perfect!
```

#### 🎫 **Form 2: Login Ticket**
```python
class HotelLogin  # "Show us your login credentials"
```
**The Story:** Like a ticket to enter a movie theater:
```
🎫 LOGIN TICKET
├── Email: [____________________]
└── Password: [_________________]

🔍 Checking... ✅ "Welcome back, Grand Resort!"
```

#### � **Form 3: Bill Upload with Consumption Data**
```python
class BillUploadResponse  # "Here's your receipt for the uploaded bill with carbon calculation"
```
**The Story:** Like a detailed receipt you get after an environmental assessment:
```
🧾 BILL UPLOAD & CARBON CALCULATION RECEIPT
├── ✅ Bill ID: #123
├── ⚡ Type: Electricity
├── 📅 Period: March 2024
├── � Consumption: 1,450.75 kWh     ⚡ NEW!
├── 🧮 CO2 Emissions: 725.375 kg    ⚡ CALCULATED!
├── 📏 Unit: kWh                    ⚡ NEW!
├── �🔗 Stored at: https://cloud-storage.com/...
└── 💬 Status: "Bill uploaded and carbon footprint calculated!"
```

---

### 📁 `routes.py` - The Bill Management Office
**What it does:** The actual office where bill-related work happens!

#### 📤 **Service Counter 1: Bill Upload with Carbon Tracking**
```python
async def upload_bill()  # "I'd like to submit my monthly electricity bill with consumption data"
```
**The Story:** A step-by-step environmental tracking journey:

1. **🚪 Hotel enters office**: "I want to upload my March electricity bill showing 1,450.75 kWh"
2. **🎫 Security check**: "Please show your access card first"
3. **📋 Form validation**: "Let me check your form and consumption data..."
   ```
   ✅ Bill type: "electricity" - Valid!
   ✅ Month: 3 (March) - Valid!
   ✅ Year: 2024 - Valid!
   ✅ Consumption: "1450.75" - Valid number!
   ✅ Unit: "kWh" - Valid for electricity!
   ✅ File: electricity_bill.pdf - Valid!
   ```
4. **🏷️ File labeling**: Creates unique name: "123_electricity_2024_3_1647891234_bill.pdf"
5. **☁️ Cloud storage**: "Uploading to secure cloud vault..."
6. **🧮 Carbon calculation**: "1,450.75 kWh × 0.5 kg CO2/kWh = 725.375 kg CO2"
7. **📁 Filing**: "Adding record with consumption and carbon data to your hotel's file..."
8. **🧾 Environmental receipt**: "Bill #456 uploaded! Your carbon footprint: 725.375 kg CO2"

#### 📋 **Service Counter 2: View My Bills with Carbon Data**
```python
async def get_my_bills()  # "I'd like to see all my hotel's bills and carbon footprint"
```
**The Story:** Like asking for your environmental impact statement:

1. **🚪 Hotel enters**: "Can I see all my bills and carbon footprint please?"
2. **🎫 Security check**: "Access card please... You're Grand Resort #123"
3. **🗃️ File search**: "Let me pull up all bills and carbon data for hotel #123..."
4. **📄 Environmental results**: 
   ```
   📋 YOUR BILLS & CARBON FOOTPRINT:
   ├── ⚡ March 2024 Electricity - 1,450.75 kWh → 725.375 kg CO2
   ├── 💧 March 2024 Water - 2,500 liters → 2.5 kg CO2
   ├── ⚡ February 2024 Electricity - 1,200 kWh → 600 kg CO2
   └── 💧 February 2024 Water - 2,200 liters → 2.2 kg CO2
   
   📊 TOTAL CARBON FOOTPRINT: 1,329.875 kg CO2
   ```

#### 🧮 **Service Counter 3: Carbon Footprint Calculator (NEW!)**
```python
async def calculate_carbon_footprint()  # "Show me my total environmental impact"
```
**The Story:** Like getting a comprehensive environmental report:

1. **🚪 Hotel enters**: "I want to see my complete carbon footprint analysis"
2. **🎫 Security check**: "Access card verified - Grand Resort #123"
3. **🧮 Calculation engine**: "Analyzing all your consumption data..."
4. **📊 Environmental report**:
   ```
   🌍 CARBON FOOTPRINT REPORT - Grand Resort Hotel
   
   📅 Year: 2024
   🧮 Total CO2 Emissions: 1,329.875 kg
   
   ⚡ ELECTRICITY BREAKDOWN:
   ├── Total Consumption: 2,650.75 kWh
   ├── CO2 Emissions: 1,325.375 kg
   └── Factor: 0.5 kg CO2 per kWh
   
   💧 WATER BREAKDOWN:
   ├── Total Consumption: 4,700 liters
   ├── CO2 Emissions: 4.7 kg
   └── Factor: 0.001 kg CO2 per liter
   
   📈 MONTHLY TRENDS:
   ├── March 2024: 727.875 kg CO2
   └── February 2024: 602.2 kg CO2
   ```

---

## 🎬 Chapter 2: The Complete User Journey

### 🎭 Act 1: "The New Hotel Arrives"
```
🏨 Grand Resort Hotel decides to join the carbon tracking system
```

1. **🌐 Visit the website**: Goes to `http://localhost:8000`
2. **📝 Create account**: POST to `/auth/register`
   ```json
   {
     "name": "Grand Resort Hotel",
     "email": "admin@grandresort.com", 
     "password": "securepassword123"
   }
   ```
3. **🎉 Success**: "Hotel registered successfully!"

### 🎭 Act 2: "The Daily Login Routine"
```
🔑 Hotel manager starts their day by logging in
```

1. **🚪 Login**: POST to `/auth/login`
   ```json
   {
     "email": "admin@grandresort.com",
     "password": "securepassword123"
   }
   ```
2. **🎫 Receive access card**: Gets JWT token
   ```json
   {
     "access_token": "eyJ0eXAiOiJKV1QiLCJ...",
     "token_type": "bearer",
     "hotel_id": 123,
     "hotel_name": "Grand Resort Hotel"
   }
   ```

### 🎭 Act 3: "The Monthly Bill Upload with Environmental Tracking"
```
📄 It's the end of March, time to upload the electricity bill with consumption data!
```

1. **📤 Upload bill with consumption**: POST to `/bills/upload`
   ```
   Headers: Authorization: Bearer eyJ0eXAiOiJKV1QiLCJ...
   Form Data:
   - bill_type: "electricity"
   - bill_month: 3
   - bill_year: 2024
   - bill_amount: "1450.75"  ⚡ NEW!
   - unit: "kWh"            ⚡ NEW!
   - file: march_electricity.pdf
   ```

2. **🔄 Behind the scenes environmental magic**:
   ```
   ✅ Token validated → "You're Grand Resort #123"
   ✅ Form validated → "All data looks good"
   ✅ Consumption validated → "1450.75 kWh is valid for electricity"
   ✅ Unit validated → "kWh is correct for electricity bills"
   📁 File renamed → "123_electricity_2024_3_1647891234_march_electricity.pdf"
   ☁️ Upload to S3 → "File safely stored in cloud"
   🧮 Carbon calculation → "1450.75 × 0.5 = 725.375 kg CO2"
   📋 Database record → "Consumption and carbon data saved in filing cabinet"
   ```

3. **🧾 Environmental impact receipt**:
   ```json
   {
     "id": 456,
     "bill_type": "electricity",
     "bill_month": 3,
     "bill_year": 2024,
     "bill_amount": "1450.75",
     "unit": "kWh",
     "file_url": "https://bucket.s3.amazonaws.com/123_electricity_2024_3_...",
     "message": "Bill uploaded successfully"
   }
   ```

### 🎭 Act 4: "The Carbon Footprint Analysis"
```
🧮 Hotel manager wants to see their environmental impact
```

1. **🌍 Request carbon footprint**: GET to `/bills/carbon-footprint?year=2024`
   ```
   Headers: Authorization: Bearer eyJ0eXAiOiJKV1QiLCJ...
   ```

2. **🔍 System calculates**: "Analyzing all consumption data for Grand Resort #123..."

3. **� Environmental impact report**:
   ```json
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
         "electricity_kwh": 1450.75,
         "water_liters": 0,
         "total_co2_kg": 725.375
       }
     ]
   }
   ```

---

## 🛠️ Chapter 3: Setting Up Your Hotel System

### 📦 Step 1: Gather Your Supplies
```bash
# Install all the tools you need
pip install -r requirements.txt
```
**What this does**: Like buying all the office supplies before opening your business!

### 🔧 Step 2: Configure Your Office
```bash
# Copy the example environment file
cp .env.example .env
```
**Then edit `.env` with your real information**:
```env
# Your secret key (like the master key to your office)
JWT_SECRET_KEY=your-super-secret-key-here

# Your cloud storage credentials (like your cloud storage account)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
S3_BUCKET=your-bucket-name

# Your database location (like your filing cabinet address)
DATABASE_URL=postgresql://user:password@host:5432/database
```

### 🚀 Step 3: Open for Business!
```bash
# Start your hotel system
uvicorn app.main:app --reload
```
**What happens**:
1. 🏗️ System builds the filing cabinet (creates database tables)
2. 🔌 Connects to cloud storage (AWS S3)
3. 🚪 Opens the front doors (starts web server)
4. 📢 Announces: "Carbon Tracking Hotel is now open at http://localhost:8000!"

### � Step 4: Read the Manual
Visit these helpful guides:
- 📚 **API Documentation**: http://localhost:8000/docs (Interactive guide with carbon calculator)
- 📋 **Alternative Docs**: http://localhost:8000/redoc (Detailed manual)
- 🧮 **Carbon Calculator**: Try the `/bills/carbon-footprint` endpoint
- 📊 **Sample Data**: Upload bills with consumption amounts to see calculations

---

## 🔒 Chapter 4: Security Features (How We Keep Your Data Safe)

### 🛡️ **The Multi-Layer Security System**

1. **🎫 Access Cards (JWT Tokens)**
   - Like hotel key cards that expire after 24 hours
   - Each card contains encrypted hotel information
   - Must be shown for every bill-related action

2. **🔒 Password Protection**
   - Passwords are scrambled using special encryption (bcrypt)
   - Even system administrators can't see your real password
   - Like having a safe that only you know the combination to

3. **🏷️ File Separation**
   - Each hotel's files are tagged with their unique ID
   - Hotel A can never see Hotel B's bills
   - Like having separate locked file cabinets for each hotel

4. **☁️ Cloud Security**
   - Files stored in professional-grade AWS cloud storage
   - Multiple backups ensure your data never gets lost
   - Like having a bank vault for your important documents

---

## 🎯 Chapter 5: What Makes This System Special

### 🌟 **For Hotel Managers**
- **📱 Easy to use**: Simple web interface, no technical knowledge needed
- **🔒 Secure**: Your bills and consumption data are private and protected
- **📊 Organized**: All bills in one place with automatic carbon calculations
- **🌍 Environmental**: Track your actual carbon footprint over time
- **🧮 Smart calculations**: Automatic CO2 emission calculations from consumption data
- **📈 Trend tracking**: See if your environmental impact is improving
- **🎯 Goal setting**: Use real data to set and track carbon reduction targets

### 🌟 **For Environmental Consultants**
- **📊 Accurate data**: Real consumption amounts, not estimates
- **🧮 Scientific calculations**: Uses standard emission factors
- **📈 Trend analysis**: Track carbon footprint changes over time
- **📋 Detailed reports**: Monthly and yearly breakdowns
- **🔬 Audit trail**: Bills stored as evidence for carbon calculations

### 🌟 **For Developers**
- **🧩 Modular**: Each part does one job well
- **📚 Well-documented**: Every function explained clearly
- **🔧 Extensible**: Easy to add new utility types or emission factors
- **✅ Production-ready**: Includes security, validation, and error handling
- **🧮 Mathematical**: Handles precise carbon footprint calculations

### 🌟 **For the Environment**
- **📈 Accurate tracking**: Real consumption data enables precise carbon calculations
- **📊 Emission analytics**: Helps hotels understand their environmental impact
- **🎯 Reduction goals**: Enables data-driven carbon reduction strategies
- **🌱 Sustainability**: Supports the hospitality industry's green initiatives
- **🏆 Benchmarking**: Compare carbon efficiency across time periods

---

## 🎓 Chapter 6: Learning Opportunities

### 🔍 **What You'll Learn by Studying This Code**
- **🌐 Web APIs**: How modern web applications communicate
- **🔐 Authentication**: How to securely identify users
- **🗄️ Databases**: How to store and organize data
- **☁️ Cloud Storage**: How to handle file uploads at scale
- **📊 Data Validation**: How to ensure data quality
- **🛡️ Security**: How to protect user information
- **🧮 Mathematical Computing**: How to perform scientific calculations in web apps
- **📈 Environmental Analytics**: How to calculate and track carbon footprints
- **🌍 Sustainability Tech**: How technology can help environmental goals

### 📖 **Technologies Used (Your Learning Path)**
- **FastAPI**: Modern Python web framework
- **JWT**: Secure authentication tokens
- **SQLAlchemy**: Database management made easy
- **Pydantic**: Data validation and serialization
- **PostgreSQL**: Professional database system
- **AWS S3**: Cloud file storage
- **bcrypt**: Password security
- **Carbon Calculations**: Environmental impact mathematics

---

## 🎉 Conclusion: Your Carbon Tracking Journey Begins!

Congratulations! You now understand how the Hotel Carbon Tracking System works. This isn't just a file storage system - it's a comprehensive environmental management platform that helps hotels become more environmentally responsible through precise carbon footprint tracking.

**🌍 The Environmental Impact:**
- Every uploaded bill with consumption data becomes a data point for carbon calculations
- Every tracked month is progress toward understanding your environmental impact
- Every hotel that joins makes the hospitality industry a little more green
- Every carbon calculation helps identify opportunities for energy reduction

**🧮 The Science Behind It:**
- **Electricity**: Each kWh consumed generates approximately 0.5 kg of CO2 (varies by region)
- **Water**: Each liter consumed generates approximately 0.001 kg of CO2 (includes treatment and distribution)
- **Tracking**: Precise consumption data enables accurate carbon footprint calculations
- **Progress**: Monthly and yearly comparisons show environmental improvement trends

**📈 Your Sustainability Journey:**
1. **📊 Track**: Upload bills with exact consumption amounts
2. **🧮 Calculate**: Get automatic carbon footprint calculations
3. **📈 Analyze**: Review trends and identify patterns
4. **🎯 Improve**: Set reduction goals based on real data
5. **🏆 Achieve**: Measure success with precise metrics

**🌍 Ready to make a difference? Let's start tracking that carbon footprint and building a more sustainable future!**

---

*Made with 💚 for a more sustainable future - Every kWh tracked, every liter measured, every gram of CO2 calculated brings us closer to a greener hospitality industry* 🌱
