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

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

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
    - processing.AnalysisReporter: Análisis de tendencias y reglas de riesgo
    - models.ml_model: Modelo de Machine Learning (predicción de abandono)
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

    # ======================================================================
    # FR1: Carga de Datos Históricos
    # ======================================================================
    def upload_historical_data(self, file_path: str) -> Dict[str, any]:
        result = self.loader.upload_historical_data(file_path)
        if result["success"]:
            # Sincroniza el estado del Analyzer con el estado del Loader
            self.df = self.loader.df
            self.customer_col = self.loader.customer_col
        return result

    # ======================================================================
    # FR2: Agregación de Compras por Cliente y Período
    # ======================================================================
    def aggregate_purchases_by_customer_and_period(
        self, period: str = "month", custom_period: Optional[str] = None
    ) -> Dict[str, any]:
        if self.df is None or not self.customer_col:
            return {
                "success": False,
                "message": "Error: Data not loaded or columns not detected.",
            }

        result = self.aggregator.aggregate_purchases_by_customer_and_period(
            df=self.df,
            customer_col=self.loader.customer_col,
            quantity_col=self.loader.quantity_col,
            date_col=self.loader.date_col,
            year_col=self.loader.year_col,
            month_col=self.loader.month_col,
            period=period,
            custom_period=custom_period,
            operational_center_col=self.loader.operational_center_col
        )
        print(self.loader.operational_center_col)
        print(result["aggregated_data"]["operational_center"].head(5))
        
        if result["success"]:
            # Almacena el resultado agregado para las siguientes etapas
            self.aggregated_df = result["aggregated_data"]
            self.total_records = len(self.aggregated_df)
        return result

    # ======================================================================
    # FR3: Visualización de Tendencias
    # ======================================================================
    def visualize_customer_trends(
        self,
        customer_id: str,
        start_date_str: Optional[str] = None,
        end_date_str: Optional[str] = None,
    ) -> pd.DataFrame:
        if self.aggregated_df is None or not self.customer_col:
            return pd.DataFrame()
        return self.reporter.visualize_customer_trends(
            aggregated_df=self.aggregated_df,
            customer_col=self.customer_col,
            customer_id=customer_id,
            start_date_str=start_date_str,
            end_date_str=end_date_str,
        )

    # ======================================================================
    # FR4: Identificación de Clientes en Riesgo por Regla
    # ======================================================================
    def identify_at_risk_customers(
        self,
        threshold_pct: Optional[float] = None,
        threshold_value: Optional[float] = None,
    ) -> pd.DataFrame:
        if self.aggregated_df is None or not self.customer_col:
            return pd.DataFrame()
        return self.reporter.identify_at_risk_customers(
            aggregated_df=self.aggregated_df,
            customer_col=self.customer_col,
            threshold_pct=threshold_pct,
            threshold_value=threshold_value,
        )

    # ======================================================================
    # FR5: Predicción de Abandono con ML (Random Forest)
    # ======================================================================
    def train_and_predict_churn_with_rf(
        self, test_size: float = 0.2, granularity: str = "M"
    ) -> Dict:
        """
        FR5: Entrena el modelo de Machine Learning (Random Forest)
        y predice clientes con riesgo de abandono.
        """
        print("\n" + "=" * 80)
        print("FR5: MODELO ROBUSTO Y ADAPTATIVO - Análisis", granularity)
        print("=" * 80)

        # --- Validaciones previas ---
        if self.aggregated_df is None:
            return {
                "success": False,
                "message": "❌ Error: You must aggregate data first.",
            }

        if self.customer_col is None:
            return {
                "success": False,
                "message": "❌ Customer column not identified, please check your data.",
            }

        df = self.aggregated_df.copy()
        
        print("#" * 100)
        print(df[["operational_center"]].head(5))

        # --- Diagnóstico previo al modelo ---
        print("\n🔍 VALIDACIÓN DE DATOS DE ENTRADA AL MODELO")
        print(f"   Total de registros: {len(df):,}")
        print(
            f"   Clientes únicos: {df[self.customer_col].nunique() if self.customer_col in df.columns else 'N/A'}"
        )
        print(f"   Columnas disponibles: {df.columns.tolist()}")

        if "total_tons" in df.columns:
            print(
                f"   Suma total de ventas (total_tons): {df['total_tons'].sum():,.2f}"
            )
            print(
                f"   Porcentaje de registros con 0 ventas: {(df['total_tons'] == 0).mean() * 100:.2f}%"
            )
        else:
            posibles = [
                c
                for c in df.columns
                if "ton" in c.lower() or "venta" in c.lower() or "kg" in c.lower()
            ]
            return {
                "success": False,
                "message": f"❌ La columna 'total_tons' no existe en los datos agregados. Posibles columnas: {posibles}",
            }

        # --- Validar si los datos tienen información útil ---
        if df["total_tons"].sum() == 0:
            return {
                "success": False,
                "message": "🚨 ERROR CRÍTICO: El dataset contiene 100% de registros sin ventas. Verifica la preparación de datos.",
            }

        # --- Entrenamiento del modelo ---
        print("\n[INFO] Entrenando modelo de predicción de abandono...")
        result = self.predictor.train_and_predict_churn_with_rf(
            aggregated_df=df,
            customer_col=self.customer_col,
            test_size=test_size,
            granularity=granularity,
        )

        # --- Resultados ---
        if result.get("success"):
            print(
                f"[SUCCESS] Modelo entrenado correctamente con granularidad {granularity}"
            )
        else:
            print(f"[ERROR] Falló el entrenamiento: {result.get('message')}")

        return result

    # ======================================================================
    # FR6: Señalamiento de Caídas Significativas
    # ======================================================================
    def flag_significant_drops(
        self, drop_pct_threshold: float = 30.0, drop_value_threshold: float = 5.0
    ) -> pd.DataFrame:
        if self.aggregated_df is None or not self.customer_col:
            return pd.DataFrame()
        return self.flagger.flag_significant_drops(
            aggregated_df=self.aggregated_df,
            customer_col=self.customer_col,
            drop_pct_threshold=drop_pct_threshold,
            drop_value_threshold=drop_value_threshold,
        )
