/**
 * Problem List API Routes
 * MongoDB CRUD operations for problem list entries
 */

const { MongoClient, ObjectId } = require('mongodb');
require('dotenv').config();

// MongoDB connection configuration
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017';
const DATABASE_NAME = process.env.DATABASE_NAME || 'problemlist';
const COLLECTION_NAME = 'entries';

let db = null;

/**
 * Connect to MongoDB
 */
async function connectToMongoDB() {
  if (db) return db;
  
  try {
    console.log('Connecting to MongoDB...');
    const client = new MongoClient(MONGODB_URI, {
      useUnifiedTopology: true,
    });
    
    await client.connect();
    console.log('MongoDB connected successfully');
    
    db = client.db(DATABASE_NAME);
    
    // Create indexes for better performance
    await db.collection(COLLECTION_NAME).createIndex({ patientId: 1 });
    await db.collection(COLLECTION_NAME).createIndex({ createdAt: -1 });
    await db.collection(COLLECTION_NAME).createIndex({ 'fhirCondition.id': 1 });
    
    return db;
  } catch (error) {
    console.error('MongoDB connection error:', error);
    throw error;
  }
}

/**
 * Initialize problem list API routes
 * @param {Object} app - Express app instance
 */
function initializeProblemListAPI(app) {
  
  // CREATE: Save new problem list entry
  app.post('/api/problem-list', async (req, res) => {
    try {
      const database = await connectToMongoDB();
      const collection = database.collection(COLLECTION_NAME);
      
      const entry = req.body;
      
      // Add metadata
      entry.createdAt = new Date();
      entry.updatedAt = new Date();
      
      // Insert into MongoDB
      const result = await collection.insertOne(entry);
      
      // Return the saved entry with MongoDB ID
      const savedEntry = {
        ...entry,
        _id: result.insertedId
      };
      
      console.log(`Problem list entry saved with ID: ${result.insertedId}`);
      
      res.status(201).json(savedEntry);
    } catch (error) {
      console.error('Error saving problem list entry:', error);
      res.status(500).json({
        message: 'Failed to save problem list entry',
        error: error.message
      });
    }
  });

  // READ: Get all problem list entries
  app.get('/api/problem-list', async (req, res) => {
    try {
      const database = await connectToMongoDB();
      const collection = database.collection(COLLECTION_NAME);
      
      // Get pagination parameters
      const page = parseInt(req.query.page) || 1;
      const limit = parseInt(req.query.limit) || 50;
      const skip = (page - 1) * limit;
      
      // Get entries with pagination, sorted by creation date (newest first)
      const entries = await collection
        .find({})
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(limit)
        .toArray();
      
      const totalEntries = await collection.countDocuments({});
      
      console.log(`Retrieved ${entries.length} problem list entries (page ${page})`);
      
      res.json({
        entries,
        pagination: {
          page,
          limit,
          total: totalEntries,
          totalPages: Math.ceil(totalEntries / limit)
        }
      });
    } catch (error) {
      console.error('Error fetching problem list entries:', error);
      res.status(500).json({
        message: 'Failed to fetch problem list entries',
        error: error.message
      });
    }
  });

  // READ: Get problem list entries for specific patient
  app.get('/api/problem-list/patient/:patientId', async (req, res) => {
    try {
      const database = await connectToMongoDB();
      const collection = database.collection(COLLECTION_NAME);
      
      const patientId = req.params.patientId;
      
      // Get entries for the specific patient
      const entries = await collection
        .find({ patientId: patientId })
        .sort({ createdAt: -1 })
        .toArray();
      
      console.log(`Retrieved ${entries.length} entries for patient: ${patientId}`);
      
      res.json(entries);
    } catch (error) {
      console.error('Error fetching patient entries:', error);
      res.status(500).json({
        message: 'Failed to fetch patient entries',
        error: error.message
      });
    }
  });

  // READ: Get statistics
  app.get('/api/problem-list/stats', async (req, res) => {
    try {
      const database = await connectToMongoDB();
      const collection = database.collection(COLLECTION_NAME);
      
      // Aggregate statistics
      const stats = await collection.aggregate([
        {
          $group: {
            _id: null,
            totalEntries: { $sum: 1 },
            uniquePatients: { $addToSet: '$patientId' },
            namasteCodesUsed: { $addToSet: '$selectedNamasteCode.code' },
            icd11CodesUsed: { $addToSet: '$selectedIcd11Code.code' },
            clinicalStatuses: { $push: '$clinicalStatus' },
            verificationStatuses: { $push: '$verificationStatus' },
            oldestEntry: { $min: '$createdAt' },
            newestEntry: { $max: '$createdAt' }
          }
        }
      ]).toArray();
      
      if (stats.length === 0) {
        return res.json({
          totalEntries: 0,
          patientsCount: 0,
          codesUsed: { namaste: 0, icd11: 0 },
          statusBreakdown: {},
          dateRange: null
        });
      }
      
      const result = stats[0];
      
      // Count status occurrences
      const clinicalStatusCount = {};
      const verificationStatusCount = {};
      
      result.clinicalStatuses.forEach(status => {
        clinicalStatusCount[status] = (clinicalStatusCount[status] || 0) + 1;
      });
      
      result.verificationStatuses.forEach(status => {
        verificationStatusCount[status] = (verificationStatusCount[status] || 0) + 1;
      });
      
      const finalStats = {
        totalEntries: result.totalEntries,
        patientsCount: result.uniquePatients.length,
        codesUsed: {
          namaste: result.namasteCodesUsed.filter(code => code).length,
          icd11: result.icd11CodesUsed.filter(code => code).length
        },
        statusBreakdown: {
          clinical: clinicalStatusCount,
          verification: verificationStatusCount
        },
        dateRange: {
          oldest: result.oldestEntry,
          newest: result.newestEntry
        }
      };
      
      console.log('Statistics retrieved:', finalStats);
      
      res.json(finalStats);
    } catch (error) {
      console.error('Error fetching statistics:', error);
      res.status(500).json({
        message: 'Failed to fetch statistics',
        error: error.message
      });
    }
  });

  // UPDATE: Update problem list entry
  app.put('/api/problem-list/:id', async (req, res) => {
    try {
      const database = await connectToMongoDB();
      const collection = database.collection(COLLECTION_NAME);
      
      const entryId = req.params.id;
      const updateData = req.body;
      
      // Add updated timestamp
      updateData.updatedAt = new Date();
      
      const result = await collection.updateOne(
        { _id: new ObjectId(entryId) },
        { $set: updateData }
      );
      
      if (result.matchedCount === 0) {
        return res.status(404).json({
          message: 'Problem list entry not found'
        });
      }
      
      console.log(`Problem list entry updated: ${entryId}`);
      
      res.json({
        message: 'Problem list entry updated successfully',
        modifiedCount: result.modifiedCount
      });
    } catch (error) {
      console.error('Error updating problem list entry:', error);
      res.status(500).json({
        message: 'Failed to update problem list entry',
        error: error.message
      });
    }
  });

  // DELETE: Delete problem list entry
  app.delete('/api/problem-list/:id', async (req, res) => {
    try {
      const database = await connectToMongoDB();
      const collection = database.collection(COLLECTION_NAME);
      
      const entryId = req.params.id;
      
      const result = await collection.deleteOne({ _id: new ObjectId(entryId) });
      
      if (result.deletedCount === 0) {
        return res.status(404).json({
          message: 'Problem list entry not found'
        });
      }
      
      console.log(`Problem list entry deleted: ${entryId}`);
      
      res.json({
        message: 'Problem list entry deleted successfully'
      });
    } catch (error) {
      console.error('Error deleting problem list entry:', error);
      res.status(500).json({
        message: 'Failed to delete problem list entry',
        error: error.message
      });
    }
  });
  
  console.log('Problem List API routes initialized');
}

module.exports = {
  initializeProblemListAPI,
  connectToMongoDB
};