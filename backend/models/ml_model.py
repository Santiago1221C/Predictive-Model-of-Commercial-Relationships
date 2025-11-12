import pandas as pd
import numpy as np
from typing import Dict, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
import warnings

warnings.filterwarnings("ignore")


class ChurnPredictor:
    """Predictor de abandono de clientes (churn) con validación y trazabilidad por centro operativo."""

    def __init__(self):
        self.model: Optional[RandomForestClassifier] = None
        self.granularity: str = "M"

    # ------------------------------------------------------------------------------------
    # VALIDACIÓN DE CALIDAD DE DATOS
    # ------------------------------------------------------------------------------------
    def _validate_sales_data(self, df: pd.DataFrame, customer_col: str):
        """Verifica la calidad de los datos de ventas antes del modelado."""
        total_sales = df["total_tons"].sum()
        zero_sales_ratio = (df["total_tons"] == 0).mean()

        print("\n=== VALIDACIÓN DE DATOS DE ENTRADA ===")
        print(f"Total de registros: {len(df):,}")
        print(f"Clientes únicos: {df[customer_col].nunique():,}")
        print(f"Total de ventas (total_tons): {total_sales:,.2f}")
        print(f"Porcentaje de registros con ventas = 0: {zero_sales_ratio * 100:.1f}%")

        if total_sales == 0 or zero_sales_ratio > 0.99:
            raise Exception(
                "ERROR: El dataset contiene casi todos los registros sin ventas. "
                "Verifica la agregación en data_aggregator.py."
            )
        elif zero_sales_ratio > 0.8:
            print("ADVERTENCIA: Más del 80% de los registros tienen ventas = 0.")

    # ------------------------------------------------------------------------------------
    # ENTRENAMIENTO DEL MODELO DE CHURN
    # ------------------------------------------------------------------------------------
    def train_and_predict_churn_with_rf(
        self,
        aggregated_df: pd.DataFrame,
        customer_col: str,
        test_size: float = 0.2,
        granularity: str = "M",
    ) -> Dict[str, any]:
        """
        Entrena un modelo Random Forest para predecir abandono de clientes (churn)
        usando la data agregada. Mantiene el centro operativo para análisis posteriores.
        """

        print("\n=== ENTRENAMIENTO DEL MODELO DE CHURN ===")
        df = aggregated_df.copy()

        required_cols = ["period", customer_col, "total_tons"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            msg = f"Faltan columnas requeridas: {missing_cols}"
            print(msg)
            return {"success": False, "message": msg}

        # Validar calidad básica
        self._validate_sales_data(df, customer_col)

        # Convertir a numérico
        df["total_tons"] = pd.to_numeric(df["total_tons"], errors="coerce").fillna(0)

        # Guardar el centro operativo para trazabilidad (si existe)
        if "operational_center" in df.columns:
            centers_df = df[[customer_col, "operational_center"]].drop_duplicates()
        else:
            centers_df = pd.DataFrame(columns=[customer_col, "operational_center"])
        print("#" * 100)
        print(df[["operational_center"]].head(5))

        # Pivot (cliente x período)
        pivot_df = df.pivot_table(
            index=customer_col,
            columns="period",
            values="total_tons",
            aggfunc="sum",
            fill_value=0,
        ).reset_index()

        # Restaurar centro operativo al resultado
        pivot_df = pivot_df.merge(centers_df, on=customer_col, how="left")

        print(
            f"Pivot final: {pivot_df.shape[0]} clientes x {pivot_df.shape[1]} columnas"
        )
        print(
            f"Total ventas post-pivot: {pivot_df.drop(columns=[customer_col, 'operational_center'], errors='ignore').sum().sum():,.2f}"
        )

        # Validación post-pivot
        total_sum = (
            pivot_df.drop(columns=[customer_col, "operational_center"], errors="ignore")
            .sum()
            .sum()
        )
        if total_sum == 0:
            msg = "Error: todas las ventas son 0 después del pivot. Revisar data_aggregator."
            print(msg)
            return {"success": False, "message": msg}

        # Ordenar columnas por nombre
        pivot_df = pivot_df.reindex(sorted(pivot_df.columns), axis=1)

        # Identificar columnas de período
        period_cols = [
            c for c in pivot_df.columns if c not in [customer_col, "operational_center"]
        ]
        if len(period_cols) < 2:
            msg = "Error: no hay suficientes períodos para entrenar."
            print(msg)
            return {"success": False, "message": msg}

        last_period = period_cols[-1]
        prev_period = period_cols[-2]

        # Calcular tasa de caída
        pivot_df["drop_pct"] = (
            (pivot_df[last_period] - pivot_df[prev_period])
            / pivot_df[prev_period].replace(0, np.nan)
        ) * 100
        pivot_df["drop_pct"] = pivot_df["drop_pct"].fillna(0)

        # Etiqueta de churn
        pivot_df["churn_flag"] = (pivot_df["drop_pct"] < -30).astype(int)

        print("\nEjemplo de cálculo de churn_flag:")
        print(
            pivot_df[
                [
                    customer_col,
                    "operational_center",
                    prev_period,
                    last_period,
                    "drop_pct",
                    "churn_flag",
                ]
            ].head(5)
        )

        # Preparar features y etiquetas
        X = pivot_df.drop(
            columns=[customer_col, "operational_center", "churn_flag", "drop_pct"],
            errors="ignore",
        )
        y = pivot_df["churn_flag"]

        if len(y.unique()) < 2:
            msg = "Error: no hay suficiente variabilidad en 'churn_flag'."
            print(msg)
            return {"success": False, "message": msg}

        # Split y entrenamiento
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
        except Exception:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)

        print("\n=== RESULTADOS DEL MODELO ===")
        try:
            print(classification_report(y_test, y_pred))
        except Exception:
            print("No se pudo generar el classification_report.")

        print("Modelo entrenado correctamente.\n")

        # Generate predictions for all customers
        y_proba_all = self.model.predict_proba(X)
        churn_predictions = pd.DataFrame({
            customer_col: pivot_df[customer_col],
            'churn_probability': y_proba_all[:, 1],  # Probability of churn (class 1)
            'churn_prediction': self.model.predict(X),
            'drop_pct': pivot_df['drop_pct'],
        })

        # Add total_tons from the last period
        if last_period in pivot_df.columns:
            churn_predictions['total_tons'] = pivot_df[last_period]
        else:
            churn_predictions['total_tons'] = 0

        # Add operational_center if available
        if 'operational_center' in pivot_df.columns:
            churn_predictions['operational_center'] = pivot_df['operational_center']

        # Sort by churn probability (highest risk first) and get top 10
        top_predictions = churn_predictions.sort_values(
            'churn_probability', 
            ascending=False
        ).head(10)

        return {
            "success": True,
            "message": "Modelo entrenado correctamente",
            "granularity": granularity,
            "predictions": top_predictions.to_dict('records'),
            "evaluation": {
                "report": classification_report(y_test, y_pred, output_dict=True),
                "accuracy": (y_pred == y_test).mean()
            }
        }
