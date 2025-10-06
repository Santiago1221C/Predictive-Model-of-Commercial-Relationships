# processing/analyzer.py

import pandas as pd
from typing import Dict, Optional

# Importaciones CORREGIDAS usando rutas relativas
try:
    # Intentar imports relativos primero
    from ..data.data_loader import DataLoader
    from ..data.data_aggregator import DataAggregator
    from .analysis_reporter import AnalysisReporter
    from ..models.ml_model import ChurnPredictor
    from .flag_reporter import FlagReporter
    
except ImportError:
    # Si fallan, intentar imports absolutos con sys.path
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    
    from data.data_loader import DataLoader
    from data.data_aggregator import DataAggregator
    from processing.analysis_reporter import AnalysisReporter
    from models.ml_model import ChurnPredictor
    from processing.flag_reporter import FlagReporter

class FunctionalRequirementsAnalyzer:
    """
    Clase principal orquestadora (Façade/SRP). Gestiona el flujo de datos
    y delega tareas específicas a módulos especializados:
    - data.DataLoader: Carga de datos
    - data.DataAggregator: Agregación por período
    - processing.AnalysisReporter: Análisis de tendencias y reglas de riesgo (umbral)
    - models.ml_model: Modelo de Machine Learning para predicción de abandono
    """
    
    def __init__(self, csv_file: Optional[str] = None):
        # Estado principal de los datos
        self.df: Optional[pd.DataFrame] = None
        self.aggregated_df: Optional[pd.DataFrame] = None
        
        # Información de las columnas (mantenida por el loader)
        self.customer_col: Optional[str] = None
        
        # Composición de módulos especializados (Inyección de dependencias)
        self.loader = DataLoader()
        self.aggregator = DataAggregator()
        self.reporter = AnalysisReporter()
        self.predictor = ChurnPredictor()
        self.flagger = FlagReporter()
        
        if csv_file:
            self.upload_historical_data(csv_file)

    # FR1: Carga de Datos Históricos (Delegado a DataLoader)
    def upload_historical_data(self, file_path: str) -> Dict[str, any]:
        result = self.loader.upload_historical_data(file_path)
        if result['success']:
            # Sincroniza el estado del Analyzer con el estado del Loader
            self.df = self.loader.df
            self.customer_col = self.loader.customer_col
        return result

    # FR2: Agregación de Compras (Delegado a DataAggregator)
    def aggregate_purchases_by_customer_and_period(self, period: str = 'month', custom_period: Optional[str] = None) -> Dict[str, any]:
        if self.df is None or not self.customer_col:
            return {'success': False, 'message': "Error: Data not loaded or columns not detected."}
            
        result = self.aggregator.aggregate_purchases_by_customer_and_period(
            df=self.df,
            customer_col=self.loader.customer_col,
            quantity_col=self.loader.quantity_col,
            date_col=self.loader.date_col,
            year_col=self.loader.year_col,
            month_col=self.loader.month_col,
            period=period,
            custom_period=custom_period
        )
        if result['success']:
            # Almacena el resultado agregado para las siguientes etapas
            self.aggregated_df = result['aggregated_data']
        return result

    # FR3: Visualización de Tendencias (Delegado a AnalysisReporter)
    def visualize_customer_trends(self, customer_id: str, start_date_str: Optional[str] = None, end_date_str: Optional[str] = None) -> pd.DataFrame:
        if self.aggregated_df is None or not self.customer_col:
            return pd.DataFrame()
        return self.reporter.visualize_customer_trends(
            aggregated_df=self.aggregated_df,
            customer_col=self.customer_col,
            customer_id=customer_id,
            start_date_str=start_date_str,
            end_date_str=end_date_str
        )

    # FR4: Identificación de Riesgo por Regla (Delegado a AnalysisReporter)
    def identify_at_risk_customers(self, threshold_pct: Optional[float] = None, threshold_value: Optional[float] = None) -> pd.DataFrame:
        if self.aggregated_df is None or not self.customer_col:
            return pd.DataFrame()
        return self.reporter.identify_at_risk_customers(
            aggregated_df=self.aggregated_df,
            customer_col=self.customer_col,
            threshold_pct=threshold_pct,
            threshold_value=threshold_value
        )
        
    # FR5: Predicción de Abandono con ML (Delegado a ChurnPredictor)
    def train_and_predict_churn_with_rf(self, test_size: float = 0.2) -> Dict:
        if self.aggregated_df is None or not self.customer_col:
            return {'success': False, 'message': "Error: You must aggregate data first."}
            
        result = self.predictor.train_and_predict_churn_with_rf(
            aggregated_df=self.aggregated_df,
            customer_col=self.customer_col,
            test_size=test_size
        )
        
        # === AÑADIR COMPROBACIÓN ADICIONAL ===
        if result.get('success') and not result.get('predictions'):
            # Si 'success' es True pero 'predictions' está vacío (o no existe)
            return {'success': False, 'message': "ML Model trained successfully, but no predictions were generated (predictions list is empty). Check data format."}
        # ====================================

        return result
        
    def flag_significant_drops(self, drop_pct_threshold: float = 30.0, drop_value_threshold: float = 5.0) -> pd.DataFrame:
        if self.aggregated_df is None or not self.customer_col:
            return pd.DataFrame()
        return self.flagger.flag_significant_drops(
            aggregated_df=self.aggregated_df,
            customer_col=self.customer_col,
            drop_pct_threshold=drop_pct_threshold,
            drop_value_threshold=drop_value_threshold
        )

