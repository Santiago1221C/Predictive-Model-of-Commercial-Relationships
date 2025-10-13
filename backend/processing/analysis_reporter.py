# processing/analysis_reporter.py

import pandas as pd
import numpy as np
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

class AnalysisReporter:
    """Clase para generar reportes de análisis de riesgo."""
    
    def __init__(self):
        pass
    
    def identify_at_risk_customers(self, aggregated_df, customer_col, threshold_pct=None, threshold_value=None):
        """
        Identifica clientes en riesgo basado en caída de compras.
        Retorna los 10 clientes con mayor riesgo.
        
        Args:
            aggregated_df (DataFrame): Datos agregados por período
            customer_col (str): Columna de cliente
            threshold_pct (float): Umbral de porcentaje de caída
            threshold_value (float): Umbral de valor absoluto de caída
            
        Returns:
            dict: Lista de los 10 clientes en mayor riesgo
        """
        try:
            print(f"Identifying at-risk customers with thresholds - Percentage: {threshold_pct}%, Value: {threshold_value}")
            
            # Ordenar datos por cliente y período
            df_sorted = aggregated_df.sort_values([customer_col, 'period_dt'])
            
            # Obtener los últimos 2 períodos para cada cliente para calcular caída
            customer_latest = df_sorted.groupby(customer_col).tail(2)
            
            # Calcular caídas para cada cliente
            risk_analysis = []
            
            for customer in df_sorted[customer_col].unique():
                customer_data = df_sorted[df_sorted[customer_col] == customer].sort_values('period_dt')
                
                if len(customer_data) < 2:
                    continue  # Necesitamos al menos 2 períodos
                
                # Obtener último y penúltimo período
                latest = customer_data.iloc[-1]
                previous = customer_data.iloc[-2]
                
                # Calcular promedios históricos (excluyendo último período)
                historical_data = customer_data.iloc[:-1]
                historical_avg = historical_data['total_quantity'].mean()
                
                if historical_avg <= 0:
                    continue
                
                # Calcular métricas de riesgo
                current_quantity = latest['total_quantity']
                quantity_drop = historical_avg - current_quantity
                drop_percentage = (quantity_drop / historical_avg) * 100
                
                # Calcular tendencia (correlación con tiempo)
                if len(customer_data) > 2:
                    x = np.arange(len(customer_data))
                    y = customer_data['total_quantity'].values
                    trend = np.corrcoef(x, y)[0, 1] if len(set(y)) > 1 else 0
                else:
                    trend = 0
                
                risk_analysis.append({
                    'customer': customer,
                    'current_quantity': current_quantity,
                    'historical_avg': historical_avg,
                    'quantity_drop': quantity_drop,
                    'drop_percentage': drop_percentage,
                    'trend': trend,
                    'last_period': str(latest['period_dt']),
                    'periods_count': len(customer_data)
                })
            
            if len(risk_analysis) == 0:
                return {'success': True, 'data': []}
            
            # Convertir a DataFrame para facilitar filtrado
            risk_df = pd.DataFrame(risk_analysis)
            
            # Aplicar filtros basados en umbrales
            at_risk_customers = risk_df.copy()
            
            if threshold_pct is not None:
                at_risk_customers = at_risk_customers[at_risk_customers['drop_percentage'] >= threshold_pct]
                print(f"After percentage filter ({threshold_pct}%): {len(at_risk_customers)} customers")
            
            if threshold_value is not None:
                at_risk_customers = at_risk_customers[at_risk_customers['quantity_drop'] >= threshold_value]
                print(f"After value filter ({threshold_value}): {len(at_risk_customers)} customers")
            
            # Si no se especificaron umbrales, usar valores por defecto
            if threshold_pct is None and threshold_value is None:
                # Usar 10% de caída o tendencia negativa como umbrales por defecto
                at_risk_customers = at_risk_customers[
                    (at_risk_customers['drop_percentage'] >= 10) | 
                    (at_risk_customers['trend'] <= -0.3)
                ]
                print(f"Using default thresholds (10% drop or negative trend): {len(at_risk_customers)} customers")
            
            # Ordenar por mayor riesgo y tomar top 10
            at_risk_customers['risk_score'] = (
                at_risk_customers['drop_percentage'] * 0.6 + 
                abs(at_risk_customers['trend']) * 100 * 0.4
            )
            
            at_risk_customers = at_risk_customers.sort_values('risk_score', ascending=False).head(10)
            
            # Preparar datos de salida
            risk_data = []
            for _, row in at_risk_customers.iterrows():
                risk_data.append({
                    'Client': row['customer'],
                    'Last Period': row['last_period'],
                    'Current (Tons)': round(row['current_quantity'] / 1000, 2),
                    'Historical Avg (Tons)': round(row['historical_avg'] / 1000, 2),
                    'Drop (%)': round(row['drop_percentage'], 2),
                    'Drop (Tons)': round(row['quantity_drop'] / 1000, 2),
                    'Trend': round(row['trend'], 3),
                    'Risk Score': round(row['risk_score'], 2)
                })
            
            print(f"Returning top 10 at-risk customers out of {len(risk_df)} analyzed")
            
            return {
                'success': True,
                'data': risk_data,
                'total_at_risk': len(risk_data),
                'analysis_summary': {
                    'total_customers_analyzed': len(risk_df),
                    'customers_at_risk': len(risk_data),
                    'risk_percentage': round((len(at_risk_customers) / len(risk_df)) * 100, 2) if len(risk_df) > 0 else 0
                }
            }
            
        except Exception as e:
            error_msg = f'Error en análisis de riesgo: {str(e)}'
            print(f"❌ {error_msg}")
            return {'success': False, 'message': error_msg}