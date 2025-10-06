'use client';

import React, { useState, useEffect } from 'react';
import Logo from '@/components/Logo';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Database, GitCommit, BarChartHorizontal, Search, Brain, Loader2 } from 'lucide-react';

export default function Dashboard() {
    const [loading, setLoading] = useState(false);
    const [customers, setCustomers] = useState([]);
    const [step, setStep] = useState(0);

    const [uploadResult, setUploadResult] = useState(null);
    const [aggResult, setAggResult] = useState('');
    const [trendsData, setTrendsData] = useState([]);
    const [riskData, setRiskData] = useState([]);
    const [predictionData, setPredictionData] = useState(null);

    const [flagData, setFlagData] = useState([]);
    const [visibleCols, setVisibleCols] = useState<string[]>([]);
    const [searchId, setSearchId] = useState("");
    const [rowsLimit, setRowsLimit] = useState(10);

    const COLUMN_LABELS: Record<string, string> = {
        customer_id: "Customer ID",
        period: "Period",
        last_purchase: "Last Purchase (Tons)",
        avg_last_3_periods: "Avg Last 3 Periods (Tons)",
        drop_pct: "Drop (%)",
        drop_value: "Drop (Tons)",
        justification: "Justification",
        timestamp: "Generated At",
      };
      

    useEffect(() => {
        if (flagData.length > 0) {
          const cols = Object.keys(flagData[0]).filter(
            (c) => c !== "applied_pct_threshold" && c !== "applied_value_threshold"
          );
          setVisibleCols(cols);
        }
      }, [flagData]);
      

    const callApi = async (endpoint, options, errorMsg) => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:5000/api${endpoint}`, options);
            const data = await response.json();
            if (!response.ok || data.success === false) throw new Error(data.message || 'API Error');
            return data;
        } catch (error) {
            alert(`${errorMsg}: ${error.message}`);
            return null;
        } finally {
            setLoading(false);
        }
    };

    // --- Manejadores para cada Requerimiento Funcional ---
    const handleUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;
      
        setLoading(true); // ⬅️ activa el spinner
      
        const formData = new FormData();
        formData.append("file", file);
      
        try {
          const response = await fetch("http://localhost:5000/api/upload", {
            method: "POST",
            body: formData,
          });
      
          const data = await response.json();
          if (data.success) {
            setUploadResult(data.data);
            setCustomers(data.customers);
            setStep(1);
          } else {
            alert("Upload failed: " + data.message);
          }
        } catch (err) {
          alert("Error during upload: " + err.message);
        } finally {
          setLoading(false); // ⬅️ desactiva el spinner
        }
    };
      
      

    const handleAggregate = async () => {
        const period = prompt("Select period (month, quarter, year):", 'month') || 'month';
        const data = await callApi('/aggregate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ period }) }, 'Aggregation Failed');
        if (data) {
            setAggResult(data.message);
            setStep(2);
        }
    };

    const handleVisualize = async () => {
        const customerId = prompt("Enter the Customer ID to visualize:");
        if (!customerId) return;
        const startDate = prompt("Enter start date (YYYY-MM, optional):");
        const endDate = prompt("Enter end date (YYYY-MM, optional):");
        const chartType = prompt("Enter chart type ('line' or 'bar'):", 'line') || 'line';

        const payload = { customerId, startDate, endDate, chartType };
        const data = await callApi('/visualize', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }, 'Visualization Failed');
        if (data) {
            data.forEach(d => d.total_tons = parseFloat(d.total_tons));
            setTrendsData({ data, type: chartType });
        }
    };

    const handleIdentifyRisk = async () => {
        const thresholdType = prompt("Choose threshold type ('percentage' or 'value'):", 'percentage') || 'percentage';
        let payload = {};
        if (thresholdType === 'value') {
            const val = parseFloat(prompt("Enter the purchase drop threshold in Tons (e.g., 50):"));
            if (!isNaN(val)) payload.thresholdValue = val;
        } else {
            const pct = parseFloat(prompt("Enter the purchase drop threshold % (e.g., 30.0):", '30.0'));
            if (!isNaN(pct)) payload.thresholdPct = pct;
        }
        
        const response = await callApi('/identify-risk', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }, 'Risk Identification Failed');
        
        if (response) {
            // Usar directamente la propiedad 'data' que viene del backend
            if (response.data && Array.isArray(response.data)) {
                setRiskData(response.data);
            } 
            // Si no hay 'data', intentar encontrar un array en alguna propiedad
            else {
                let dataFound = false;
                
                for (const key of Object.keys(response)) {
                    if (Array.isArray(response[key]) && response[key].length > 0) {
                        setRiskData(response[key]);
                        dataFound = true;
                        break;
                    }
                }
                
                if (!dataFound) {
                    alert("No se encontraron clientes en riesgo con los criterios especificados.");
                }
            }
        }
    };

    const handleFlagDrops = async () => {
        const pct = parseFloat(prompt("Enter drop % threshold:", "30.0")) || 30.0;
        const val = parseFloat(prompt("Enter drop value threshold (tons):", "5.0")) || 5.0;
      
        const payload = { thresholdPct: pct, thresholdValue: val };
        const data = await callApi(
          "/flag-drops",
          { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) },
          "Flagging Failed"
        );
        if (data) setFlagData(data);
    };
      

    const handlePredictRisk = async () => {
        const data = await callApi('/predict-risk', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) }, 'Prediction Failed');
        if (data) {
            setPredictionData(data);
            alert('Modelo entrenado y predicciones generadas exitosamente.');
        }
    };

    const renderTable = (data) => {
        if (!data || !Array.isArray(data) || data.length === 0) {
            return <p className="text-sm text-black">No hay datos para mostrar.</p>;
        }
        
        if (typeof data[0] !== 'object' || data[0] === null) {
            return <p className="text-sm text-black">Error: Los datos no tienen el formato esperado.</p>;
        }
        
        const headers = Object.keys(data[0]);
        
        return (
            <div className="overflow-x-auto mt-4 text-black">
                <table className="min-w-full text-sm divide-y divide-gray-300">
                    <thead className="bg-gray-100">
                        <tr className="text-left text-xs font-semibold uppercase">
                            {headers.map((h) => (
                                <th key={h} className="px-4 py-2">
                                    {COLUMN_LABELS[h] || h.replace(/_/g, " ")}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {data.map((row, i) => (
                            <tr key={i}>
                                {headers.map(h => (
                                    <td key={h} className="px-4 py-2 whitespace-nowrap">
                                        {typeof row[h] === 'number' ? row[h].toFixed(2) : row[h]?.toString() || 'N/A'}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-gray-100">
            {loading && <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 text-white"><Loader2 className="w-8 h-8 animate-spin mr-3" /> Processing...</div>}
            <header className="bg-white shadow-sm border-b"><div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center py-4"><Logo /> <h1 className="text-xl font-semibold text-gray-800">Customer Churn Risk Analysis System</h1></div></header>
            
            <main className="max-w-7xl mx-auto p-8 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                    <label className="p-4 bg-blue-600 text-white text-center rounded shadow hover:bg-blue-700 cursor-pointer">1. Upload Data<input type="file" accept=".csv" onChange={handleUpload} className="hidden" /></label>
                    <button onClick={handleAggregate} disabled={step < 1} className="p-4 bg-green-600 text-white rounded shadow hover:bg-green-700 disabled:opacity-50">2. Aggregate Data</button>
                    <button onClick={handleVisualize} disabled={step < 2} className="p-4 bg-teal-600 text-white rounded shadow hover:bg-teal-700 disabled:opacity-50">3. Visualize Trends</button>
                    <button onClick={handleIdentifyRisk} disabled={step < 2} className="p-4 bg-amber-600 text-white rounded shadow hover:bg-amber-700 disabled:opacity-50">4. Identify Risk (Rules)</button>
                    <button onClick={handlePredictRisk} disabled={step < 2} className="p-4 bg-purple-600 text-white rounded shadow hover:bg-purple-700 disabled:opacity-50">5. Predict Risk (ML)</button>
                    <button onClick={handleFlagDrops} disabled={step < 2} className="p-4 bg-red-600 text-white rounded shadow hover:bg-red-700 disabled:opacity-50">6. Flag Drops</button>
                </div>
                <div className="bg-white p-6 rounded-lg shadow space-y-6">
                    {uploadResult && <div><h3 className="font-bold text-black">1. Upload Result:</h3><p className="text-sm text-black">Rows: {uploadResult.totalRows}, Columns: {uploadResult.totalColumns}</p></div>}
                    {aggResult && <div><h3 className="font-bold text-black">2. Aggregation Result:</h3><p className="text-sm text-black">{aggResult}</p></div>}
                    {trendsData.data && (
                        <div>
                            <h3 className="font-bold text-black">3. Customer Trend:</h3>
                            <div className="h-72">
                                <ResponsiveContainer width="100%" height="100%">
                                    {trendsData.type === 'bar' ? (
                                        <BarChart data={trendsData.data}><CartesianGrid /><XAxis dataKey="period_dt" /><YAxis /><Tooltip /><Bar dataKey="total_tons" fill="#2dd4bf" /></BarChart>
                                    ) : (
                                        <LineChart data={trendsData.data}><CartesianGrid /><XAxis dataKey="period_dt" /><YAxis /><Tooltip /><Line type="monotone" dataKey="total_tons" stroke="#2dd4bf" /></LineChart>
                                    )}
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}
                    
                    {riskData && riskData.length > 0 && 
                        <div>
                            <h3 className="font-bold text-black">4. At-Risk Customers (Rules-Based):</h3>
                            {renderTable(riskData)}
                        </div>
                    }
                    
                    {predictionData && (
                        <div>
                            <h3 className="font-bold text-black">5. Prediction Results (Random Forest):</h3>
                            <div className="text-sm text-black mt-2">
                                <h4 className="font-semibold">Evaluation Metrics:</h4>
                                <p>Accuracy: {(predictionData.evaluation.report.accuracy * 100).toFixed(2)}%</p>
                                <p>Precision (for Churn): {((predictionData.evaluation.report['1']?.precision ?? 0) * 100).toFixed(2)}%</p>
                                <p>Recall (for Churn): {((predictionData.evaluation.report['1']?.recall ?? 0) * 100).toFixed(2)}%</p>
                            </div>
                            <div className="mt-4"><h4 className="font-semibold text-black">High Churn Risk Customers:</h4>{renderTable(predictionData.predictions)}</div>
                        </div>
                    )}
                    {flagData.length > 0 && (
                        <div>
                            <h3 className="font-bold text-black">6. Significant Purchase Drops:</h3>
                            <p className="text-sm text-black mb-2">Applied Percent Threshold: {flagData[0].applied_pct_threshold}%</p>
                            <p className="text-sm text-black mb-2">Applied Value Threshold: {flagData[0].applied_value_threshold}</p>
                            {/* Filtros */}
                            <div className="my-2 space-y-2 text-black">
                                {/* Buscar por ID */}
                                <input type="text" placeholder="Search by Customer ID" value={searchId} onChange={(e) => setSearchId(e.target.value)} className="border p-1 rounded" />
                                {/* Selección de columnas */}
                                <div className="flex flex-wrap gap-2">
                                    {Object.keys(flagData[0])
                                    .filter((c) => c !== "applied_pct_threshold" && c !== "applied_value_threshold")
                                    .map((col) => (
                                        <label key={col} className="text-sm">
                                        <input type="checkbox" checked={visibleCols.includes(col)}
                                            onChange={() =>
                                            setVisibleCols((prev) =>
                                                prev.includes(col)
                                                ? prev.filter((c) => c !== col)
                                                : [
                                                    ...Object.keys(flagData[0]).filter(
                                                        (x) =>
                                                        x !== "applied_pct_threshold" &&
                                                        x !== "applied_value_threshold" &&
                                                        (prev.includes(x) || x === col)
                                                    ),
                                                    ]
                                            )
                                            }
                                        />
                                        {COLUMN_LABELS[col] || col}
                                        </label>
                                    ))}
                                </div>
                                {/* Límite de filas */}
                                <select value={rowsLimit} onChange={(e) => setRowsLimit(parseInt(e.target.value))} className="border p-1 rounded" >
                                    <option value={10}>10 rows</option>
                                    <option value={20}>20 rows</option>
                                    <option value={50}>50 rows</option>
                                    <option value={100}>100 rows</option>
                                    <option value={flagData.length}>All rows</option>
                                </select>
                            </div>
                            {/* Tabla filtrada */}
                            {renderTable(
                                flagData
                                    .filter((row) =>
                                    row.customer_id?.toLowerCase().includes(searchId.toLowerCase())
                                    )
                                    .slice(0, rowsLimit)
                                    .map((row) => {
                                    const filtered: any = {};
                                    visibleCols.forEach((col) => (filtered[col] = row[col]));
                                    return filtered;
                                    })
                            )}

                            <div className="mt-2">
                                <a href="http://localhost:5000/api/download-flags" className="inline-block px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600" > Download Flags (CSV) </a>
                            </div>
                        </div>
                        )}

                </div>
            </main>
        </div>
    );
}