import React, { useState, useEffect } from 'react';
import axios from 'axios';

function IdentifyRiskRules() {
  const [riskData, setRiskData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [threshold, setThreshold] = useState(30);
  const [totalAtRisk, setTotalAtRisk] = useState(0);

  const fetchRiskData = async (thresholdPct = threshold) => {
    try {
      setLoading(true);
      const response = await axios.post('/api/identify-risk', { thresholdPct });
      console.log("Risk data received:", response.data); // Debug log
      
      if (response.data.success) {
        // Use the 'data' field from the response, not 'customers'
        setRiskData(response.data.data || []);
        setTotalAtRisk(response.data.total_at_risk || 0);
      } else {
        setError(response.data.message || "Failed to process risk data");
      }
      setLoading(false);
    } catch (err) {
      console.error("Error fetching risk data:", err);
      setError(err.message || "Failed to load risk data");
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRiskData();
  }, []);

  const handleThresholdChange = (e) => {
    setThreshold(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchRiskData(threshold);
  };

  if (loading) return <div className="loading">Loading risk data...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (riskData.length === 0) return (
    <div className="no-data">
      <h2>Risk Identification</h2>
      <p>No customers at risk found with current threshold ({threshold}%).</p>
      <form onSubmit={handleSubmit} className="threshold-form">
        <div className="form-group">
          <label htmlFor="threshold">Threshold Percentage:</label>
          <input 
            type="number" 
            id="threshold" 
            value={threshold} 
            onChange={handleThresholdChange} 
            min="1" 
            max="100"
          />
          <button type="submit">Apply Threshold</button>
        </div>
      </form>
    </div>
  );

  return (
    <div className="risk-container">
      <h2>Risk Identification Results</h2>
      
      <form onSubmit={handleSubmit} className="threshold-form">
        <div className="form-group">
          <label htmlFor="threshold">Threshold Percentage:</label>
          <input 
            type="number" 
            id="threshold" 
            value={threshold} 
            onChange={handleThresholdChange} 
            min="1" 
            max="100"
          />
          <button type="submit">Apply Threshold</button>
        </div>
      </form>

      <div className="summary">
        <h3>Summary</h3>
        <p>Total customers at risk: {totalAtRisk}</p>
      </div>

      <div className="customers-list">
        <h3>At-Risk Customers</h3>
        {console.log("Rendering risk data:", riskData)}
        <table className="risk-table">
          <thead>
            <tr>
              <th>Client</th>
              <th>Last Period</th>
              <th>Last Purchase (Tons)</th>
              <th>Previous Avg (Tons)</th>
              <th>% Drop</th>
              <th>Drop (Tons)</th>
            </tr>
          </thead>
          <tbody>
            {riskData.map((customer, index) => (
              <tr key={index}>
                <td>{customer['Client']}</td>
                <td>{customer['Last Period']}</td>
                <td>{customer['Last Purchase (Tons)']}</td>
                <td>{customer['Previous Avg (Tons)']}</td>
                <td>{customer['% Drop']}</td>
                <td>{customer['Drop (Tons)']}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default IdentifyRiskRules;