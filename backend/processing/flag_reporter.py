# processing/flag_reporter.py

import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo


class FlagReporter:
    """FR06: Automatically flag significant purchase drops."""

    def __init__(self):
        self.flags = []

    def flag_significant_drops(
        self,
        aggregated_df: pd.DataFrame,
        customer_col: str,
        drop_pct_threshold: float = 30.0,
        drop_value_threshold: float = 5.0,
    ) -> pd.DataFrame:
        from .analysis_reporter import (
            AnalysisReporter,
        )  # Importar aquí para evitar ciclos

        reporter = AnalysisReporter()

        df_risk_pct = reporter.identify_at_risk_customers(
            aggregated_df, customer_col, threshold_pct=drop_pct_threshold
        )
        df_risk_val = reporter.identify_at_risk_customers(
            aggregated_df, customer_col, threshold_value=drop_value_threshold
        )

        if (df_risk_pct is None or df_risk_pct.empty) and (
            df_risk_val is None or df_risk_val.empty
        ):
            print("No significant drops detected.")
            self.flags = []
            return pd.DataFrame()

        df_risk = pd.concat(
            [df for df in [df_risk_pct, df_risk_val] if df is not None and not df.empty]
        ).drop_duplicates(subset=[customer_col])

        # Filtrar clientes del último año
        df_risk["period_dt"] = pd.to_datetime(df_risk["period"], format="%Y-%m")
        cutoff_date = (datetime.now() - pd.DateOffset(months=12)).replace(tzinfo=None)
        df_risk = df_risk[df_risk["period_dt"] >= cutoff_date]

        if df_risk.empty:
            print("No recent customers to flag (last 12 months).")
            self.flags = []
            return pd.DataFrame()

        flagged_results = []
        timestamp = datetime.now(ZoneInfo("America/Bogota")).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        for _, row in df_risk.iterrows():
            raw_last_purchase = float(row.get("total_tons", 0))
            last_purchase = max(raw_last_purchase, 0.0)
            raw_avg_last_3 = float(row.get("avg_last_3_tons", 0))
            avg_last_3 = max(raw_avg_last_3, 0.0)
            raw_drop_pct = float(row.get("drop_pct", 0))
            drop_pct = min(raw_drop_pct, 100)
            drop_value = float(row.get("drop_value", 0))

            if raw_last_purchase < 0:
                justification = (
                    f"Drop exceeded 100% due to product return "
                    f"(customer had {raw_last_purchase:.2f} tons in last period)."
                )
            else:
                justification = (
                    f"Drop of {drop_pct:.2f}% ({drop_value:.2f} tons) "
                    f"compared to avg of last 3 periods."
                )

            flagged_results.append(
                {
                    "customer_id": row[customer_col],
                    "period": str(row["period"]),
                    "last_purchase": last_purchase,
                    "avg_last_3_periods": avg_last_3,
                    "drop_pct": drop_pct,
                    "drop_value": drop_value,
                    "timestamp": timestamp,
                    "justification": justification,
                    "applied_pct_threshold": drop_pct_threshold,
                    "applied_value_threshold": drop_value_threshold,
                }
            )

        df_flags = (
            pd.DataFrame(flagged_results)
            .sort_values(by=["drop_pct", "drop_value"], ascending=[False, False])
            .reset_index(drop=True)
        )

        self.flags = df_flags.to_dict(orient="records")
        return df_flags
