# processing/analysis_reporter.py

import pandas as pd
import numpy as np
from typing import Optional

class AnalysisReporter:
    """Maneja el informe de tendencias de clientes (FR3) y la identificación de clientes en riesgo (FR4)."""

    def visualize_customer_trends(self, aggregated_df: pd.DataFrame, customer_col: str, customer_id: str, start_date_str: Optional[str] = None, end_date_str: Optional[str] = None) -> pd.DataFrame:
        """FR3: Filtra los datos agregados para un cliente específico y un rango de fechas."""
        print(f"Getting trend data for customer {customer_id}...")

        if aggregated_df.empty:
            return pd.DataFrame()

        customer_data = aggregated_df[aggregated_df[customer_col] == customer_id].copy()

        if customer_data.empty:
            return pd.DataFrame()

        # Convertir la columna de período a datetime para facilitar el filtrado
        customer_data['period_dt'] = pd.to_datetime(customer_data['period'])
        
        try:
            if start_date_str:
                start_date = pd.to_datetime(start_date_str)
                customer_data = customer_data[customer_data['period_dt'] >= start_date]
            if end_date_str:
                end_date = pd.to_datetime(end_date_str)
                customer_data = customer_data[customer_data['period_dt'] <= end_date]
        except ValueError:
            print("Warning: Invalid date format. Date filter will be ignored.")

        if customer_data.empty:
            return pd.DataFrame()

        return customer_data.sort_values('period_dt')

    def identify_at_risk_customers(self, aggregated_df: pd.DataFrame, customer_col: str, threshold_pct: Optional[float] = None, threshold_value: Optional[float] = None) -> pd.DataFrame:
        """FR4: Identifica clientes en riesgo basándose en una caída respecto a su promedio de los últimos 3 períodos."""
        print("Identifying at-risk customers...")
        if aggregated_df.empty:
            return pd.DataFrame()
            
        df_risk = aggregated_df.copy().sort_values([customer_col, 'period'])
        
        # Calcular un promedio móvil de 3 períodos, desplazado por 1 para representar la actividad anterior
        df_risk['avg_last_3_tons'] = df_risk.groupby(customer_col)['total_tons'].transform(lambda x: x.rolling(3, min_periods=1).mean().shift(1))
        
        # Obtener el último período de compra para cada cliente
        latest_purchases = df_risk.loc[df_risk.groupby(customer_col)['period'].idxmax()].copy()
        
        # Calcular métricas de caída
        latest_purchases['drop_pct'] = np.where(
            latest_purchases['avg_last_3_tons'] > 0, 
            ((latest_purchases['avg_last_3_tons'] - latest_purchases['total_tons']) / latest_purchases['avg_last_3_tons']) * 100, 
            0
        )
        latest_purchases['drop_value'] = latest_purchases['avg_last_3_tons'] - latest_purchases['total_tons']
        
        # Aplicar filtrado basado en umbrales
        if threshold_pct is not None:
            return latest_purchases[latest_purchases['drop_pct'] >= threshold_pct]
        if threshold_value is not None:
            return latest_purchases[latest_purchases['drop_value'] >= threshold_value]
            
        return pd.DataFrame()
