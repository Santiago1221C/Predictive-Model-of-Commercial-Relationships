# processing/flag_reporter.py

import pandas as pd
import numpy as np
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

class FlagReporter:
    """Clase para marcar y reportar clientes con caídas significativas."""
    
    def __init__(self):
        pass
    
    def flag_customers_with_drops(self, aggregated_df, customer_col, threshold_pct=30.0, threshold_value=None):
        """
        Marca clientes con caídas significativas en sus compras.
        
        Args:
            aggregated_df (DataFrame): Datos agregados
            customer_col (str): Columna de cliente
            threshold_pct (float): Umbral de porcentaje para marcar
            threshold_value (float): Umbral de valor para marcar
            
        Returns:
            dict: Clientes marcados y datos para reporte
        """
        try:
            print(f"Flagging customers with drops - Threshold: {threshold_pct}%, Value: {threshold_value}")
            
            # Ordenar por cliente y período
            df_sorted = aggregated_df.sort_values([customer_col, 'period_dt'])
            
            # Calcular diferencias período a período
            df_sorted['prev_quantity'] = df_sorted.groupby(customer_col)['total_quantity'].shift(1)
            df_sorted['quantity_change'] = df_sorted['total_quantity'] - df_sorted['prev_quantity']
            df_sorted['pct_change'] = (df_sorted['quantity_change'] / df_sorted['prev_quantity']) * 100
            
            # Identificar caídas significativas
            flagged_mask = pd.Series([False] * len(df_sorted))
            
            if threshold_pct is not None:
                flagged_mask |= (df_sorted['pct_change'] <= -threshold_pct)
            
            if threshold_value is not None:
                flagged_mask |= (df_sorted['quantity_change'] <= -threshold_value)
            
            # Si no se especificaron umbrales, usar valores por defecto
            if threshold_pct is None and threshold_value is None:
                flagged_mask = (df_sorted['pct_change'] <= -20) | (df_sorted['quantity_change'] <= -500)
            
            flagged_data = df_sorted[flagged_mask & df_sorted['prev_quantity'].notna()]
            
            # Preparar datos de salida
            flag_data = []
            for _, row in flagged_data.iterrows():
                flag_data.append({
                    'Client': row[customer_col],
                    'Period': str(row['period_dt']),
                    'Current Quantity (Tons)': round(row['total_quantity'] / 1000, 2),
                    'Previous Quantity (Tons)': round(row['prev_quantity'] / 1000, 2),
                    'Change (Tons)': round(row['quantity_change'] / 1000, 2),
                    'Change (%)': round(row['pct_change'], 2),
                    'Flag Reason': self._get_flag_reason(row, threshold_pct, threshold_value)
                })
            
            # Ordenar por mayor caída
            flag_data = sorted(flag_data, key=lambda x: x['Change (%)'])
            
            return {
                'success': True,
                'data': flag_data,
                'flagged_data': flagged_data,  # Para uso interno
                'total_flagged': len(flag_data),
                'flag_summary': {
                    'total_periods_analyzed': len(df_sorted),
                    'periods_flagged': len(flagged_data),
                    'unique_customers_flagged': flagged_data[customer_col].nunique() if len(flagged_data) > 0 else 0
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error marcando clientes: {str(e)}'}
    
    def _get_flag_reason(self, row, threshold_pct, threshold_value):
        """Determina la razón del marcado."""
        reasons = []
        
        if threshold_pct is not None and row['pct_change'] <= -threshold_pct:
            reasons.append(f"Caída >{threshold_pct}%")
        
        if threshold_value is not None and row['quantity_change'] <= -threshold_value:
            reasons.append(f"Caída >{threshold_value/1000:.1f} tons")
        
        if not reasons:
            if row['pct_change'] <= -20:
                reasons.append("Caída >20%")
            if row['quantity_change'] <= -500:
                reasons.append("Caída >0.5 tons")
        
        return "; ".join(reasons) if reasons else "Caída significativa"
