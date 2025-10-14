# models/ml_model.py - MODELO ROBUSTO Y ADAPTATIVO (ACTUALIZADO CON VALIDACIÓN DE DATOS)

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
import warnings

warnings.filterwarnings('ignore')


class ChurnPredictor:
    """FR5: Predictor de abandono ROBUSTO con adaptación temporal y detección de anomalías."""

    def __init__(self):
        self.model: Optional[RandomForestClassifier] = None
        self.model_gb: Optional[GradientBoostingClassifier] = None
        self.scaler: Optional[RobustScaler] = None
        self.granularity: str = 'M'
        self.global_stats: Dict = {}

    # ------------------------------------------------------------------------------------
    # FUNCIONES AUXILIARES
    # ------------------------------------------------------------------------------------

    def _calculate_global_context(self, df: pd.DataFrame, customer_col: str) -> pd.DataFrame:
        """Calcula contexto global del mercado por período para normalización adaptativa."""
        global_stats = df.groupby('period').agg({
            'total_tons': ['mean', 'median', 'std', 'sum']
        }).reset_index()

        global_stats.columns = ['period', 'market_avg', 'market_median', 'market_std', 'market_total']
        df = df.merge(global_stats, on='period', how='left')
        self.global_stats = global_stats.set_index('period').to_dict('index')
        return df

    def _create_advanced_features(self, df: pd.DataFrame, customer_col: str, window_size: int) -> pd.DataFrame:
        """Crea features avanzados que capturan contexto relativo y anomalías."""
        df = df.copy()

        # 1️⃣ Features básicos
        df['avg_tons_last_n'] = df.groupby(customer_col)['total_tons'].transform(
            lambda x: x.rolling(window_size, 1).mean().shift(1)
        )
        df['std_tons_last_n'] = df.groupby(customer_col)['total_tons'].transform(
            lambda x: x.rolling(window_size, 1).std().shift(1)
        )

        # 2️⃣ Relación con el mercado
        df['tons_vs_market_avg'] = df['total_tons'] / (df['market_avg'] + 0.01)
        df['tons_vs_market_median'] = df['total_tons'] / (df['market_median'] + 0.01)

        # 3️⃣ Tendencia
        df['trend_tons'] = df.groupby(customer_col)['total_tons'].transform(
            lambda x: x.rolling(window_size, min_periods=2).apply(
                lambda y: np.polyfit(range(len(y)), y, 1)[0] if len(y) > 1 else 0, raw=True
            ).shift(1)
        )
        df['trend_normalized'] = df['trend_tons'] / (df['avg_tons_last_n'] + 0.01)

        # 4️⃣ Variabilidad y estabilidad
        df['cv_tons'] = df['std_tons_last_n'] / (df['avg_tons_last_n'] + 0.01)
        df['stability'] = 1 / (1 + df['cv_tons'])

        # 5️⃣ Ratio de cambio
        df['tons_change_ratio'] = (df['total_tons'] - df['avg_tons_last_n']) / (df['avg_tons_last_n'] + 0.01)

        # 6️⃣ Z-score (detección de anomalías)
        df['z_score_tons'] = df.groupby(customer_col)['total_tons'].transform(
            lambda x: (x - x.rolling(window_size, 1).mean().shift(1)) /
                      (x.rolling(window_size, 1).std().shift(1) + 0.01)
        )

        # 7️⃣ Frecuencia de compras
        df['purchase_frequency'] = df.groupby(customer_col)['total_tons'].transform(
            lambda x: (x > 0).rolling(window_size, 1).sum().shift(1)
        )

        # 8️⃣ Períodos desde última compra
        df['has_purchase'] = (df['total_tons'] > 0).astype(int)

        def calculate_periods_since_purchase(group):
            result = []
            periods_counter = 0
            for _, row in group.iterrows():
                if row['has_purchase'] == 1:
                    periods_counter = 0
                else:
                    periods_counter += 1
                result.append(periods_counter)
            return pd.Series(result, index=group.index)

        df['periods_since_last_purchase'] = df.groupby(customer_col).apply(
            calculate_periods_since_purchase
        ).reset_index(level=0, drop=True)

        # 9️⃣ Aceleración y momentum
        df['acceleration'] = df.groupby(customer_col)['trend_tons'].transform(lambda x: x.diff().shift(1))
        df['momentum'] = df['trend_normalized'] * df['purchase_frequency']

        return df

    # ------------------------------------------------------------------------------------
    # VALIDACIÓN DE CALIDAD DE DATOS
    # ------------------------------------------------------------------------------------
    def _validate_sales_data(self, df: pd.DataFrame, customer_col: str):
        """🧩 NUEVO: Verifica si el dataset tiene ventas válidas antes del modelado."""
        total_sales = df['total_tons'].sum()
        zero_sales_ratio = (df['total_tons'] == 0).mean()

        print("\n🔍 VALIDACIÓN DE DATOS DE ENTRADA")
        print(f"   Total de registros: {len(df):,}")
        print(f"   Clientes únicos: {df[customer_col].nunique():,}")
        print(f"   Total de ventas (suma total_tons): {total_sales:,.2f}")
        print(f"   Porcentaje de registros con 0 ventas: {zero_sales_ratio*100:.1f}%")

        print("🧠 DEBUG: Revisión justo antes del cálculo de suma")
        print(f"Columnas actuales: {df.columns.tolist() if 'df' in locals() else 'df no definido'}")
        if 'df' in locals() and 'total_tons' in df.columns:
            print(f"Suma total_tons (ahora): {df['total_tons'].sum():,.2f}")
        else:
            print("⚠️ 'total_tons' ya no está presente en este punto del flujo")
        print("=" * 120)


        if total_sales == 0 or zero_sales_ratio > 0.99:
            raise Exception(
                "🚨 ERROR CRÍTICO: El dataset contiene 100% de registros sin ventas.\n"
                "Esto indica un problema en la preparación de datos (probablemente en data_aggregator.py).\n"
                "Verifica que las toneladas se agreguen correctamente por cliente y período."
            )
        elif zero_sales_ratio > 0.8:
            print("⚠️ ADVERTENCIA: Más del 80% de los registros tienen ventas = 0.")
            print("   Esto puede afectar la calidad del modelo y debe revisarse.")

    # ------------------------------------------------------------------------------------
    # FUNCIÓN PRINCIPAL DE ENTRENAMIENTO
    # ------------------------------------------------------------------------------------
    def train_and_predict_churn_with_rf(
        self,
        aggregated_df,
        customer_col,
        test_size: float = 0.2,
        granularity: str = 'M'
    ):
        """
        Entrena un modelo Random Forest para predecir abandono de clientes (churn)
        basado en el comportamiento de compra agregado.
        Incluye validaciones y trazas detalladas para depuración.
        """

        print("\n[INFO] Entrenando modelo de predicción de abandono...")
        print("=" * 120)

        # ------------------------------------------------------------------------------------------------------
        # COPIA SEGURA DEL DATAFRAME
        # ------------------------------------------------------------------------------------------------------
        df = aggregated_df.copy()
        print("📊 DEBUG POST-PROCESAMIENTO INICIAL EN ML MODEL")
        print(f"Columnas actuales: {df.columns.tolist()}")
        if 'total_tons' in df.columns:
            try:
                print(f"Suma inicial total_tons: {df['total_tons'].sum():,.2f}")
            except Exception:
                print("Suma inicial total_tons: ERROR al sumar (tipo no numérico).")
        print(df.head(5))
        print("=" * 120)

        # ------------------------------------------------------------------------------------------------------
        # VALIDACIÓN DE COLUMNAS NECESARIAS
        # ------------------------------------------------------------------------------------------------------
        required_cols = ['period', customer_col, 'total_tons']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            msg = f"❌ Faltan columnas requeridas: {missing_cols}"
            print(msg)
            return {'success': False, 'message': msg}

        # ------------------------------------------------------------------------------------------------------
        # ASEGURAR TIPOS NUMÉRICOS EN total_tons
        # ------------------------------------------------------------------------------------------------------
        df['total_tons'] = pd.to_numeric(df['total_tons'], errors='coerce').fillna(0)
        print(f"✅ Suma antes del pivot: {df['total_tons'].sum():,.2f}")

        # ------------------------------------------------------------------------------------------------------
        # CREACIÓN DE MATRIZ CLIENTE vs PERÍODO (pivot)
        # ------------------------------------------------------------------------------------------------------
        pivot_df = (
            df.pivot_table(
                index=customer_col,
                columns='period',
                values='total_tons',
                aggfunc='sum',
                fill_value=0
            )
        )

        # Normalizar nombres de columnas (string) y reset index
        pivot_df.columns = [str(c) for c in pivot_df.columns]
        pivot_df = pivot_df.reset_index()

        print(f"✅ Suma total post-pivot: {pivot_df.drop(columns=[customer_col]).sum().sum():,.2f}")
        print(f"📋 Forma final del pivot_df: {pivot_df.shape}")
        print("=" * 120)

        # ------------------------------------------------------------------------------------------------------
        # VALIDACIÓN POSTERIOR AL PIVOT
        # ------------------------------------------------------------------------------------------------------
        total_sum = pivot_df.drop(columns=[customer_col]).sum().sum()
        if total_sum == 0:
            msg = (
                "🚨 ERROR CRÍTICO: Tras pivotar, todas las ventas son 0.\n"
                "Esto indica pérdida de datos en la matriz temporal (pivot_df).\n"
                "Verifica el formato de los períodos o los nombres de columnas."
            )
            print(msg)
            return {'success': False, 'message': msg}

        # ------------------------------------------------------------------------------------------------------
        # CREACIÓN DE VARIABLES DE ENTRADA Y ETIQUETA (EJEMPLO BÁSICO)
        # ------------------------------------------------------------------------------------------------------
        # Necesitamos al menos 3 columnas (cliente + 2 períodos) para calcular la caída
        if pivot_df.shape[1] < 3:
            msg = "❌ No hay suficientes períodos para entrenar (mínimo 2 períodos + cliente)."
            print(msg)
            return {'success': False, 'message': msg}

        # Convertir todas las columnas de período a numéricas (excepto la columna cliente)
        for col in pivot_df.columns:
            if col != customer_col:
                pivot_df[col] = pd.to_numeric(pivot_df[col], errors='coerce').fillna(0)

        # Ordenar las columnas por nombre (esto sitúa períodos cronológicos si tus nombres son ordenables)
        pivot_df = pivot_df.reindex(sorted(pivot_df.columns), axis=1)

        # Generar lista de columnas de período (excluyendo columna cliente)
        period_cols = [c for c in pivot_df.columns if c != customer_col]
        if len(period_cols) < 2:
            msg = "❌ No hay suficientes columnas de período después de procesar."
            print(msg)
            return {'success': False, 'message': msg}

        last_period = period_cols[-1]
        prev_period = period_cols[-2]

        print(f"🧩 DEBUG: Últimos períodos detectados -> prev: {prev_period}, last: {last_period}")
        print(f"Tipos de datos de esas columnas:\n{pivot_df[[prev_period, last_period]].dtypes}")

        # Calcular el porcentaje de caída (manejo seguro de ceros)
        pivot_df['drop_pct'] = (
            (pivot_df[last_period] - pivot_df[prev_period]) /
            pivot_df[prev_period].replace(0, pd.NA)
        ) * 100
        pivot_df['drop_pct'] = pivot_df['drop_pct'].fillna(0)

        # Crear etiqueta de churn (ejemplo simple: caída mayor a 30%)
        pivot_df['churn_flag'] = (pivot_df['drop_pct'] < -30).astype(int)

        print("📉 Ejemplo de cálculo de churn_flag (primeros registros):")
        print(pivot_df[[customer_col, prev_period, last_period, 'drop_pct', 'churn_flag']].head(5))

        # ------------------------------------------------------------------------------------------------------
        # ENTRENAMIENTO DE MODELO RANDOM FOREST (BÁSICO)
        # ------------------------------------------------------------------------------------------------------
        X = pivot_df.drop(columns=[customer_col, 'churn_flag', 'drop_pct'])
        y = pivot_df['churn_flag']

        # Verificar que hay al menos una clase positiva y una negativa
        if len(y.unique()) < 2:
            msg = "❌ No hay suficiente variabilidad en la etiqueta 'churn_flag' para entrenar el modelo."
            print(msg)
            return {'success': False, 'message': msg}

        try:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
        except Exception:
            # fallback si stratify falla
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        print("\n🧠 RESULTADOS DEL MODELO:")
        try:
            print(classification_report(y_test, y_pred))
        except Exception:
            print("No se pudo generar el classification_report (posible falta de clases en y_test).")

        print("[✅] Validaciones superadas. Modelo entrenado correctamente.")
        print("=" * 120)

        return {
            'success': True,
            'message': 'Modelo entrenado correctamente',
            'granularity': granularity,
            'aggregated': pivot_df,
            'report': classification_report(y_test, y_pred, output_dict=True) if len(y.unique()) > 1 else None
        }