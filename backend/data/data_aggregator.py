# data/data_aggregator.py

import pandas as pd
import numpy as np
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

class DataAggregator:
    """Clase para agregar datos por diferentes períodos."""
    
    def __init__(self):
        self.supported_periods = ['month', 'quarter', 'year']
    
    def aggregate_by_period(self, df, customer_col, date_col, quantity_col, period='month'):
        """
        Agrega datos por cliente y período especificado.
        
        Args:
            df (DataFrame): Datos originales
            customer_col (str): Nombre de la columna de cliente
            date_col (str): Nombre de la columna de fecha
            quantity_col (str): Nombre de la columna de cantidad
            period (str): Período de agregación
            
        Returns:
            dict: Resultado con datos agregados
        """
        try:
            print(f"Aggregating data by {period}")
            print(f"Input data shape: {df.shape}")
            print(f"Columns: Customer={customer_col}, Date={date_col}, Quantity={quantity_col}")
            
            if period not in self.supported_periods:
                return {
                    'success': False, 
                    'message': f'Período no soportado: {period}. Use: {self.supported_periods}'
                }
            
            # Crear copia del dataframe
            agg_df = df.copy()
            
            # Asegurar que la fecha sea datetime
            agg_df[date_col] = pd.to_datetime(agg_df[date_col])
            
            # Crear columna de período
            if period == 'month':
                agg_df['period_dt'] = agg_df[date_col].dt.to_period('M')
            elif period == 'quarter':
                agg_df['period_dt'] = agg_df[date_col].dt.to_period('Q')
            elif period == 'year':
                agg_df['period_dt'] = agg_df[date_col].dt.to_period('Y')
            
            print(f"Period column created successfully")
            
            # Agregar por cliente y período
            aggregated = agg_df.groupby([customer_col, 'period_dt']).agg({
                quantity_col: ['sum', 'count', 'mean']
            }).reset_index()
            
            # Aplanar columnas múltiples
            aggregated.columns = [
                customer_col, 
                'period_dt', 
                'total_quantity', 
                'transaction_count', 
                'avg_quantity'
            ]
            
            print(f"Data aggregated successfully. Shape: {aggregated.shape}")
            
            # Convertir period_dt a string para serialización
            aggregated['period_dt'] = aggregated['period_dt'].astype(str)
            
            # Ordenar por cliente y período
            aggregated = aggregated.sort_values([customer_col, 'period_dt'])
            
            print(f"Unique customers: {aggregated[customer_col].nunique()}")
            print(f"Unique periods: {aggregated['period_dt'].nunique()}")
            
            return {
                'success': True,
                'aggregated_data': aggregated,
                'total_records': len(aggregated),
                'unique_customers': aggregated[customer_col].nunique(),
                'period': period,
                'message': f'Datos agregados exitosamente por {period}'
            }
            
        except Exception as e:
            error_msg = f'Error agregando datos: {str(e)}'
            print(f"❌ {error_msg}")
            return {'success': False, 'message': error_msg}
    
    def calculate_customer_metrics(self, aggregated_df, customer_col):
        """
        Calcula métricas adicionales por cliente.
        
        Args:
            aggregated_df (DataFrame): Datos agregados
            customer_col (str): Columna de cliente
            
        Returns:
            DataFrame: Datos con métricas adicionales
        """
        try:
            # Calcular métricas por cliente
            customer_metrics = aggregated_df.groupby(customer_col).agg({
                'total_quantity': ['sum', 'mean', 'std', 'count'],
                'transaction_count': 'sum',
                'period_dt': ['min', 'max']
            })
            
            # Aplanar columnas
            customer_metrics.columns = [
                'total_sum', 'total_mean', 'total_std', 'period_count',
                'total_transactions', 'first_period', 'last_period'
            ]
            
            customer_metrics = customer_metrics.reset_index()
            
            # Calcular duración del cliente
            customer_metrics['customer_lifetime'] = customer_metrics['period_count']
            
            # Rellenar valores nulos en std con 0
            customer_metrics['total_std'] = customer_metrics['total_std'].fillna(0)
            
            return customer_metrics
            
        except Exception as e:
            raise Exception(f"Error calculando métricas de cliente: {str(e)}")
