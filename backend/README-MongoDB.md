# SIH Problem List MongoDB Setup

## Overview
The application now uses MongoDB to store problem list entries in FHIR Condition resource format. All previous file-based storage has been removed for proper data persistence.

## Architecture
- **Flask Server** (Port 5000): Handles NAMASTE and ICD-11 search functionality
- **Express Server** (Port 5001): Handles MongoDB operations for problem list entries
- **MongoDB Database**: Stores FHIR-compliant problem list entries

## Prerequisites

### 1. MongoDB Installation
Choose one of these options:

#### Option A: Local MongoDB
1. Download and install MongoDB Community Server from https://www.mongodb.com/try/download/community
2. Start MongoDB service:
   ```bash
   # Windows (as Administrator)
   net start MongoDB
   
   # Or start manually
   mongod --dbpath "C:\data\db"
   ```

#### Option B: MongoDB Atlas (Cloud)
1. Create free account at https://www.mongodb.com/cloud/atlas
2. Create a cluster and get connection string
3. Update `.env` file with your Atlas connection string

### 2. Backend Dependencies
```bash
cd backend
npm install
```

## Configuration

### Environment Variables
Create a `.env` file in the backend directory:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=problemlist

# Server Configuration  
EXPRESS_PORT=5001
NODE_ENV=development

# Google API Key (for existing Flask server)
GOOGLE_API_KEY=your_google_api_key_here

# For MongoDB Atlas (replace MONGODB_URI above)
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/problemlist?retryWrites=true&w=majority
```

## Running the Application

### Method 1: Automated Startup (Recommended)
```bash
# Windows Batch File
cd backend
start-servers.bat

# Or PowerShell
cd backend
.\start-servers.ps1
```

### Method 2: Manual Startup
```bash
# Terminal 1: Flask Server
cd backend
python flask_server.py

# Terminal 2: Express Server  
cd backend
node expressServer.js

# Terminal 3: Frontend
cd frontend
npm run dev
```

### Method 3: Development Mode
```bash
cd backend
npm run dev:both  # Runs both servers with auto-restart
```

## API Endpoints

### Flask Server (Port 5000)
- `GET /search_ayurvedic?q=query&k=5` - Search NAMASTE codes
- `GET /search_icd?q=query&k=5` - Search ICD-11 codes
- `GET /map?query=text&k=5` - Map NAMASTE to ICD-11

### Express Server (Port 5001)
- `POST /api/problem-list` - Create problem list entry
- `GET /api/problem-list` - Get all entries (paginated)
- `GET /api/problem-list/patient/:patientId` - Get patient entries
- `GET /api/problem-list/stats` - Get database statistics
- `PUT /api/problem-list/:id` - Update entry
- `DELETE /api/problem-list/:id` - Delete entry
- `GET /api/health` - Health check

## Database Schema

### Collection: `entries`
```javascript
{
  _id: ObjectId,
  patientId: String,
  condition: String,
  selectedNamasteCode: {
    code: String,
    title: String,
    description: String
  },
  selectedIcd11Code: {
    code: String,
    title: String,
    similarity_score: Number
  },
  clinicalStatus: String,
  verificationStatus: String,
  onsetDate: String,
  recordedDate: String,
  notes: String,
  fhirCondition: {
    resourceType: "Condition",
    id: String,
    clinicalStatus: {...},
    verificationStatus: {...},
    category: [...],
    code: {...},
    subject: {...},
    onsetDateTime: String,
    recordedDate: String
  },
  createdAt: Date,
  updatedAt: Date,
  fhirId: String,
  version: String
}
```

## Features

### FHIR Compliance
- All entries stored as FHIR R4 Condition resources
- Proper FHIR validation and ID generation
- NAMASTE and ICD-11 codes mapped to FHIR CodeableConcept

### Problem List Functionality
1. **Search NAMASTE codes** - Find Ayurvedic disease codes
2. **Auto-map to ICD-11** - Automatically find matching ICD-11 codes
3. **FHIR Preview** - Preview the FHIR JSON before saving
4. **MongoDB Storage** - Persistent storage in MongoDB
5. **Patient Management** - Organize by patient ABHA ID

### Data Persistence
- **Database Storage**: All entries stored in MongoDB
- **CRUD Operations**: Create, Read, Update, Delete entries
- **Statistics**: Track usage and entry counts
- **Patient Filtering**: View entries by specific patient

## Troubleshooting

### MongoDB Connection Issues
1. **Check MongoDB Status**:
   ```bash
   # Windows
   sc query MongoDB
   
   # Check if process is running
   tasklist | findstr mongod
   ```

2. **Start MongoDB**:
   ```bash
   # Windows (as Administrator)
   net start MongoDB
   ```

3. **Test Connection**:
   ```bash
   # Using MongoDB Compass or mongo shell
   mongo mongodb://localhost:27017
   ```

### Express Server Issues
1. **Check Port Availability**:
   ```bash
   netstat -an | findstr :5001
   ```

2. **View Logs**:
   - Express server logs show in the terminal
   - Check for MongoDB connection errors

### Common Errors
- **Port 5001 in use**: Change EXPRESS_PORT in .env
- **MongoDB not running**: Start MongoDB service
- **Connection refused**: Check MONGODB_URI in .env
- **No data showing**: Verify Express server is running and API calls are working

## Development

### Adding New Features
1. **Backend**: Add routes in `api/problemListAPI.js`
2. **Frontend**: Update service calls in `services/mongoDBService.js`
3. **Database**: Modify schema in MongoDB operations

### Testing API
```bash
# Test Express server health
curl http://localhost:5001/api/health

# Test MongoDB connection
curl http://localhost:5001/api/problem-list/stats
```

## Migration from File Storage
All previous file-based storage has been removed. The application now uses MongoDB exclusively for:
- ✅ Persistent data storage
- ✅ CRUD operations
- ✅ Multi-user support
- ✅ Better performance
- ✅ Data integrity
- ✅ Backup and recovery