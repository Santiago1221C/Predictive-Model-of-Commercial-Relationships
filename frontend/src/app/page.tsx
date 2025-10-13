'use client';

import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Database, GitCommit, BarChartHorizontal, Search, Brain, Loader2, Upload, TrendingUp, AlertTriangle, Target, FileText, Flag, Download, Users } from 'lucide-react';

export default function Dashboard() {
    const [loading, setLoading] = useState(false);
    const [activeSection, setActiveSection] = useState(null);
    const [step, setStep] = useState(0);

    const [uploadResult, setUploadResult] = useState(null);
    const [aggResult, setAggResult] = useState('');
    const [trendsData, setTrendsData] = useState([]);
    const [riskData, setRiskData] = useState([]);
    const [predictionData, setPredictionData] = useState(null);
    const [flaggedData, setFlaggedData] = useState([]);
    const [availableCustomers, setAvailableCustomers] = useState([]);

    // Verificar si hay datos cargados al iniciar
    useEffect(() => {
        checkDefaultData();
    }, []);

    const callApi = async (endpoint, options, errorMsg) => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:5000${endpoint}`, options);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error(errorMsg, error);
            alert(`${errorMsg}: ${error.message}`);
            return null;
        } finally {
            setLoading(false);
        }
    };

    const checkDefaultData = async () => {
        try {
            // Intentar cargar datos por defecto del archivo ventas_anonimizadas.csv
            const result = await callApi('/api/upload', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ use_default: true })
            }, 'Error loading default data');
            
            if (result && result.success) {
                setUploadResult({ 
                    totalRows: result.total_rows, 
                    totalColumns: result.total_columns,
                    source: 'ventas_anonimizadas.csv (predeterminado)'
                });
                setAvailableCustomers(result.customers || []);
                setStep(1);
            }
        } catch (error) {
            console.log('No se pudieron cargar los datos predeterminados');
        }
    };

    const loadCustomers = async () => {
        const result = await callApi('/api/customers', { method: 'GET' }, 'Error loading customers');
        if (result && result.success) {
            setAvailableCustomers(result.customers);
        }
    };

    const handleUpload = async () => {
        // Mostrar opción de usar archivo predeterminado o subir nuevo
        const useDefault = confirm(
            "¿Desea usar el archivo predeterminado 'ventas_anonimizadas.csv'?\n\n" +
            "Presione 'Aceptar' para usar el archivo predeterminado\n" +
            "Presione 'Cancelar' para subir un archivo personalizado"
        );

        if (useDefault) {
            // Usar archivo predeterminado
            const result = await callApi('/api/upload', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ use_default: true })
            }, 'Error loading default data');
            
            if (result && result.success) {
                setUploadResult({ 
                    totalRows: result.total_rows, 
                    totalColumns: result.total_columns,
                    source: 'ventas_anonimizadas.csv (predeterminado)'
                });
                setAvailableCustomers(result.customers || []);
                setStep(1);
                setActiveSection('upload');
            }
        } else {
            // Subir archivo personalizado
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.csv';
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (!file) return;
                
                const formData = new FormData();
                formData.append('file', file);
                
                const result = await callApi('/api/upload', { method: 'POST', body: formData }, 'Upload failed');
                if (result && result.success) {
                    setUploadResult({ 
                        totalRows: result.total_rows, 
                        totalColumns: result.total_columns,
                        source: file.name
                    });
                    setAvailableCustomers(result.customers || []);
                    setStep(1);
                    setActiveSection('upload');
                }
            };
            input.click();
        }
    };

    const handleAggregate = async () => {
        const period = prompt("Enter aggregation period (month/quarter/year):", 'month') || 'month';
        const result = await callApi('/api/aggregate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ period }) }, 'Aggregation failed');
        if (result && result.success) {
            setAggResult(`Aggregation successful: ${result.total_records} records | Period: ${period}`);
            setStep(2);
            setActiveSection('aggregate');
        }
    };

    const handleVisualize = async () => {
        // Cargar clientes si no están disponibles
        if (availableCustomers.length === 0) {
            await loadCustomers();
        }

        // Crear una modal para ingresar cliente manualmente
        const customerSelection = await showCustomerInputModal();
        if (!customerSelection) return;

        const chartType = prompt("Choose chart type ('line' or 'bar'):", 'line') || 'line';
        const result = await callApi('/api/visualize', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify({ 
                chart_type: chartType,
                customer_id: customerSelection 
            }) 
        }, 'Visualization failed');
        
        if (result && result.success) {
            setTrendsData({ 
                data: result.data, 
                type: chartType, 
                customer: customerSelection 
            });
            setActiveSection('visualize');
        }
    };

    const showCustomerInputModal = () => {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
            
            const content = document.createElement('div');
            content.className = 'bg-white p-6 rounded-lg max-w-lg w-full mx-4';
            
            // Generar algunos ejemplos de clientes
            const exampleCustomers = availableCustomers.slice(0, 5);
            
            content.innerHTML = `
                <h3 class="text-lg font-bold mb-4 text-gray-800">Ingresar ID del Cliente</h3>
                
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        ID del Cliente:
                    </label>
                    <input 
                        type="text" 
                        id="customerInput" 
                        placeholder="Ingrese el ID del cliente (ej: Cliente_001)" 
                        class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                </div>
                
                <div class="mb-4 p-4 bg-gray-50 rounded-lg">
                    <p class="text-sm font-medium text-gray-700 mb-2">Ejemplos de clientes disponibles:</p>
                    <div class="flex flex-wrap gap-2">
                        ${exampleCustomers.map(customer => 
                            `<button class="example-btn px-3 py-1 bg-blue-100 text-blue-800 text-xs rounded-full hover:bg-blue-200 transition-colors" data-customer="${customer}">
                                ${customer}
                            </button>`
                        ).join('')}
                    </div>
                    <p class="text-xs text-gray-500 mt-2">
                        Total de ${availableCustomers.length} clientes disponibles
                    </p>
                </div>
                
                <div class="flex space-x-3">
                    <button 
                        id="confirmBtn" 
                        class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                    >
                        Confirmar
                    </button>
                    <button 
                        id="cancelBtn" 
                        class="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
                    >
                        Cancelar
                    </button>
                </div>
            `;
            
            modal.appendChild(content);
            document.body.appendChild(modal);
            
            const customerInput = content.querySelector('#customerInput');
            const confirmBtn = content.querySelector('#confirmBtn');
            const cancelBtn = content.querySelector('#cancelBtn');
            
            // Auto-focus en el input
            customerInput.focus();
            
            // Event listeners para los botones de ejemplo
            content.querySelectorAll('.example-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    customerInput.value = btn.dataset.customer;
                    customerInput.focus();
                });
            });
            
            // Función para confirmar
            const confirmCustomer = () => {
                const customerValue = customerInput.value.trim();
                if (!customerValue) {
                    alert('Por favor ingrese un ID de cliente');
                    customerInput.focus();
                    return;
                }
                
                resolve(customerValue);
                document.body.removeChild(modal);
            };
            
            // Event listeners
            confirmBtn.addEventListener('click', confirmCustomer);
            
            cancelBtn.addEventListener('click', () => {
                resolve(null);
                document.body.removeChild(modal);
            });
            
            // Permitir Enter para confirmar
            customerInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    confirmCustomer();
                }
            });
            
            // Permitir Escape para cancelar
            modal.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    resolve(null);
                    document.body.removeChild(modal);
                }
            });
        });
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
        
        const response = await callApi('/api/identify-risk', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }, 'Risk Identification Failed');
        
        if (response && response.success) {
            setRiskData(response.data || []);
            setActiveSection('risk');
        }
    };

    const handlePredictRisk = async () => {
        const result = await callApi('/api/predict-risk', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) }, 'ML Prediction failed');
        if (result && result.success) {
            setPredictionData(result);
            setActiveSection('predict');
        }
    };

    const handleFlagDrops = async () => {
        const thresholdType = prompt("Choose threshold type ('percentage' or 'value'):", 'percentage') || 'percentage';
        let payload = {};
        if (thresholdType === 'value') {
            const val = parseFloat(prompt("Enter the purchase drop threshold in Tons (e.g., 50):"));
            if (!isNaN(val)) payload.thresholdValue = val;
        } else {
            const pct = parseFloat(prompt("Enter the purchase drop threshold % (e.g., 30.0):", '30.0'));
            if (!isNaN(pct)) payload.thresholdPct = pct;
        }
        
        const response = await callApi('/api/flag-drops', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }, 'Flag Drops Failed');
        
        if (response && response.success) {
            const top10Flagged = response.data.slice(0, 10);
            setFlaggedData(top10Flagged);
            setActiveSection('flagged');
        }
    };

    const handleDownloadFlags = async () => {
        try {
            setLoading(true);
            const response = await fetch('http://localhost:5000/api/download-flags');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'flagged_customers.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            alert('Archivo descargado exitosamente: flagged_customers.csv');
        } catch (error) {
            console.error('Download failed:', error);
            alert(`Error al descargar: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const renderTable = (data) => {
        if (!data || !Array.isArray(data) || data.length === 0) {
            return <p className="text-sm text-gray-600">No hay datos para mostrar.</p>;
        }
        
        if (typeof data[0] !== 'object' || data[0] === null) {
            return <p className="text-sm text-red-600">Error: Los datos no tienen el formato esperado.</p>;
        }
        
        const headers = Object.keys(data[0]);
        
        return (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                {headers.map(h => (
                                    <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        {h}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {data.map((row, i) => (
                                <tr key={i} className="hover:bg-gray-50">
                                    {headers.map(h => (
                                        <td key={h} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {typeof row[h] === 'number' ? row[h].toFixed(2) : row[h]?.toString() || 'N/A'}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    const menuItems = [
        { id: 'upload', label: 'Cargar Datos', icon: Upload, action: handleUpload, disabled: false },
        { id: 'aggregate', label: 'Agregar Datos', icon: Database, action: handleAggregate, disabled: step < 1 },
        { id: 'visualize', label: 'Visualizar Tendencias', icon: TrendingUp, action: handleVisualize, disabled: step < 2 },
        { id: 'risk', label: 'Identificar Riesgo', icon: AlertTriangle, action: handleIdentifyRisk, disabled: step < 2 },
        { id: 'predict', label: 'Predecir Riesgo (ML)', icon: Target, action: handlePredictRisk, disabled: step < 2 },
        { id: 'flagged', label: 'Marcar Caídas', icon: Flag, action: handleFlagDrops, disabled: step < 2 },
    ];

    const renderContent = () => {
        if (!activeSection) {
            return (
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                        <div className="mb-8 flex justify-center">
                            <img 
                                src="/grupo_bios.png" 
                                alt="Grupo Bios" 
                                className="opacity-30 transition-opacity duration-300"
                                style={{ maxWidth: '300px', height: 'auto' }}
                            />
                        </div>
                        <h2 className="text-3xl font-bold text-gray-400 mb-4">
                            Sistema de Análisis de Riesgo de Abandono de Clientes
                        </h2>
                        <p className="text-gray-400 text-lg mb-6">
                            Seleccione una opción del menú lateral para comenzar
                        </p>
                        {step >= 1 && (
                            <div className="bg-green-50 border border-green-200 rounded-lg p-4 max-w-md mx-auto">
                                <p className="text-green-800 text-sm">
                                    <FileText className="inline w-4 h-4 mr-2" />
                                    Datos cargados: {uploadResult?.source}
                                </p>
                                <p className="text-green-700 text-xs mt-1">
                                    <Users className="inline w-3 h-3 mr-1" />
                                    {availableCustomers.length} clientes disponibles
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            );
        }

        return (
            <div className="flex-1 p-8 overflow-auto">
                <div className="max-w-7xl mx-auto space-y-8">
                    {activeSection === 'upload' && uploadResult && (
                        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                                <Upload className="mr-3 text-[#00657F]" size={24} />
                                Resultado de Carga de Datos
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                <div className="bg-gray-50 p-4 rounded-lg">
                                    <p className="text-sm font-medium text-gray-600">Archivo Fuente</p>
                                    <p className="text-lg font-bold text-[#00657F] break-words">{uploadResult.source}</p>
                                </div>
                                <div className="bg-gray-50 p-4 rounded-lg">
                                    <p className="text-sm font-medium text-gray-600">Total de Filas</p>
                                    <p className="text-2xl font-bold text-[#00657F]">{uploadResult.totalRows.toLocaleString()}</p>
                                </div>
                                <div className="bg-gray-50 p-4 rounded-lg">
                                    <p className="text-sm font-medium text-gray-600">Total de Columnas</p>
                                    <p className="text-2xl font-bold text-[#00657F]">{uploadResult.totalColumns}</p>
                                </div>
                                <div className="bg-gray-50 p-4 rounded-lg">
                                    <p className="text-sm font-medium text-gray-600">Clientes</p>
                                    <p className="text-2xl font-bold text-[#AACF00]">{availableCustomers.length}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeSection === 'aggregate' && aggResult && (
                        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                                <Database className="mr-3 text-[#00657F]" size={24} />
                                Resultado de Agregación
                            </h3>
                            <p className="text-gray-700 bg-gray-50 p-4 rounded-lg">{aggResult}</p>
                        </div>
                    )}

                    {activeSection === 'visualize' && trendsData.data && (
                        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                            <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
                                <TrendingUp className="mr-3 text-[#00657F]" size={24} />
                                Tendencias del Cliente: {trendsData.customer}
                            </h3>
                            <div className="h-96">
                                <ResponsiveContainer width="100%" height="100%">
                                    {trendsData.type === 'bar' ? (
                                        <BarChart data={trendsData.data}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="period_dt" />
                                            <YAxis />
                                            <Tooltip />
                                            <Bar dataKey="total_tons" fill="#AACF00" />
                                        </BarChart>
                                    ) : (
                                        <LineChart data={trendsData.data}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="period_dt" />
                                            <YAxis />
                                            <Tooltip />
                                            <Line type="monotone" dataKey="total_tons" stroke="#00657F" strokeWidth={3} />
                                        </LineChart>
                                    )}
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}

                    {activeSection === 'risk' && riskData && riskData.length > 0 && (
                        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                            <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
                                <AlertTriangle className="mr-3 text-[#00657F]" size={24} />
                                Top 10 Clientes en Mayor Riesgo
                            </h3>
                            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                                <p className="text-sm text-red-800">
                                    <strong>Alerta:</strong> Se muestran los 10 clientes con mayor riesgo de abandono
                                </p>
                            </div>
                            {renderTable(riskData)}
                        </div>
                    )}

                    {activeSection === 'predict' && predictionData && (
                        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                            <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
                                <Target className="mr-3 text-[#00657F]" size={24} />
                                Top 10 Predicciones de Riesgo (Random Forest)
                            </h3>
                            <div className="grid grid-cols-3 gap-4 mb-6">
                                <div className="bg-gray-50 p-4 rounded-lg text-center">
                                    <p className="text-sm font-medium text-gray-600">Precisión</p>
                                    <p className="text-2xl font-bold text-[#00657F]">
                                        {(predictionData.evaluation.report.accuracy * 100).toFixed(2)}%
                                    </p>
                                </div>
                                <div className="bg-gray-50 p-4 rounded-lg text-center">
                                    <p className="text-sm font-medium text-gray-600">Precisión (Churn)</p>
                                    <p className="text-2xl font-bold text-[#AACF00]">
                                        {((predictionData.evaluation.report['1']?.precision ?? 0) * 100).toFixed(2)}%
                                    </p>
                                </div>
                                <div className="bg-gray-50 p-4 rounded-lg text-center">
                                    <p className="text-sm font-medium text-gray-600">Recall (Churn)</p>
                                    <p className="text-2xl font-bold text-[#AACF00]">
                                        {((predictionData.evaluation.report['1']?.recall ?? 0) * 100).toFixed(2)}%
                                    </p>
                                </div>
                            </div>
                            <h4 className="text-lg font-semibold text-gray-800 mb-4">
                                Top 10 Clientes con Mayor Probabilidad de Abandono
                            </h4>
                            {renderTable(predictionData.predictions)}
                        </div>
                    )}

                    {activeSection === 'flagged' && flaggedData && flaggedData.length > 0 && (
                        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                            <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
                                <Flag className="mr-3 text-[#00657F]" size={24} />
                                Top 10 Clientes Marcados por Caídas Significativas
                            </h3>
                            <div className="mb-4 p-4 bg-orange-50 border border-orange-200 rounded-lg flex justify-between items-center">
                                <div>
                                    <p className="text-sm text-orange-800">
                                        <strong>Información:</strong> Se muestran los 10 clientes con mayores caídas significativas en compras
                                    </p>
                                </div>
                                <button
                                    onClick={handleDownloadFlags}
                                    className="flex items-center space-x-2 bg-[#00657F] text-white px-4 py-2 rounded-lg hover:bg-[#00657F]/80 transition-colors"
                                >
                                    <Download size={16} />
                                    <span>Descargar CSV</span>
                                </button>
                            </div>
                            {renderTable(flaggedData)}
                        </div>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="flex h-screen bg-gray-100">
            {/* Loading Overlay */}
            {loading && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-lg flex items-center space-x-3">
                        <Loader2 className="w-6 h-6 animate-spin text-[#00657F]" />
                        <span className="text-gray-800">Procesando...</span>
                    </div>
                </div>
            )}

            {/* Sidebar */}
            <div className="w-80 bg-[#00657F] text-white flex flex-col">
                {/* Header con Logo */}
                <div className="p-6 border-b border-[#00657F]/20">
                    <div className="flex items-center space-x-3 mb-2">
                        <img 
                            src="/grupo_bios.png" 
                            alt="Grupo Bios" 
                            className="w-10 h-10 object-contain bg-white rounded-lg p-1"
                        />
                        <div>
                            <span className="text-xl font-bold">Grupo Bios</span>
                        </div>
                    </div>
                    <p className="text-sm text-blue-200">Sistema de Análisis de Riesgo</p>
                </div>

                {/* Menu Items */}
                <nav className="flex-1 p-4 space-y-2">
                    {menuItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = activeSection === item.id;
                        
                        return (
                            <button
                                key={item.id}
                                onClick={item.action}
                                disabled={item.disabled}
                                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-all duration-200 ${
                                    isActive 
                                        ? 'bg-[#AACF00] text-[#00657F] shadow-lg' 
                                        : item.disabled
                                        ? 'text-blue-300 cursor-not-allowed opacity-50'
                                        : 'text-white hover:bg-[#00657F]/80 hover:bg-white/10'
                                }`}
                            >
                                <Icon size={20} />
                                <span className="font-medium">{item.label}</span>
                                {item.disabled && (
                                    <span className="ml-auto text-xs bg-blue-300/20 px-2 py-1 rounded">
                                        Bloqueado
                                    </span>
                                )}
                            </button>
                        );
                    })}
                </nav>

                {/* Footer */}
                <div className="p-4 border-t border-[#00657F]/20">
                    <p className="text-xs text-blue-200 text-center">
                        © 2025 Grupo Bios - Análisis Predictivo
                    </p>
                </div>
            </div>

            {/* Main Content */}
            {renderContent()}
        </div>
    );
}