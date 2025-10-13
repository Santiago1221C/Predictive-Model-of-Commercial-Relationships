# processing/analyzer.py

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import sys
import os

# Agregar el directorio backend al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.data_loader import DataLoader
from data.data_aggregator import DataAggregator
from models.ml_model import MLModel
from processing.flag_reporter import FlagReporter
from processing.analysis_reporter import AnalysisReporter

warnings.filterwarnings('ignore')

class FunctionalRequirementsAnalyzer:
    """
    Clase principal que orquesta todos los requerimientos funcionales del sistema.
    """
    
    def __init__(self):
        """Inicializa el analizador con componentes necesarios."""
        self.df = None
        self.aggregated_df = None
        self.customer_col = None
        self.date_col = None
        self.quantity_col = None
        self.flagged_customers = None
        
        # Componentes del sistema
        self.data_loader = DataLoader()
        self.data_aggregator = DataAggregator()
        self.ml_model = MLModel()
        self.flag_reporter = FlagReporter()
        self.analysis_reporter = AnalysisReporter()
        
        print("✅ FunctionalRequirementsAnalyzer initialized successfully")

    def upload_historical_data(self, file_path):
        """FR1: Carga datos históricos desde un archivo CSV."""
        try:
            print(f"\n{'='*80}")
            print("FUNCTIONAL REQUIREMENT 1: UPLOAD HISTORICAL DATA")
            print(f"{'='*80}")
            
            result = self.data_loader.load_csv(file_path)
            
            if result['success']:
                self.df = result['dataframe']
                self.customer_col = result['customer_col']
                self.date_col = result['date_col']
                self.quantity_col = result['quantity_col']
                
                print(f"File loaded successfully. Columns detected: Customer='{self.customer_col}', Date='{self.date_col}', Quantity='{self.quantity_col}'")
                print("🎉 UPLOAD COMPLETED SUCCESSFULLY")
                print(f"{'='*80}")
                
                return {
                    'success': True,
                    'message': 'Data uploaded successfully',
                    'total_rows': len(self.df),
                    'total_columns': len(self.df.columns),
                    'customer_col': self.customer_col,
                    'date_col': self.date_col,
                    'quantity_col': self.quantity_col
                }
            else:
                return result
                
        except Exception as e:
            error_msg = f"Error uploading data: {str(e)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'message': error_msg}

    def aggregate_customer_data(self, period='month'):
        """FR2: Agrega datos por cliente y período."""
        try:
            if self.df is None:
                return {'success': False, 'message': 'No data loaded. Please upload data first.'}
            
            print(f"\n{'='*80}")
            print("FUNCTIONAL REQUIREMENT 2: AGGREGATE DATA")
            print(f"{'='*80}")
            print(f"Aggregating data by customer and period: {period}")
            
            result = self.data_aggregator.aggregate_by_period(
                self.df, 
                self.customer_col, 
                self.date_col, 
                self.quantity_col, 
                period
            )
            
            if result['success']:
                self.aggregated_df = result['aggregated_data']
                print("🎉 AGGREGATION COMPLETED SUCCESSFULLY")
                print(f"{'='*80}")
                
                return {
                    'success': True,
                    'message': f'Data aggregated successfully by {period}',
                    'total_records': len(self.aggregated_df),
                    'period': period
                }
            else:
                return result
                
        except Exception as e:
            error_msg = f"Error aggregating data: {str(e)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'message': error_msg}

    def visualize_trends(self, chart_type='line', customer_id=None):
        """FR3: Genera datos para visualización de tendencias por cliente específico."""
        try:
            if self.aggregated_df is None:
                return {'success': False, 'message': 'No aggregated data available. Please aggregate data first.'}
            
            print(f"\n{'='*80}")
            print("FUNCTIONAL REQUIREMENT 3: VISUALIZE TRENDS")
            print(f"{'='*80}")
            print(f"Generating {chart_type} chart data for customer: {customer_id}")
            
            if customer_id is None:
                return {'success': False, 'message': 'Customer ID is required for trend visualization.'}
            
            # Filtrar datos por cliente específico
            customer_data = self.aggregated_df[self.aggregated_df[self.customer_col] == customer_id]
            
            if len(customer_data) == 0:
                available_customers = self.aggregated_df[self.customer_col].unique().tolist()
                return {
                    'success': False, 
                    'message': f'Customer "{customer_id}" not found. Available customers: {available_customers[:10]}...'
                }
            
            # Ordenar por período
            customer_data = customer_data.sort_values('period_dt')
            
            # Convertir a formato para charts
            chart_data = []
            for _, row in customer_data.iterrows():
                chart_data.append({
                    'period_dt': str(row['period_dt']),
                    'total_tons': round(row['total_quantity'] / 1000, 2),  # Convertir a toneladas
                    'transaction_count': int(row['transaction_count'])
                })
            
            print(f"Generated chart data with {len(chart_data)} data points for customer {customer_id}")
            print("🎉 VISUALIZATION DATA GENERATED SUCCESSFULLY")
            print(f"{'='*80}")
            
            return {
                'success': True,
                'data': chart_data,
                'chart_type': chart_type,
                'customer_id': customer_id,
                'message': f'{chart_type.title()} chart data generated successfully for customer {customer_id}'
            }
            
        except Exception as e:
            error_msg = f"Error generating visualization: {str(e)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'message': error_msg}

    def identify_at_risk_customers(self, threshold_pct=None, threshold_value=None):
        """FR4: Identifica los 10 clientes con mayor riesgo."""
        try:
            if self.aggregated_df is None:
                return {'success': False, 'message': 'No aggregated data available. Please aggregate data first.'}
            
            print(f"[DEBUG] Risk analysis parameters - Percentage: {threshold_pct}, Value: {threshold_value}")
            print(f"[DEBUG] Aggregated data shape: {self.aggregated_df.shape}")
            
            result = self.analysis_reporter.identify_at_risk_customers(
                self.aggregated_df, 
                self.customer_col, 
                threshold_pct, 
                threshold_value
            )
            
            if result['success']:
                # Tomar solo los 10 clientes con mayor riesgo
                top_10_risk = result['data'][:10] if len(result['data']) > 10 else result['data']
                
                print(f"[DEBUG] Returning top 10 risk customers: {len(top_10_risk)} customers")
                
                return {
                    'success': True,
                    'data': top_10_risk,
                    'total_at_risk': len(result['data']),
                    'showing_count': len(top_10_risk),
                    'message': f"Showing top {len(top_10_risk)} customers at risk (of {len(result['data'])} total)"
                }
            else:
                return result
                
        except Exception as e:
            error_msg = f"Error identifying at-risk customers: {str(e)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'message': error_msg}

    def predict_churn_risk(self):
        """FR5: Predice los 10 clientes con mayor riesgo usando ML."""
        try:
            if self.aggregated_df is None:
                return {'success': False, 'message': 'No aggregated data available. Please aggregate data first.'}
            
            print(f"\n{'='*80}")
            print("FUNCTIONAL REQUIREMENT 5: PREDICT CHURN RISK (ML)")
            print(f"{'='*80}")
            
            result = self.ml_model.train_and_predict(self.aggregated_df, self.customer_col)
            
            if result['success']:
                # Tomar solo los 10 clientes con mayor probabilidad de churn
                top_10_predictions = result['predictions'][:10] if len(result['predictions']) > 10 else result['predictions']
                
                # Actualizar el resultado
                result['predictions'] = top_10_predictions
                result['showing_count'] = len(top_10_predictions)
                result['evaluation']['total_high_risk_shown'] = len(top_10_predictions)
                
                print("🎉 ML PREDICTION COMPLETED SUCCESSFULLY")
                print(f"Showing top {len(top_10_predictions)} customers with highest churn risk")
                print(f"{'='*80}")
                
                return result
            else:
                return result
                
        except Exception as e:
            error_msg = f"Error predicting churn risk: {str(e)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'message': error_msg}

    def flag_significant_drops(self, threshold_pct=30.0, threshold_value=None):
        """FR6: Marca clientes con caídas significativas."""
        try:
            if self.aggregated_df is None:
                return {'success': False, 'message': 'No aggregated data available. Please aggregate data first.'}
            
            print(f"\n{'='*80}")
            print("FUNCTIONAL REQUIREMENT 6: FLAG SIGNIFICANT DROPS")
            print(f"{'='*80}")
            
            result = self.flag_reporter.flag_customers_with_drops(
                self.aggregated_df, 
                self.customer_col, 
                threshold_pct, 
                threshold_value
            )
            
            if result['success']:
                self.flagged_customers = result['flagged_data']
                print("🎉 FLAGGING COMPLETED SUCCESSFULLY")
                print(f"{'='*80}")
                
                return {
                    'success': True,
                    'data': result['data'],
                    'total_flagged': len(result['data']),
                    'message': f"Flagged {len(result['data'])} customers with significant drops"
                }
            else:
                return result
                
        except Exception as e:
            error_msg = f"Error flagging customers: {str(e)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'message': error_msg}

    def get_available_customers(self):
        """Obtiene la lista de clientes disponibles."""
        try:
            if self.df is None:
                return {'success': False, 'message': 'No data loaded.'}
            
            customers = sorted(self.df[self.customer_col].unique().tolist())
            return {
                'success': True,
                'customers': customers,
                'total_customers': len(customers)
            }
        except Exception as e:
            return {'success': False, 'message': f'Error getting customers: {str(e)}'}

