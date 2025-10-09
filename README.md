# SIH Problem List Management System

## 🌿 Medical Coding System with MongoDB Integration

A comprehensive medical coding system that integrates NAMASTE (National Medical Coding System for Traditional Medicine) with ICD-11 codes, now featuring **MongoDB database storage** for persistent problem list management.

## ✨ Key Features

- **Dual Search System**: Search both NAMASTE and ICD-11 medical codes
- **Intelligent Mapping**: Auto-map NAMASTE codes to corresponding ICD-11 codes
- **Problem List Management**: Add, view, and manage patient problem lists
- **FHIR Compliance**: Store data in FHIR R4 Condition resource format
- **MongoDB Storage**: Persistent database storage for all entries
- **Patient Management**: Organize entries by patient ABHA ID

## 🏗️ Architecture

### Backend Services
- **Flask Server** (Port 5000): NAMASTE/ICD-11 search and mapping
- **Express Server** (Port 5001): MongoDB operations for problem lists
- **MongoDB Database**: FHIR-compliant data storage

### Frontend
- **React Application** (Port 3000/5173): User interface with search and problem list management

## 🚀 Quick Start

### Prerequisites
1. **MongoDB** - Install locally or use MongoDB Atlas
2. **Python 3.8+** - For Flask server
3. **Node.js 16+** - For Express server and React frontend

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sarthak232425/SIH-Win9devs.git
   cd SIH-Win9devs
   ```

2. **Setup Backend**
   ```bash
   cd backend
   
   # Install Node.js dependencies
   npm install
   
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Create environment file
   copy .env.example .env
   # Edit .env with your MongoDB URI and API keys
   ```

3. **Setup Frontend**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Start MongoDB**
   ```bash
   # Windows (as Administrator)
   net start MongoDB
   
   # Or manually
   mongod --dbpath "C:\data\db"
   ```

5. **Start All Services**
   ```bash
   # Option 1: Automated (Recommended)
   cd backend
   start-servers.bat  # or .\start-servers.ps1
   
   # Option 2: Manual
   # Terminal 1: Flask server
   python flask_server.py
   
   # Terminal 2: Express server  
   node expressServer.js
   
   # Terminal 3: Frontend
   cd ../frontend
   npm run dev
   ```

## 📚 Usage

### 1. Search Medical Codes
- Search NAMASTE codes for traditional medicine
- Search ICD-11 codes for modern medical conditions
- Filter by medical system (Ayurveda, Unani, Siddha)

### 2. Code Mapping
- Enter NAMASTE codes to find corresponding ICD-11 codes
- Get similarity scores and detailed mappings

### 3. Problem List Management
- Add patient problem list entries with ABHA ID
- Search and select NAMASTE codes
- Auto-map to ICD-11 codes
- Preview FHIR JSON format
- Save to MongoDB database
- View all entries organized by patient

## 🗄️ Database Schema

Problem list entries are stored in MongoDB as FHIR Condition resources:

```javascript
{
  patientId: "12-3456-7890-1234",
  condition: "Fever with headache", 
  selectedNamasteCode: {
    code: "AYU-001",
    title: "Jwara",
    description: "Fever in Ayurvedic medicine"
  },
  selectedIcd11Code: {
    code: "MG30",
    title: "Fever, unspecified",
    similarity_score: 0.85
  },
  fhirCondition: { ... }, // Full FHIR R4 Condition resource
  createdAt: "2025-01-01T00:00:00.000Z"
}
```

## 🔧 Configuration

### Environment Variables
```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=problemlist

# API Configuration
GOOGLE_API_KEY=your_gemini_api_key
EXPRESS_PORT=5001
```

### FHIR Compliance
All problem list entries are stored as valid FHIR R4 Condition resources with:
- Proper resource identification
- Clinical and verification status codes
- NAMASTE and ICD-11 code mappings
- Patient references using ABHA ID

## 📡 API Endpoints

### Search & Mapping (Flask - Port 5000)
- `GET /search_ayurvedic?q=query&k=5`
- `GET /search_icd?q=query&k=5` 
- `GET /map?query=text&k=5`

### Problem List Management (Express - Port 5001)
- `POST /api/problem-list` - Create entry
- `GET /api/problem-list` - Get all entries
- `GET /api/problem-list/patient/:id` - Get patient entries
- `GET /api/problem-list/stats` - Database statistics

## 🛠️ Development

### Technology Stack
- **Backend**: Python (Flask), Node.js (Express), MongoDB
- **Frontend**: React, Tailwind CSS, Vite
- **Standards**: FHIR R4, MongoDB, RESTful APIs
- **Search**: Vector similarity using sentence-transformers

### Key Components
- **Search Engines**: NAMASTE and ICD-11 semantic search
- **Mapping System**: Intelligent code mapping with similarity scores  
- **FHIR Utils**: Validation and conversion to FHIR format
- **MongoDB Service**: Database operations and API integration

## 📄 Documentation

- [MongoDB Setup Guide](backend/README-MongoDB.md) - Detailed database setup
- [FHIR Implementation](frontend/src/utils/fhirUtils.js) - FHIR resource handling
- [API Documentation](backend/api/problemListAPI.js) - Complete API reference

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For issues and questions:
- Check the [MongoDB Setup Guide](backend/README-MongoDB.md)
- Review API documentation in the codebase
- Open an issue on GitHub

---

**Built for Smart India Hackathon 2024** - Bridging traditional and modern medical coding systems with robust database storage.
