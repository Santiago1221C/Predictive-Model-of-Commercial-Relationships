# processing/analysis_reporter.py

import pandas as pd
import numpy as np
from typing import Optional


class AnalysisReporter:
    """Maneja el informe de tendencias de clientes (FR3) y la identificación de clientes en riesgo (FR4)."""

    # [Código de visualize_customer_trends() sin cambios]
    def visualize_customer_trends(
        self,
        aggregated_df: pd.DataFrame,
        customer_col: str,
        customer_id: str,
        start_date_str: Optional[str] = None,
        end_date_str: Optional[str] = None,
    ) -> pd.DataFrame:
        """FR3: Filtra los datos agregados para un cliente específico y un rango de fechas."""
        print(f"Getting trend data for customer {customer_id}...")

        if aggregated_df.empty:
            return pd.DataFrame()

        customer_data = aggregated_df[aggregated_df[customer_col] == customer_id].copy()

        if customer_data.empty:
            return pd.DataFrame()

        # Convertir la columna de período a datetime para facilitar el filtrado
        customer_data["period_dt"] = pd.to_datetime(customer_data["period"])

        try:
            if start_date_str:
                start_date = pd.to_datetime(start_date_str)
                customer_data = customer_data[customer_data["period_dt"] >= start_date]
            if end_date_str:
                end_date = pd.to_datetime(end_date_str)
                customer_data = customer_data[customer_data["period_dt"] <= end_date]
        except ValueError:
            print("Warning: Invalid date format. Date filter will be ignored.")

        if customer_data.empty:
            return pd.DataFrame()

        return customer_data.sort_values("period_dt")

    # -------------------------------------------------------------------------------------

    def identify_at_risk_customers(
        self,
        aggregated_df: pd.DataFrame,
        customer_col: str,
        threshold_pct: Optional[float] = None,
        threshold_value: Optional[float] = None,
    ) -> pd.DataFrame:
        """FR4: Identifica clientes en riesgo basándose en una caída respecto a su promedio de los últimos 3 períodos.
        Maneja valores negativos (devoluciones/créditos) correctamente."""
        print(
            f"Identifying at-risk customers with thresholds - Percentage: {threshold_pct}%, Value: {threshold_value}"
        )

        if aggregated_df.empty:
            print("No aggregated data available")
            return pd.DataFrame()

        # Verificar que existan las columnas necesarias
        required_cols = [customer_col, "period", "total_tons"]
        if not all(col in aggregated_df.columns for col in required_cols):
            print(f"Missing required columns. Available: {list(aggregated_df.columns)}")
            return pd.DataFrame()

        df_risk = aggregated_df.copy().sort_values([customer_col, "period"])

        # Asegurar que period sea datetime para ordenamiento correcto
        if not pd.api.types.is_datetime64_any_dtype(df_risk["period"]):
            df_risk["period"] = pd.to_datetime(df_risk["period"])

        # Calcular promedio móvil de 3 períodos (excluyendo el período actual)
        # Usar el valor absoluto o cero como mínimo para el promedio
        df_risk["avg_last_3_tons"] = df_risk.groupby(customer_col)[
            "total_tons"
        ].transform(lambda x: x.shift(1).rolling(window=3, min_periods=1).mean())

        # Obtener el último período de compra para cada cliente
        latest_purchases = df_risk.loc[
            df_risk.groupby(customer_col)["period"].idxmax()
        ].copy()

        print(f"Total customers found: {len(latest_purchases)}")

        # FILTRAR: Excluir clientes cuya última compra fue hace más de 12 meses
        # Estos clientes ya abandonaron la relación comercial
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        current_date = pd.Timestamp.now()
        twelve_months_ago = current_date - relativedelta(months=12)

        print(f"Current date: {current_date.strftime('%Y-%m-%d')}")
        print(f"Cutoff date (12 months ago): {twelve_months_ago.strftime('%Y-%m-%d')}")

        # Filtrar clientes activos (última compra dentro de los últimos 12 meses)
        active_customers = latest_purchases[latest_purchases["period"] >= twelve_months_ago].copy()

        print(f"Customers with purchases in last 12 months: {len(active_customers)}")
        print(f"Customers filtered out (inactive > 12 months): {len(latest_purchases) - len(active_customers)}")

        if active_customers.empty:
            print("No active customers found in the last 12 months")
            return pd.DataFrame()

        # Usar solo clientes activos para el análisis
        latest_purchases = active_customers

        # Filtrar clientes que tienen datos históricos válidos
        customers_with_history = df_risk.groupby(customer_col).size() >= 2
        valid_customers = customers_with_history[customers_with_history].index

        latest_purchases = latest_purchases[
            latest_purchases[customer_col].isin(valid_customers)
            & latest_purchases["avg_last_3_tons"].notna()
            & (latest_purchases["avg_last_3_tons"] > 0)  # Promedio debe ser positivo
            & (latest_purchases["period"] >= twelve_months_ago)  # Última compra reciente
        ]

        if latest_purchases.empty:
            print("No customers with sufficient history found")
            return pd.DataFrame()

        print(f"Customers with valid history: {len(latest_purchases)}")

        # Calcular métricas de caída
        latest_purchases["drop_value"] = (
            latest_purchases["avg_last_3_tons"] - latest_purchases["total_tons"]
        )
        
        # Calcular drop_pct con manejo especial para valores negativos
        latest_purchases["drop_pct"] = (
            latest_purchases["drop_value"] / latest_purchases["avg_last_3_tons"]
        ) * 100
        
        # CORRECCIÓN: Manejar casos especiales
        # 1. Si total_tons es negativo (devolución), la caída es 100% + el valor absoluto
        # 2. Limitar drop_pct a un máximo razonable de 100%
        def calculate_adjusted_drop_pct(row):
            current_tons = row["total_tons"]
            avg_tons = row["avg_last_3_tons"]
            
            # Si las compras actuales son negativas (devolución/crédito)
            if current_tons < 0:
                # La caída es del 100% (dejó de comprar) más consideramos la devolución
                return 100.0
            
            # Si las compras actuales son 0
            if current_tons == 0:
                return 100.0
            
            # Calcular caída normal
            drop_pct = ((avg_tons - current_tons) / avg_tons) * 100
            
            # Limitar al rango [-100, 100] (aunque normalmente será positivo)
            return max(-100.0, min(100.0, drop_pct))
        
        latest_purchases["drop_pct"] = latest_purchases.apply(
            calculate_adjusted_drop_pct, axis=1
        )

        # Redondear valores para mejor presentación
        latest_purchases["avg_last_3_tons"] = latest_purchases["avg_last_3_tons"].round(2)
        latest_purchases["drop_pct"] = latest_purchases["drop_pct"].round(2)
        latest_purchases["drop_value"] = latest_purchases["drop_value"].round(2)
        
        # Ajustar total_tons negativos para mostrar como 0 en reportes (opcional)
        # Mantener el valor original pero añadir una columna informativa
        latest_purchases["has_return"] = latest_purchases["total_tons"] < 0
        latest_purchases["total_tons_display"] = latest_purchases["total_tons"].apply(
            lambda x: max(0, x)
        )

        # Aplicar filtros de riesgo
        df_filtered = latest_purchases.copy()

        # Solo considerar clientes con caída positiva (compra actual menor al promedio)
        # O clientes con devoluciones (valores negativos)
        df_filtered = df_filtered[
            (df_filtered["drop_value"] > 0) | (df_filtered["total_tons"] < 0)
        ]

        if df_filtered.empty:
            print("No customers showing decline in purchases")
            return pd.DataFrame()

        # Aplicar umbrales si se proporcionan
        if threshold_pct is not None and threshold_pct > 0:
            df_filtered = df_filtered[df_filtered["drop_pct"] >= threshold_pct]
            print(
                f"After percentage filter ({threshold_pct}%): {len(df_filtered)} customers"
            )

        if threshold_value is not None and threshold_value > 0:
            df_filtered = df_filtered[df_filtered["drop_value"] >= threshold_value]
            print(
                f"After value filter ({threshold_value}): {len(df_filtered)} customers"
            )

        # Si no hay umbrales específicos, usar valores por defecto razonables
        if (threshold_pct is None or threshold_pct <= 0) and (
            threshold_value is None or threshold_value <= 0
        ):
            # Por defecto: caída de al menos 10% o 1 tonelada
            df_filtered = df_filtered[
                (df_filtered["drop_pct"] >= 10) | (df_filtered["drop_value"] >= 1.0)
            ]
            print(
                f"Using default thresholds (10% or 1 ton): {len(df_filtered)} customers"
            )

        return df_filtered.sort_values("drop_pct", ascending=False)