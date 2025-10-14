'use client'

import React from 'react'

export default function AnalysisResults({ analysis }: { analysis: any }) {
  if (!analysis) {
    return (
      <div className="text-center text-gray-500 p-4">
        No hay resultados de análisis disponibles. Ejecuta la predicción nuevamente.
      </div>
    )
  }

  const {
    executive_summary = {},
    risk_segmentation = {},
    behavioral_patterns = [],
    feature_insights = [],
    actionable_recommendations = [],
    model_performance = [],
    temporal_analysis = [],
  } = analysis

  return (
    <div className="space-y-6">
      {/* 🧾 RESUMEN EJECUTIVO */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">🧾 Resumen Ejecutivo</h2>
        <p><strong>Granularidad:</strong> {executive_summary.granularidad}</p>
        <p><strong>Precisión del Modelo:</strong> {executive_summary.precision_modelo}</p>
        <p><strong>Clientes Evaluados:</strong> {executive_summary.clientes_evaluados}</p>
      </div>

      {/* ⚙️ SEGMENTACIÓN DE RIESGO */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">⚙️ Segmentación de Riesgo</h2>
        <ul className="list-disc ml-6">
          {Object.entries(risk_segmentation).map(([nivel, valor]: any) => (
            <li key={nivel}>
              {nivel.toUpperCase()}: {(valor * 100).toFixed(1)}%
            </li>
          ))}
        </ul>
      </div>

      {/* 📈 PATRONES DE COMPORTAMIENTO */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">📈 Patrones de Comportamiento</h2>
        {behavioral_patterns.length > 0 ? (
          <ul className="list-disc ml-6">
            {behavioral_patterns.map((p: any, i: number) => (
              <li key={i}>{p.pattern}</li>
            ))}
          </ul>
        ) : (
          <p>No se detectaron patrones significativos.</p>
        )}
      </div>

      {/* 💡 INSIGHTS DE VARIABLES */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">💡 Insights de Variables</h2>
        {feature_insights.length > 0 ? (
          <ul className="list-disc ml-6">
            {feature_insights.map((f: any, i: number) => (
              <li key={i}>
                <strong>{f.feature}</strong>: {f.impacto}
              </li>
            ))}
          </ul>
        ) : (
          <p>No hay insights disponibles.</p>
        )}
      </div>

      {/* 🎯 RECOMENDACIONES */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">🎯 Recomendaciones Accionables</h2>
        {actionable_recommendations.length > 0 ? (
          <ul className="list-disc ml-6">
            {actionable_recommendations.map((r: any, i: number) => (
              <li key={i}>
                <strong>{r.titulo}</strong>: {r.detalle}
              </li>
            ))}
          </ul>
        ) : (
          <p>No hay recomendaciones disponibles.</p>
        )}
      </div>

      {/* 📊 PERFORMANCE DEL MODELO */}
      {model_performance.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">📊 Performance del Modelo</h2>
          <table className="w-full text-sm text-left border">
            <thead>
              <tr className="bg-gray-100">
                <th className="px-2 py-1">Métrica</th>
                <th className="px-2 py-1">Precisión</th>
                <th className="px-2 py-1">Recall</th>
                <th className="px-2 py-1">F1</th>
              </tr>
            </thead>
            <tbody>
              {model_performance.map((m: any, i: number) => (
                <tr key={i} className="border-t">
                  <td className="px-2 py-1">{m.Metric}</td>
                  <td className="px-2 py-1">{m.Precision?.toFixed?.(2) ?? '-'}</td>
                  <td className="px-2 py-1">{m.Recall?.toFixed?.(2) ?? '-'}</td>
                  <td className="px-2 py-1">{m['F1-Score']?.toFixed?.(2) ?? '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
