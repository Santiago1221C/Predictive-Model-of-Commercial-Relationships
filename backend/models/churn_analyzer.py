# models/churn_analyzer.py

import pandas as pd
import numpy as np
from typing import Dict, List

class ChurnAnalyzer:
    """Genera análisis automático y conclusiones sobre las predicciones de abandono."""
    
    def __init__(self, granularity: str = 'M'):
        self.granularity = granularity
        if granularity == 'M':
            self.granularity_name = 'mensual'
        else:
            self.granularity_name = 'trimestral'
    
    def generate_comprehensive_analysis(
        self, 
        predictions: List[Dict],
        model_metrics: Dict,
        feature_importances: Dict
    ) -> Dict:
        
        df_pred = pd.DataFrame(predictions)
        
        analysis = {
            'executive_summary': self._generate_executive_summary(df_pred, model_metrics),
            'risk_segmentation': self._segment_by_risk(df_pred),
            'behavioral_patterns': self._analyze_patterns(df_pred),
            'feature_insights': self._interpret_features(feature_importances),
            'actionable_recommendations': self._generate_recommendations(df_pred),
            'model_performance': self._format_model_metrics(model_metrics),
            'temporal_analysis': self._temporal_insights(df_pred)
        }
        
        return analysis
    
    def _generate_executive_summary(self, df: pd.DataFrame, metrics: Dict) -> Dict:
        """Resumen ejecutivo del análisis."""
        total_customers = len(df)
        high_risk = len(df[df['churn_probability'] >= 0.7])
        medium_risk = len(df[(df['churn_probability'] >= 0.4) & (df['churn_probability'] < 0.7)])
        low_risk = len(df[df['churn_probability'] < 0.4])
        
        accuracy = metrics.get('report', {}).get('accuracy', 0)
        
        summary = {
            'total_customers': total_customers,
            'high_risk_count': high_risk,
            'medium_risk_count': medium_risk,
            'low_risk_count': low_risk,
            'high_risk_percentage': round((high_risk / total_customers) * 100, 2),
            'model_accuracy': round(accuracy * 100, 2),
            'analysis_period': self.granularity_name,
            'main_conclusion': self._generate_main_conclusion(high_risk, total_customers)
        }
        
        return summary
    
    def _generate_main_conclusion(self, high_risk: int, total: int) -> str:
        """Genera la conclusión principal basada en el riesgo."""
        percentage = (high_risk / total) * 100
        
        if percentage >= 30:
            return (f"ALERTA CRÍTICA: {percentage:.1f}% de los clientes están en riesgo alto de abandono. " "Se requiere acción inmediata para retener estos clientes.")
        elif percentage >= 15:
            return (f"ATENCIÓN REQUERIDA: {percentage:.1f}% de los clientes muestran riesgo alto. " "Se recomienda implementar estrategias de retención focalizadas.")
        elif percentage >= 5:
            return (f"✓ SITUACIÓN MANEJABLE: {percentage:.1f}% en riesgo alto. " "Monitorear y aplicar acciones preventivas selectivas.")
        else:
            return (f"CARTERA SALUDABLE: Solo {percentage:.1f}% en riesgo alto. " "Mantener estrategias actuales de fidelización.")
    
    def _segment_by_risk(self, df: pd.DataFrame) -> Dict:
        """Segmenta clientes por nivel de riesgo."""
        df['risk_category'] = pd.cut(
            df['churn_probability'],
            bins=[0, 0.4, 0.7, 1.0],
            labels=['Bajo', 'Medio', 'Alto']
        )
        
        segmentation = {}
        for category in ['Alto', 'Medio', 'Bajo']:
            segment_df = df[df['risk_category'] == category]
            
            segmentation[category.lower()] = {
                'count': len(segment_df),
                'avg_probability': round(segment_df['churn_probability'].mean(), 3),
                'avg_inactivity_periods': round(segment_df['periods_since_last_purchase'].mean(), 1),
                'avg_current_tons': round(segment_df['total_tons'].mean(), 2),
                'top_customers': segment_df.nlargest(5, 'churn_probability')[
                    ['churn_probability', 'periods_since_last_purchase', 'total_tons']
                ].to_dict('records') if category == 'Alto' else []
            }
        
        return segmentation
    
    def _analyze_patterns(self, df: pd.DataFrame) -> Dict:
        """Identifica patrones de comportamiento."""
        patterns = {}
        
        # Patrón 1: Inactividad prolongada
        inactive = df[df['periods_since_last_purchase'] > 2]
        patterns['inactive_customers'] = {
            'count': len(inactive),
            'avg_churn_prob': round(inactive['churn_probability'].mean(), 3),
            'insight': (f"{len(inactive)} clientes llevan más de 2 períodos {self.granularity_name}es sin comprar. "
                    f"Probabilidad promedio de abandono: {inactive['churn_probability'].mean():.1%}")
        }
        
        # Patrón 2: Clientes con baja actividad reciente
        low_volume = df[df['total_tons'] < df['total_tons'].quantile(0.25)]
        patterns['low_volume_customers'] = {
            'count': len(low_volume),
            'avg_churn_prob': round(low_volume['churn_probability'].mean(), 3),
            'insight': (f"{len(low_volume)} clientes en el cuartil inferior de volumen. "
                    f"Riesgo promedio: {low_volume['churn_probability'].mean():.1%}")
        }
        
        # Patrón 3: Correlación inactividad-riesgo
        correlation = df['periods_since_last_purchase'].corr(df['churn_probability'])
        patterns['inactivity_correlation'] = {
            'coefficient': round(correlation, 3),
            'insight': (f"Correlación {'fuerte' if abs(correlation) > 0.7 else 'moderada' if abs(correlation) > 0.4 else 'débil'} "
                    f"entre inactividad y riesgo de abandono (r={correlation:.2f})")
        }
        
        return patterns
    
    def _interpret_features(self, importances: Dict) -> Dict:
        """Interpreta la importancia de las características."""
        sorted_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        
        interpretations = {
            'total_tons': 'Volumen de compra actual',
            'avg_tons_last_3': 'Promedio histórico de compras',
            'std_tons_last_3': 'Variabilidad en el comportamiento de compra',
            'periods_since_last_purchase': 'Tiempo desde última compra'
        }
        
        insights = []
        for feature, importance in sorted_features[:3]:
            readable_name = interpretations.get(feature, feature)
            insights.append({
                'feature': feature,
                'readable_name': readable_name,
                'importance': round(importance, 3),
                'interpretation': self._get_feature_interpretation(feature, importance)
            })
        
        return {
            'top_features': insights,
            'main_driver': sorted_features[0][0],
            'main_driver_interpretation': self._get_feature_interpretation(
                sorted_features[0][0], 
                sorted_features[0][1]
            )
        }
    
    def _get_feature_interpretation(self, feature: str, importance: float) -> str:
        """Genera interpretación textual de cada característica."""
        interpretations = {
            'periods_since_last_purchase': 
                f"El tiempo transcurrido desde la última compra es el predictor más fuerte "
                f"({importance:.1%}), indicando que la recencia es crítica para identificar abandono.",
            'total_tons': 
                f"El volumen actual de compra tiene un impacto del {importance:.1%}, "
                f"sugiriendo que clientes con bajo volumen están en mayor riesgo.",
            'avg_tons_last_3': 
                f"El promedio histórico representa {importance:.1%} de la predicción, "
                f"mostrando que el comportamiento pasado es un buen indicador.",
            'std_tons_last_3': 
                f"La variabilidad en compras contribuye {importance:.1%}, "
                f"indicando que la inconsistencia puede señalar inestabilidad en la relación."
        }
        
        return interpretations.get(feature, f"Contribuye {importance:.1%} a la predicción.")
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[Dict]:
        """Genera recomendaciones accionables por segmento."""
        recommendations = []
        
        # Para clientes de alto riesgo
        high_risk = df[df['churn_probability'] >= 0.7]
        if len(high_risk) > 0:
            recommendations.append({
                'priority': 'ALTA',
                'segment': 'Clientes en Riesgo Alto',
                'count': len(high_risk),
                'actions': [
                    'Contacto directo inmediato con gerente de cuenta',
                    'Oferta personalizada o descuento de reactivación',
                    'Encuesta para identificar motivos de insatisfacción',
                    'Plan de recuperación con incentivos especiales'
                ],
                'expected_impact': 'Recuperación potencial de hasta 40% de clientes en riesgo'
            })
        
        # Para clientes de riesgo medio
        medium_risk = df[(df['churn_probability'] >= 0.4) & (df['churn_probability'] < 0.7)]
        if len(medium_risk) > 0:
            recommendations.append({
                'priority': 'MEDIA',
                'segment': 'Clientes en Riesgo Medio',
                'count': len(medium_risk),
                'actions': [
                    'Campaña de email marketing con ofertas relevantes',
                    'Recordatorios de productos complementarios',
                    'Programa de puntos o beneficios por lealtad',
                    'Seguimiento proactivo mensual'
                ],
                'expected_impact': 'Prevención de 60% de posibles abandonos'
            })
        
        # Para clientes de bajo riesgo
        low_risk = df[df['churn_probability'] < 0.4]
        if len(low_risk) > 0:
            recommendations.append({
                'priority': 'BAJA',
                'segment': 'Clientes Estables',
                'count': len(low_risk),
                'actions': [
                    'Mantener comunicación regular',
                    'Programas de referidos o embajadores de marca',
                    'Oportunidades de upselling/cross-selling',
                    'Encuestas de satisfacción periódicas'
                ],
                'expected_impact': 'Maximizar lifetime value y generar nuevos referidos'
            })
        
        return recommendations
    
    def _format_model_metrics(self, metrics: Dict) -> Dict:
        """Formatea las métricas del modelo de forma legible."""
        report = metrics.get('report', {})
        
        return {
            'accuracy': round(report.get('accuracy', 0) * 100, 2),
            'precision_churn': round(report.get('1', {}).get('precision', 0) * 100, 2),
            'recall_churn': round(report.get('1', {}).get('recall', 0) * 100, 2),
            'f1_score_churn': round(report.get('1', {}).get('f1-score', 0) * 100, 2),
            'confusion_matrix': metrics.get('confusion_matrix', []),
            'interpretation': self._interpret_model_performance(report)
        }
    
    def _interpret_model_performance(self, report: Dict) -> str:
        """Interpreta el rendimiento del modelo."""
        accuracy = report.get('accuracy', 0)
        f1_churn = report.get('1', {}).get('f1-score', 0)
        
        if accuracy >= 0.85 and f1_churn >= 0.75:
            return "Excellent: The model has high accuracy and balance for identifying at-risk customers."
        elif accuracy >= 0.75 and f1_churn >= 0.60:
            return "✓ Good: The model is reliable for making business decisions."
        elif accuracy >= 0.65:
            return "Acceptable: The model works but could be improved with more data or adjustments."
        else:
            return "Needs improvement: Consider more historical data or additional feature engineering."
    
    def _temporal_insights(self, df: pd.DataFrame) -> Dict:
        """Análisis de patrones temporales."""
        return {
            'avg_inactivity': round(df['periods_since_last_purchase'].mean(), 1),
            'max_inactivity': int(df['periods_since_last_purchase'].max()),
            'customers_active_current_period': len(df[df['periods_since_last_purchase'] == 0]),
            'customers_inactive_1plus': len(df[df['periods_since_last_purchase'] >= 1]),
            'insight': (f"Promedio de inactividad: {df['periods_since_last_purchase'].mean():.1f} "
                    f"períodos {self.granularity_name}es. "
                    f"{len(df[df['periods_since_last_purchase'] >= 1])} clientes no compraron "
                    f"en el último período.")
        }