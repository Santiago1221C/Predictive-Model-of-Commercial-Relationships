const express = require('express');
const router = express.Router();
const Rule = require('../models/Rule');

// @route   GET api/rules
// @desc    Get all rules
// @access  Public
router.get('/api/rules', async (req, res) => {
  try {
    // Add logging to debug
    console.log("Fetching rules from database");
    const rules = await Rule.find({});
    console.log(`Found ${rules.length} rules:`, rules);
    
    // Send proper response
    res.status(200).json(rules);
  } catch (error) {
    console.error("Error fetching rules:", error);
    res.status(500).json({ message: 'Error fetching rules', error: error.message });
  }
});

module.exports = router;