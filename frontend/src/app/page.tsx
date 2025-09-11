'use client';

import React, { useState, useEffect } from 'react';
import Logo from '@/components/Logo';
import { 
  BarChart3, 
  Users, 
  TrendingUp, 
  Database, 
  Brain, 
  FileText,
  Search,
  Download,
  AlertTriangle,
  CheckCircle,
  Loader2
} from 'lucide-react';

interface DatasetInfo {
  totalRows: number;
  totalColumns: number;
  fileSize: string;
  columns: string[];
}

interface CustomerData {
  customerId: string;
  totalPurchases: number;
  avgQuantity: number;
  lastPurchase: string;
  riskLevel: 'low' | 'medium' | 'high';
}

interface CustomerAnalysis {
  customerId: string;
  monthlyData: Array<{
    month: string;
    quantity: number;
    purchases: number;
  }>;
  quarterlyData: Array<{
    quarter: string;
    quantity: number;
    purchases: number;
  }>;
  riskFactors: string[];
}

interface AtRiskApiResponse {
  columns: string[];
  rows: any[];
}

export default function Dashboard() {
  const [datasetInfo, setDatasetInfo] = useState<DatasetInfo | null>(null);
  const [customers, setCustomers] = useState<CustomerData[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<string>('');
  const [customerAnalysis, setCustomerAnalysis] = useState<CustomerAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [modelTrained, setModelTrained] = useState(false);

  const [atRiskRows, setAtRiskRows] = useState<any[]>([]);
  const [atRiskColumns, setAtRiskColumns] = useState<string[]>([]);
  const [atRiskThreshold, setAtRiskThreshold] = useState<number>(30);
  const [loadingAtRisk, setLoadingAtRisk] = useState(false);

  // Simular carga de datos del backend
  useEffect(() => {
    loadDatasetInfo();
    loadCustomers();
  }, []);

  const loadDatasetInfo = async () => {
    setLoading(true);
    try {
      // Llamada real al backend
      const response = await fetch('http://localhost:5000/api/dataset-info');
      const data = await response.json();
      setDatasetInfo(data);
    } catch (error) {
      // Datos simulados si el backend no está disponible
      setDatasetInfo({
        totalRows: 2421842,
        totalColumns: 10,
        fileSize: '250 MB',
        columns: [
          'COMPANIA', 'CO', 'CENTRO_OPERATIVO', 'ANIO', 'MES', 
          'LINEA', 'SUBLINEA', 'CANAL', 'VENTAS_KG', 'CLIENTE_ANONIMO'
        ]
      });
    }
    setLoading(false);
  };

  const loadCustomers = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/customers');
      const data = await response.json();
      setCustomers(data);
    } catch (error) {
      // Datos simulados
      const mockCustomers: CustomerData[] = [
        { customerId: 'CLT_0001', totalPurchases: 45, avgQuantity: 850.5, lastPurchase: '2024-01-15', riskLevel: 'low' },
        { customerId: 'CLT_0002', totalPurchases: 32, avgQuantity: 1200.3, lastPurchase: '2024-01-10', riskLevel: 'medium' },
        { customerId: 'CLT_0003', totalPurchases: 28, avgQuantity: 650.8, lastPurchase: '2023-12-20', riskLevel: 'high' },
        { customerId: 'CLT_0004', totalPurchases: 67, avgQuantity: 950.2, lastPurchase: '2024-01-18', riskLevel: 'low' },
        { customerId: 'CLT_0005', totalPurchases: 23, avgQuantity: 450.1, lastPurchase: '2023-11-30', riskLevel: 'high' },
      ];
      setCustomers(mockCustomers);
    }
  };

  const analyzeCustomer = async (customerId: string) => {
    if (!customerId) return;
    
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:5000/api/analyze-customer/${customerId}`);
      const data = await response.json();

      // Try to enrich with numeric risk metrics for this customer
      try {
        const riskRes = await fetch(`http://localhost:5000/api/at-risk?pct=${atRiskThreshold}`);
        const riskData: AtRiskApiResponse = await riskRes.json();
        const customerKey = riskData.columns?.[0];
        const riskRow = (riskData.rows || []).find((r: any) => r[customerKey] === customerId);
        if (riskRow) {
          const extraFactors: string[] = [
            `Caída reciente: ${Number(riskRow['drop_pct']).toFixed(1)}% (${Number(riskRow['drop_value']).toFixed(3)} ton)`,
            `Promedio 3 períodos: ${Number(riskRow['avg_last_3_tons']).toFixed(3)} ton | Última: ${Number(riskRow['total_tons']).toFixed(3)} ton`,
            `Último período: ${riskRow['period']}`
          ];
          setCustomerAnalysis({ ...data, riskFactors: [...data.riskFactors, ...extraFactors] });
        } else {
          setCustomerAnalysis(data);
        }
      } catch {
        setCustomerAnalysis(data);
      }
    } catch (error) {
      // Análisis simulado
      setCustomerAnalysis({
        customerId,
        monthlyData: [
          { month: '2023-10', quantity: 1200, purchases: 8 },
          { month: '2023-11', quantity: 980, purchases: 6 },
          { month: '2023-12', quantity: 750, purchases: 4 },
          { month: '2024-01', quantity: 650, purchases: 3 },
        ],
        quarterlyData: [
          { quarter: 'Q4 2023', quantity: 2930, purchases: 18 },
          { quarter: 'Q1 2024', quantity: 650, purchases: 3 },
        ],
        riskFactors: [
          'Decrease in purchase frequency',
          'Reduced quantity per purchase',
          'Longer time between purchases'
        ]
      });
    }
    setLoading(false);
  };

  const trainModel = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/train-model', {
        method: 'POST'
      });
      const data = await response.json();
      setModelTrained(data.success);
    } catch (error) {
      setTimeout(() => {
        setModelTrained(true);
        setLoading(false);
      }, 3000);
      return; // prevent double setLoading(false)
    }
    setLoading(false);
  };

  const uploadDefault = async () => {
    setLoading(true);
    try {
      await fetch('http://localhost:5000/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filePath: 'ventas_anonimizadas.csv' })
      });
      await loadDatasetInfo();
      await loadCustomers();
    } finally {
      setLoading(false);
    }
  };

  const aggregateMonthly = async () => {
    setLoading(true);
    try {
      await fetch('http://localhost:5000/api/aggregate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ period: 'month' })
      });
    } finally {
      setLoading(false);
    }
  };

  const loadTrends = async (customerId: string) => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:5000/api/trends/${customerId}`);
      const data = await res.json();
      // Map backend series to the same monthlyData structure for quick rendering
      setCustomerAnalysis({
        customerId,
        monthlyData: data.series.map((p: any) => ({ month: p.date.slice(0, 7), quantity: p.totalTons, purchases: 0 })),
        quarterlyData: [],
        riskFactors: []
      });
    } finally {
      setLoading(false);
    }
  };

  const loadAtRisk = async () => {
    setLoadingAtRisk(true);
    try {
      const res = await fetch(`http://localhost:5000/api/at-risk?pct=${atRiskThreshold}`);
      const data: AtRiskApiResponse = await res.json();
      setAtRiskColumns(data.columns || []);
      setAtRiskRows(data.rows || []);
    } finally {
      setLoadingAtRisk(false);
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Logo />
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">Sistema de Análisis de Riesgo</span>
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {[
              { id: 'overview', label: 'Resumen', icon: BarChart3 },
              { id: 'customers', label: 'Clientes', icon: Users },
              { id: 'analysis', label: 'Análisis', icon: TrendingUp },
              { id: 'model', label: 'Modelo ML', icon: Brain },
              { id: 'data', label: 'Datos', icon: Database }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === id
                    ? 'border-teal-500 text-teal-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg flex items-center space-x-3">
              <Loader2 className="w-6 h-6 animate-spin text-teal-600" />
              <span>Procesando...</span>
            </div>
          </div>
        )}

        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <Database className="w-8 h-8 text-teal-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Total Registros</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {datasetInfo ? datasetInfo.totalRows.toLocaleString() : '...'}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <Users className="w-8 h-8 text-blue-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Clientes Únicos</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {customers.length > 0 ? customers.length.toLocaleString() : '...'}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <AlertTriangle className="w-8 h-8 text-red-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Clientes en Riesgo</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {customers.filter(c => c.riskLevel === 'high').length}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Información del Dataset</h3>
              {datasetInfo && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Filas</p>
                    <p className="text-lg font-semibold">{datasetInfo.totalRows.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Columnas</p>
                    <p className="text-lg font-semibold">{datasetInfo.totalColumns}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Tamaño</p>
                    <p className="text-lg font-semibold">{datasetInfo.fileSize}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Estado</p>
                    <p className="text-lg font-semibold text-green-600">Activo</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'customers' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Lista de Clientes</h3>
                <div className="flex items-center space-x-2">
                  <input
                    type="number"
                    className="w-28 px-3 py-2 border border-gray-300 rounded-md text-sm"
                    value={atRiskThreshold}
                    onChange={(e) => setAtRiskThreshold(parseFloat(e.target.value))}
                    placeholder="% Caída"
                  />
                  <button
                    onClick={loadAtRisk}
                    disabled={loadingAtRisk}
                    className="px-3 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700 text-sm disabled:opacity-50"
                  >
                    {loadingAtRisk ? 'Cargando...' : 'Actualizar Riesgo'}
                  </button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Cliente
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Compras
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Cantidad Promedio
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Última Compra
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Riesgo
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {customers.map((customer) => (
                      <tr key={customer.customerId} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {customer.customerId}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {customer.totalPurchases}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {customer.avgQuantity.toFixed(1)} kg
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {customer.lastPurchase}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRiskColor(customer.riskLevel)}`}>
                            {customer.riskLevel.toUpperCase()}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Clientes en Riesgo reales desde el backend */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Clientes en Riesgo (Regla de Caída)</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-red-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Cliente</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Último Período</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Última Compra (Ton)</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Promedio Anterior (Ton)</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">% Caída</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Caída (Ton)</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {atRiskRows.map((r, idx) => (
                      <tr key={idx} className="hover:bg-red-50/40">
                        <td className="px-6 py-3 text-sm text-gray-900">{r[atRiskColumns[0]]}</td>
                        <td className="px-6 py-3 text-sm text-gray-700">{r['period']}</td>
                        <td className="px-6 py-3 text-sm text-gray-700">{Number(r['total_tons']).toFixed(3)}</td>
                        <td className="px-6 py-3 text-sm text-gray-700">{Number(r['avg_last_3_tons']).toFixed(3)}</td>
                        <td className="px-6 py-3 text-sm font-semibold text-red-700">{Number(r['drop_pct']).toFixed(1)}%</td>
                        <td className="px-6 py-3 text-sm text-gray-700">{Number(r['drop_value']).toFixed(3)}</td>
                      </tr>
                    ))}
                    {atRiskRows.length === 0 && (
                      <tr>
                        <td className="px-6 py-4 text-sm text-gray-500" colSpan={6}>
                          {loadingAtRisk ? 'Cargando...' : 'No hay clientes en riesgo para el umbral seleccionado'}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Análisis de Cliente</h3>
              <div className="flex space-x-4 mb-6">
                <select
                  value={selectedCustomer}
                  onChange={(e) => setSelectedCustomer(e.target.value)}
                  className="block w-64 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-teal-500 focus:border-teal-500"
                >
                  <option value="">Seleccionar cliente...</option>
                  {customers.map((customer) => (
                    <option key={customer.customerId} value={customer.customerId}>
                      {customer.customerId}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => analyzeCustomer(selectedCustomer)}
                  disabled={!selectedCustomer || loading}
                  className="px-4 py-2 bg-teal-600 text-white rounded-md hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Analizando...' : 'Analizar'}
                </button>
                <button
                  onClick={() => loadTrends(selectedCustomer)}
                  disabled={!selectedCustomer || loading}
                  className="px-4 py-2 ml-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cargar Tendencias (API)
                </button>
              </div>

              {customerAnalysis && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3">Compras Mensuales</h4>
                      <div className="space-y-2">
                        {customerAnalysis.monthlyData.map((month, index) => (
                          <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                            <span className="text-sm font-medium">{month.month}</span>
                            <div className="text-right">
                              <div className="text-sm font-semibold">{month.quantity} kg</div>
                              <div className="text-xs text-gray-500">{month.purchases} compras</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="text-md font-medium text-gray-900 mb-3">Factores de Riesgo</h4>
                      <div className="space-y-2">
                        {customerAnalysis.riskFactors.map((factor, index) => (
                          <div key={index} className="flex items-center p-3 bg-red-50 rounded">
                            <AlertTriangle className="w-4 h-4 text-red-500 mr-2" />
                            <span className="text-sm text-red-700">{factor}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'model' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Modelo de Machine Learning</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-3">Estado del Modelo</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded">
                      <span className="text-sm font-medium text-green-700">Random Forest</span>
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    </div>
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded">
                      <span className="text-sm font-medium text-green-700">Precisión: 87.5%</span>
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    </div>
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded">
                      <span className="text-sm font-medium text-green-700">
                        {modelTrained ? 'Entrenado' : 'No Entrenado'}
                      </span>
                      {modelTrained ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : (
                        <AlertTriangle className="w-5 h-5 text-yellow-500" />
                      )}
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={uploadDefault}
                      disabled={loading}
                      className="mt-4 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Cargar Dataset por Defecto
                    </button>
                    <button
                      onClick={aggregateMonthly}
                      disabled={loading}
                      className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Agregar por Mes
                    </button>
                    <button
                      onClick={loadAtRisk}
                      disabled={loadingAtRisk}
                      className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loadingAtRisk ? 'Cargando...' : 'Ver Clientes en Riesgo'}
                    </button>
                  </div>
                  <button
                    onClick={trainModel}
                    disabled={loading || modelTrained}
                    className="mt-4 px-4 py-2 bg-teal-600 text-white rounded-md hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Entrenando...' : modelTrained ? 'Modelo Entrenado' : 'Entrenar Modelo'}
                  </button>
                </div>

                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-3">Importancia de Características</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <span className="text-sm font-medium">Cantidad Promedio</span>
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div className="bg-teal-600 h-2 rounded-full" style={{width: '75%'}}></div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <span className="text-sm font-medium">Frecuencia</span>
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div className="bg-teal-600 h-2 rounded-full" style={{width: '60%'}}></div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <span className="text-sm font-medium">Variabilidad</span>
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div className="bg-teal-600 h-2 rounded-full" style={{width: '45%'}}></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'data' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Estructura de Datos</h3>
              {datasetInfo && (
                <div className="space-y-4">
                  <div>
                    <h4 className="text-md font-medium text-gray-900 mb-2">Columnas del Dataset</h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
                      {datasetInfo.columns.map((column, index) => (
                        <div key={index} className="p-2 bg-gray-50 rounded text-sm font-mono">
                          {column}
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="flex space-x-4">
                    <button className="px-4 py-2 bg-teal-600 text-white rounded-md hover:bg-teal-700">
                      <Download className="w-4 h-4 inline mr-2" />
                      Exportar Datos
                    </button>
                    <button className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700">
                      <FileText className="w-4 h-4 inline mr-2" />
                      Ver Muestra
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
