'use client';

import React, { useState } from 'react';
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

    const handleUpload = async () => {
        const filePath = prompt("Enter file path (or press Enter for 'ventas_anonimizadas.csv'):", 'ventas_anonimizadas.csv') || 'ventas_anonimizadas.csv';
        const data = await callApi('/upload', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ filePath }) }, 'Upload Failed');
        if (data) {
            setUploadResult(data.data);
            setCustomers(data.customers);
            setStep(1);
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
        const data = await callApi('/identify-risk', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }, 'Risk Identification Failed');
        if (data) setRiskData(data);
    };

    const handlePredictRisk = async () => {
        const data = await callApi('/predict-risk', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) }, 'Prediction Failed');
        if (data) {
            setPredictionData(data);
            alert('Modelo entrenado y predicciones generadas exitosamente.');
        }
    };

    const renderTable = (data) => {
        if (!data || data.length === 0) return <p className="text-sm text-black">No data to display.</p>;
        const headers = Object.keys(data[0]);
        return (
            <div className="overflow-x-auto mt-4 text-black">
                <table className="min-w-full text-sm divide-y divide-gray-300">
                    <thead className="bg-gray-100"><tr className="text-left text-xs font-semibold uppercase">{headers.map(h => <th key={h} className="px-4 py-2">{h}</th>)}</tr></thead>
                    <tbody className="bg-white divide-y divide-gray-200">{data.map((row, i) => <tr key={i}>{headers.map(h => <td key={h} className="px-4 py-2 whitespace-nowrap">{typeof row[h] === 'number' ? row[h].toFixed(4) : row[h]}</td>)}</tr>)}</tbody>
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
                    <button onClick={handleUpload} className="p-4 bg-blue-600 text-white rounded shadow hover:bg-blue-700">1. Upload Data</button>
                    <button onClick={handleAggregate} disabled={step < 1} className="p-4 bg-green-600 text-white rounded shadow hover:bg-green-700 disabled:opacity-50">2. Aggregate Data</button>
                    <button onClick={handleVisualize} disabled={step < 2} className="p-4 bg-teal-600 text-white rounded shadow hover:bg-teal-700 disabled:opacity-50">3. Visualize Trends</button>
                    <button onClick={handleIdentifyRisk} disabled={step < 2} className="p-4 bg-amber-600 text-white rounded shadow hover:bg-amber-700 disabled:opacity-50">4. Identify Risk (Rules)</button>
                    <button onClick={handlePredictRisk} disabled={step < 2} className="p-4 bg-purple-600 text-white rounded shadow hover:bg-purple-700 disabled:opacity-50">5. Predict Risk (ML)</button>
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
                    {riskData.length > 0 && <div><h3 className="font-bold text-black">4. At-Risk Customers (Rule-Based):</h3>{renderTable(riskData)}</div>}
                    {predictionData && (
                        <div>
                            <h3 className="font-bold text-black">5. Prediction Results (Random Forest):</h3>
                            {/* ---> LA SOLUCIÓN ESTÁ AQUÍ <--- */}
                            <div className="text-sm text-black mt-2">
                                <h4 className="font-semibold">Evaluation Metrics:</h4>
                                <p>Accuracy: {(predictionData.evaluation.report.accuracy * 100).toFixed(2)}%</p>
                                <p>Precision (for Churn): {((predictionData.evaluation.report['1']?.precision ?? 0) * 100).toFixed(2)}%</p>
                                <p>Recall (for Churn): {((predictionData.evaluation.report['1']?.recall ?? 0) * 100).toFixed(2)}%</p>
                            </div>
                            <div className="mt-4"><h4 className="font-semibold text-black">High Churn Risk Customers:</h4>{renderTable(predictionData.predictions)}</div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}