/**
 * Express Server with MongoDB Integration for Problem List
 * Runs alongside Flask server for MongoDB operations
 */

const express = require('express');
const cors = require('cors');
const { initializeProblemListAPI } = require('./api/problemListAPI');
require('dotenv').config();

const app = express();
const PORT = process.env.EXPRESS_PORT || 5001;

// Middleware
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:5173'], // React dev servers
  credentials: true
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Add request logging
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// Initialize Problem List API routes
initializeProblemListAPI(app);

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'Problem List MongoDB API',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: 'Problem List MongoDB API Server',
    status: 'running',
    endpoints: {
      'POST /api/problem-list': 'Create new problem list entry',
      'GET /api/problem-list': 'Get all problem list entries (with pagination)',
      'GET /api/problem-list/patient/:patientId': 'Get entries for specific patient',
      'GET /api/problem-list/stats': 'Get database statistics',
      'PUT /api/problem-list/:id': 'Update entry by ID',
      'DELETE /api/problem-list/:id': 'Delete entry by ID',
      'GET /api/health': 'Health check'
    },
    timestamp: new Date().toISOString()
  });
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Server Error:', error);
  res.status(500).json({
    message: 'Internal server error',
    error: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    message: 'Endpoint not found',
    path: req.path,
    method: req.method
  });
});

// Start server
app.listen(PORT, () => {
  console.log('🚀 Problem List MongoDB API Server Started');
  console.log('=' + '='.repeat(50));
  console.log(`📡 Server running on: http://localhost:${PORT}`);
  console.log(`🗄️  Database: ${process.env.MONGODB_URI || 'mongodb://localhost:27017'}`);
  console.log(`🌐 CORS enabled for React dev servers`);
  console.log(`🔍 API endpoints available at /api/problem-list`);
  console.log('=' + '='.repeat(50));
  console.log('💡 Press Ctrl+C to stop');
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('👋 Received SIGTERM, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('\n👋 Received SIGINT, shutting down gracefully');
  process.exit(0);
});