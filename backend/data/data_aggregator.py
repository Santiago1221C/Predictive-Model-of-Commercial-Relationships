# data/data_aggregator.py

import pandas as pd
from typing import Dict, Optional

class DataAggregator:
    """Maneja la agregación de datos de compra por cliente y período (FR2)."""
    
    def aggregate_purchases_by_customer_and_period(
        self, 
        df: pd.DataFrame, 
        customer_col: str, 
        quantity_col: str, 
        date_col: Optional[str], 
        year_col: Optional[str], 
        month_col: Optional[str],
        period: str = 'month', 
        custom_period: Optional[str] = None
    ) -> Dict[str, any]:
        """Agrega datos por cliente y un período de tiempo especificado."""
        print("=" * 80)
        print("FUNCTIONAL REQUIREMENT 2: AGGREGATE DATA")
        print("=" * 80)
        
        result = {'success': False, 'message': '', 'aggregated_data': None}
        
        try:
            df_work = df.copy()
            
            print(f"Aggregating data by customer and period: {period}")
            
            # --- Lógica de Creación de Fechas ---
            if year_col and month_col in df_work.columns:
                df_work['date'] = pd.to_datetime(df_work[year_col].astype(str) + '-' + df_work[month_col].astype(str).str.zfill(2) + '-01')
            elif date_col in df_work.columns:
                df_work['date'] = pd.to_datetime(df_work[date_col])
            else:
                result['message'] = "Cannot create date column."
                return result

            # --- Lógica de Cálculo de Período ---
            period_map = {'month': 'M', 'quarter': 'Q', 'year': 'Y'}
            if period in period_map:
                df_work['period'] = df_work['date'].dt.to_period(period_map[period])
            elif period == 'custom' and custom_period:
                df_work['period'] = df_work['date'].dt.to_period(custom_period)
            else:
                result['message'] = "Invalid period."
                return result
            
            # --- Agregación ---
            aggregated = df_work.groupby([customer_col, 'period']).agg({quantity_col: 'sum'}).round(4)
            aggregated.columns = ['total_kg']
            aggregated = aggregated.reset_index()
            aggregated['total_tons'] = aggregated['total_kg'] / 1000

            if 'period' in aggregated.columns:
                aggregated['period'] = aggregated['period'].astype(str)
            
            result['success'] = True
            result['message'] = f"Aggregation successful: {len(aggregated):,} records"
            result['aggregated_data'] = aggregated
            
            print("🎉 AGGREGATION COMPLETED SUCCESSFULLY")
            print("=" * 80)
            
        except Exception as e:
            result['message'] = f"Error in aggregation: {str(e)}"
            print(f"Error: {result['message']}")
            
        return result
