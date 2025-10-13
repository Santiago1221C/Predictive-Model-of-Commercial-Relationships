// src/components/ChurnPrediction.tsx
'use client';

import React, { useState } from 'react';
import AnalysisResults from './AnalysisResults';

interface PredictionResponse {
    success: boolean;
    message?: string;
    granularity?: string;
    granularity_name?: string;
    predictions?: any[];
    predictions_formatted?: any[];
    evaluation?: any;
    evaluation_report?: any[];
    feature_importances?: any;
    analysis?: {
    executive_summary: any;
    risk_segmentation: any;
    behavioral_patterns: any;
    feature_insights: any;
    actionable_recommendations: any[];
    model_performance: any;
    temporal_analysis: any;
    };
}

export default function ChurnPrediction() {
    const [granularity, setGranularity] = useState<'M' | 'Q'>('M');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<PredictionResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handlePredict = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
        const response = await fetch('http://localhost:5000/api/predict-risk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        body: JSON.stringify({ granularity }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Error en la predicción');
        }

        if (data.success) {
            setResult(data);
        } else {
            setError(data.message || 'La predicción falló');
        }
    } catch (err: any) {
        setError(err.message || 'Error de conexión con el servidor');
        console.error('Error:', err);
    } finally {
        setLoading(false);
    }
    };

    return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
            🔮 Predicción de Abandono de Clientes
            </h1>
            <p className="text-gray-600">
            Sistema de Machine Learning con análisis automático y granularidad temporal
            </p>
        </div>

        {/* Control Panel */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
            ⚙️ Configuración de Análisis
            </h2>

            <div className="space-y-4">
            {/* Granularity Selector */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                Seleccionar Granularidad Temporal:
                </label>
                <div className="flex gap-4">
                <button
                    onClick={() => setGranularity('M')}
                    className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all ${
                    granularity === 'M'
                        ? 'bg-blue-600 text-white shadow-lg'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                >
                    📅 Mensual (M)
                    <div className="text-xs mt-1 opacity-80">
                    Análisis mes a mes
                    </div>
                </button>
                <button
                    onClick={() => setGranularity('Q')}
                    className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all ${
                    granularity === 'Q'
                        ? 'bg-blue-600 text-white shadow-lg'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                >
                    📊 Trimestral (Q)
                    <div className="text-xs mt-1 opacity-80">
                    Análisis por trimestres
                    </div>
                </button>
                </div>
            </div>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                <strong>Granularidad seleccionada:</strong>{' '}
                {granularity === 'M' ? 'Mensual' : 'Trimestral'}
                </p>
                <p className="text-xs text-blue-600 mt-1">
                {granularity === 'M'
                    ? 'Ideal para productos de alta rotación con ciclos de compra cortos'
                    : 'Ideal para productos de baja frecuencia o contratos a largo plazo'}
                </p>
            </div>

            {/* Execute Button */}
            <button
                onClick={handlePredict}
                disabled={loading}
                className={`w-full py-4 px-6 rounded-lg font-bold text-lg transition-all ${
                loading
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl'
                }`}
            >
                {loading ? (
                <span className="flex items-center justify-center">
                    <svg
                    className="animate-spin h-5 w-5 mr-3"
                    viewBox="0 0 24 24"
                    >
                    <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                    />
                    <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                    </svg>
                    Entrenando modelo y generando análisis...
                </span>
                ) : (
                '🚀 Ejecutar Predicción y Análisis'
                )}
            </button>
            </div>
        </div>

        {/* Error Message */}
        {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-start">
                <span className="text-2xl mr-3">❌</span>
                <div>
                <h3 className="font-semibold text-red-800">Error</h3>
                <p className="text-red-600 text-sm mt-1">{error}</p>
                </div>
            </div>
            </div>
        )}

        {/* Results */}
        {result && result.success && (
            <AnalysisResults data={result} />
        )}

        {/* Instructions */}
        {!result && !loading && !error && (
            <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">
            📋 Instrucciones
            </h3>
            <ol className="list-decimal list-inside space-y-2 text-gray-600">
                <li>Selecciona la granularidad temporal deseada (Mensual o Trimestral)</li>
                <li>Haz clic en "Ejecutar Predicción y Análisis"</li>
                <li>El sistema procesará los datos y generará:
                <ul className="list-disc list-inside ml-6 mt-1 text-sm">
                    <li>Predicciones de abandono por cliente</li>
                    <li>Resumen ejecutivo</li>
                    <li>Segmentación por nivel de riesgo</li>
                    <li>Patrones de comportamiento</li>
                    <li>Recomendaciones accionables</li>
                </ul>
                </li>
            </ol>
            </div>
        )}
        </div>
    </div>
    );
}