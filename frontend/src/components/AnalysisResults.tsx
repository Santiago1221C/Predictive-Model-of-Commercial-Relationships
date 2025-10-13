// src/components/AnalysisResults.tsx
'use client';

import React, { useState } from 'react';

interface AnalysisResultsProps {
  data: any;
}

export default function AnalysisResults({ data }: AnalysisResultsProps) {
  const [activeTab, setActiveTab] = useState<'summary' | 'segmentation' | 'patterns' | 'recommendations' | 'predictions'>('summary');
  
  const { analysis, predictions_formatted, evaluation_report, granularity_name } = data;

  if (!analysis) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800">No hay datos de análisis disponibles</p>
      </div>
    );
  }

  const { executive_summary, risk_segmentation, behavioral_patterns, actionable_recommendations, feature_insights, model_performance } = analysis;

  // Función helper para obtener estilos según nivel de riesgo
  const getRiskStyles = (level: string) => {
    const styles = {
      alto: {
        bg: 'bg-red-50',
        border: 'border-red-200',
        text: 'text-red-700',
        badge: 'bg-red-200 text-red-800'
      },
      medio: {
        bg: 'bg-yellow-50',
        border: 'border-yellow-200',
        text: 'text-yellow-700',
        badge: 'bg-yellow-200 text-yellow-800'
      },
      bajo: {
        bg: 'bg-green-50',
        border: 'border-green-200',
        text: 'text-green-700',
        badge: 'bg-green-200 text-green-800'
      }
    };
    return styles[level as keyof typeof styles] || styles.bajo;
  };

  const getPriorityStyles = (priority: string) => {
    const styles = {
      ALTA: {
        bg: 'bg-red-50',
        border: 'border-red-300',
        badge: 'bg-red-200 text-red-800',
        impact: 'bg-blue-50 border-blue-200 text-blue-800'
      },
      MEDIA: {
        bg: 'bg-yellow-50',
        border: 'border-yellow-300',
        badge: 'bg-yellow-200 text-yellow-800',
        impact: 'bg-blue-50 border-blue-200 text-blue-800'
      },
      BAJA: {
        bg: 'bg-green-50',
        border: 'border-green-300',
        badge: 'bg-green-200 text-green-800',
        impact: 'bg-blue-50 border-blue-200 text-blue-800'
      }
    };
    return styles[priority as keyof typeof styles] || styles.BAJA;
  };

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="flex border-b border-gray-200 overflow-x-auto">
          {[
            { key: 'summary', label: '📊 Resumen', icon: '📊' },
            { key: 'segmentation', label: '🎯 Segmentación', icon: '🎯' },
            { key: 'patterns', label: '🔍 Patrones', icon: '🔍' },
            { key: 'recommendations', label: '💡 Recomendaciones', icon: '💡' },
            { key: 'predictions', label: '📈 Predicciones', icon: '📈' },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`px-6 py-3 font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.key
                  ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {/* Summary Tab */}
          {activeTab === 'summary' && (
            <div className="space-y-6">
              <div className="flex items-start space-x-4">
                <span className="text-4xl">📊</span>
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-gray-800 mb-2">
                    Resumen Ejecutivo - Análisis {granularity_name}
                  </h2>
                  <div className={`p-4 rounded-lg ${
                    executive_summary.high_risk_percentage >= 30 ? 'bg-red-50 border border-red-200' :
                    executive_summary.high_risk_percentage >= 15 ? 'bg-yellow-50 border border-yellow-200' :
                    'bg-green-50 border border-green-200'
                  }`}>
                    <p className="text-gray-800 font-medium">{executive_summary.main_conclusion}</p>
                  </div>
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <div className="text-3xl font-bold text-blue-700">
                    {executive_summary.total_customers}
                  </div>
                  <div className="text-sm text-blue-600 mt-1">Total Clientes</div>
                </div>
                <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                  <div className="text-3xl font-bold text-red-700">
                    {executive_summary.high_risk_count}
                  </div>
                  <div className="text-sm text-red-600 mt-1">
                    Riesgo Alto ({executive_summary.high_risk_percentage}%)
                  </div>
                </div>
                <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                  <div className="text-3xl font-bold text-yellow-700">
                    {executive_summary.medium_risk_count}
                  </div>
                  <div className="text-sm text-yellow-600 mt-1">Riesgo Medio</div>
                </div>
                <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                  <div className="text-3xl font-bold text-green-700">
                    {executive_summary.low_risk_count}
                  </div>
                  <div className="text-sm text-green-600 mt-1">Riesgo Bajo</div>
                </div>
              </div>

              {/* Model Performance */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h3 className="font-semibold text-gray-800 mb-2">🎯 Rendimiento del Modelo</h3>
                <p className="text-sm text-gray-600 mb-3">{model_performance.interpretation}</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div>
                    <div className="text-xs text-gray-500">Precisión</div>
                    <div className="text-lg font-bold text-gray-800">{model_performance.accuracy}%</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Precision (Churn)</div>
                    <div className="text-lg font-bold text-gray-800">{model_performance.precision_churn}%</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Recall (Churn)</div>
                    <div className="text-lg font-bold text-gray-800">{model_performance.recall_churn}%</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">F1-Score (Churn)</div>
                    <div className="text-lg font-bold text-gray-800">{model_performance.f1_score_churn}%</div>
                  </div>
                </div>
              </div>

              {/* Feature Insights */}
              <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                <h3 className="font-semibold text-gray-800 mb-2">🔑 Factores Clave de Predicción</h3>
                <p className="text-sm text-gray-600 mb-3">{feature_insights.main_driver_interpretation}</p>
                <div className="space-y-2">
                  {feature_insights.top_features.map((feature: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">{feature.readable_name}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-purple-600 h-2 rounded-full"
                            style={{ width: `${feature.importance * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-600 w-12 text-right">
                          {(feature.importance * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Segmentation Tab */}
          {activeTab === 'segmentation' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">🎯 Segmentación por Nivel de Riesgo</h2>
              
              {['alto', 'medio', 'bajo'].map((level) => {
                const segment = risk_segmentation[level];
                const styles = getRiskStyles(level);
                
                return (
                  <div key={level} className={`${styles.bg} rounded-lg p-6 border ${styles.border}`}>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-bold capitalize text-gray-800">
                        Riesgo {level.charAt(0).toUpperCase() + level.slice(1)}
                      </h3>
                      <span className={`text-2xl font-bold ${styles.text}`}>
                        {segment.count} clientes
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div>
                        <div className="text-xs text-gray-600">Prob. Promedio</div>
                        <div className="text-lg font-semibold text-gray-800">
                          {(segment.avg_probability * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-600">Inactividad Promedio</div>
                        <div className="text-lg font-semibold text-gray-800">
                          {segment.avg_inactivity_periods.toFixed(1)} períodos
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-600">Volumen Promedio</div>
                        <div className="text-lg font-semibold text-gray-800">
                          {segment.avg_current_tons.toFixed(2)} tons
                        </div>
                      </div>
                    </div>

                    {level === 'alto' && segment.top_customers && segment.top_customers.length > 0 && (
                      <div className="mt-4">
                        <h4 className="font-semibold text-gray-800 mb-2">Top 5 Clientes Críticos:</h4>
                        <div className="overflow-x-auto">
                          <table className="min-w-full text-sm">
                            <thead className="bg-gray-100">
                              <tr>
                                <th className="px-3 py-2 text-left">Probabilidad</th>
                                <th className="px-3 py-2 text-left">Períodos Inactivo</th>
                                <th className="px-3 py-2 text-left">Último Volumen</th>
                              </tr>
                            </thead>
                            <tbody>
                              {segment.top_customers.slice(0, 5).map((customer: any, idx: number) => (
                                <tr key={idx} className="border-t">
                                  <td className="px-3 py-2 font-medium">
                                    {(customer.churn_probability * 100).toFixed(1)}%
                                  </td>
                                  <td className="px-3 py-2">{customer.periods_since_last_purchase}</td>
                                  <td className="px-3 py-2">{customer.total_tons.toFixed(2)} tons</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Patterns Tab */}
          {activeTab === 'patterns' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">🔍 Patrones de Comportamiento</h2>
              
              {Object.entries(behavioral_patterns).map(([key, pattern]: [string, any]) => (
                <div key={key} className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                  <div className="flex items-start space-x-4">
                    <span className="text-3xl">📉</span>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-800 mb-2 capitalize">
                        {key.replace(/_/g, ' ')}
                      </h3>
                      <div className="bg-white rounded p-3 mb-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-gray-600">Clientes afectados:</span>
                          <span className="font-bold text-blue-700">{pattern.count}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">Prob. churn promedio:</span>
                          <span className="font-bold text-blue-700">
                            {(pattern.avg_churn_prob * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-700">{pattern.insight}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Recommendations Tab */}
          {activeTab === 'recommendations' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">💡 Recomendaciones Accionables</h2>
              
              {actionable_recommendations.map((rec: any, idx: number) => {
                const styles = getPriorityStyles(rec.priority);
                
                return (
                  <div key={idx} className={`${styles.bg} rounded-lg p-6 border-2 ${styles.border}`}>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-bold text-gray-800">{rec.segment}</h3>
                      <span className={`px-4 py-1 rounded-full text-sm font-bold ${styles.badge}`}>
                        Prioridad {rec.priority}
                      </span>
                    </div>
                    
                    <div className="bg-white rounded-lg p-4 mb-4">
                      <div className="text-sm text-gray-600">Clientes en este segmento:</div>
                      <div className="text-2xl font-bold text-gray-800">{rec.count}</div>
                    </div>

                    <h4 className="font-semibold text-gray-800 mb-2">📋 Acciones Recomendadas:</h4>
                    <ul className="space-y-2 mb-4">
                      {rec.actions.map((action: string, actionIdx: number) => (
                        <li key={actionIdx} className="flex items-start">
                          <span className="text-green-600 mr-2 mt-1">✓</span>
                          <span className="text-gray-700">{action}</span>
                        </li>
                      ))}
                    </ul>

                    <div className={`rounded p-3 border ${styles.impact}`}>
                      <div className="text-xs font-medium mb-1">Impacto Esperado:</div>
                      <div className="text-sm">{rec.expected_impact}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Predictions Tab */}
          {activeTab === 'predictions' && predictions_formatted && (
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">📈 Predicciones Detalladas por Cliente</h2>
              
              <div className="overflow-x-auto">
                <table className="min-w-full bg-white border border-gray-200">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-4 py-2 text-left text-sm font-semibold">Cliente</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">Prob. Abandono</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">Períodos Inactivo</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">Último Volumen (tons)</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">Nivel Riesgo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {predictions_formatted.slice(0, 20).map((pred: any, idx: number) => {
                      const prob = parseFloat(pred.churn_probability_formatted);
                      const riskLevel = prob >= 70 ? 'Alto' : prob >= 40 ? 'Medio' : 'Bajo';
                      const riskStyles = prob >= 70 ? 'bg-red-100 text-red-800' : prob >= 40 ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800';
                      const probColor = prob >= 70 ? 'text-red-700' : prob >= 40 ? 'text-yellow-700' : 'text-green-700';
                      
                      // Obtener el ID del cliente (primera propiedad que no sea las métricas)
                      const customerKey = Object.keys(pred).find(key => 
                        !['churn_probability', 'churn_probability_formatted', 'periods_since_last_purchase', 'total_tons'].includes(key)
                      ) || Object.keys(pred)[0];
                      const customerId = pred[customerKey];
                      
                      return (
                        <tr key={idx} className="border-t hover:bg-gray-50">
                          <td className="px-4 py-2 font-medium">{String(customerId)}</td>
                          <td className="px-4 py-2">
                            <span className={`font-bold ${probColor}`}>
                              {pred.churn_probability_formatted}
                            </span>
                          </td>
                          <td className="px-4 py-2">{pred.periods_since_last_purchase}</td>
                          <td className="px-4 py-2">{pred.total_tons}</td>
                          <td className="px-4 py-2">
                            <span className={`px-2 py-1 rounded text-xs font-bold ${riskStyles}`}>
                              {riskLevel}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              
              {predictions_formatted.length > 20 && (
                <p className="text-sm text-gray-600 text-center mt-4">
                  Mostrando 20 de {predictions_formatted.length} clientes. Los clientes están ordenados por probabilidad de abandono.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}