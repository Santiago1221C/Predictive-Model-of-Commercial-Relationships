# processing/analysis_reporter.py

import pandas as pd
import numpy as np
from typing import Optional

class AnalysisReporter:
    """Maneja el informe de tendencias de clientes (FR3) y la identificación de clientes en riesgo (FR4)."""

    # [Código de visualize_customer_trends() sin cambios]
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
    # -------------------------------------------------------------------------------------

    def identify_at_risk_customers(self, aggregated_df: pd.DataFrame, customer_col: str, threshold_pct: Optional[float] = None, threshold_value: Optional[float] = None) -> pd.DataFrame:
        """FR4: Identifica clientes en riesgo basándose en una caída respecto a su promedio de los últimos 3 períodos."""
        print(f"Identifying at-risk customers with thresholds - Percentage: {threshold_pct}%, Value: {threshold_value}")
        
        if aggregated_df.empty:
            print("No aggregated data available")
            return pd.DataFrame()
            
        # Verificar que existan las columnas necesarias
        required_cols = [customer_col, 'period', 'total_tons']
        if not all(col in aggregated_df.columns for col in required_cols):
            print(f"Missing required columns. Available: {list(aggregated_df.columns)}")
            return pd.DataFrame()
            
        df_risk = aggregated_df.copy().sort_values([customer_col, 'period'])
        
        # Asegurar que period sea datetime para ordenamiento correcto
        if not pd.api.types.is_datetime64_any_dtype(df_risk['period']):
            df_risk['period'] = pd.to_datetime(df_risk['period'])
        
        # Calcular promedio móvil de 3 períodos (excluyendo el período actual)
        df_risk['avg_last_3_tons'] = df_risk.groupby(customer_col)['total_tons'].transform(
            lambda x: x.shift(1).rolling(window=3, min_periods=1).mean()
        )
        
        # Obtener el último período de compra para cada cliente
        latest_purchases = df_risk.loc[df_risk.groupby(customer_col)['period'].idxmax()].copy()
        
        print(f"Total customers found: {len(latest_purchases)}")
        
        # Filtrar clientes que tienen datos históricos válidos
        # Un cliente necesita al menos 2 períodos para tener un promedio anterior
        customers_with_history = df_risk.groupby(customer_col).size() >= 2
        valid_customers = customers_with_history[customers_with_history].index
        
        latest_purchases = latest_purchases[
            latest_purchases[customer_col].isin(valid_customers) & 
            latest_purchases['avg_last_3_tons'].notna() & 
            (latest_purchases['avg_last_3_tons'] > 0)
        ]
        
        if latest_purchases.empty:
            print("No customers with sufficient history found")
            return pd.DataFrame()
        
        print(f"Customers with valid history: {len(latest_purchases)}")
        
        # Calcular métricas de caída
        latest_purchases['drop_value'] = latest_purchases['avg_last_3_tons'] - latest_purchases['total_tons']
        latest_purchases['drop_pct'] = (latest_purchases['drop_value'] / latest_purchases['avg_last_3_tons']) * 100
        
        # Redondear valores para mejor presentación
        latest_purchases['avg_last_3_tons'] = latest_purchases['avg_last_3_tons'].round(2)
        latest_purchases['drop_pct'] = latest_purchases['drop_pct'].round(2)
        latest_purchases['drop_value'] = latest_purchases['drop_value'].round(2)
        
        # Aplicar filtros de riesgo
        df_filtered = latest_purchases.copy()
        
        # Solo considerar clientes con caída positiva (compra actual menor al promedio)
        df_filtered = df_filtered[df_filtered['drop_value'] > 0]
        
        if df_filtered.empty:
            print("No customers showing decline in purchases")
            return pd.DataFrame()
        
        # Aplicar umbrales si se proporcionan
        if threshold_pct is not None and threshold_pct > 0:
            df_filtered = df_filtered[df_filtered['drop_pct'] >= threshold_pct]
            print(f"After percentage filter ({threshold_pct}%): {len(df_filtered)} customers")
            
        if threshold_value is not None and threshold_value > 0:
            df_filtered = df_filtered[df_filtered['drop_value'] >= threshold_value]
            print(f"After value filter ({threshold_value}): {len(df_filtered)} customers")
        
        # Si no hay umbrales específicos, usar valores por defecto razonables
        if (threshold_pct is None or threshold_pct <= 0) and (threshold_value is None or threshold_value <= 0):
            # Por defecto: caída de al menos 10% o 1 tonelada
            df_filtered = df_filtered[
                (df_filtered['drop_pct'] >= 10) | (df_filtered['drop_value'] >= 1.0)
            ]
            print(f"Using default thresholds (10% or 1 ton): {len(df_filtered)} customers")
        
        return df_filtered.sort_values('drop_pct', ascending=False)