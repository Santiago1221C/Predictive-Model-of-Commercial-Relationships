# backend/data/data_aggregator.py

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
        """Agrega datos por cliente y un período de tiempo especificado, con validaciones y depuración."""
        print("=" * 100)
        print("FUNCTIONAL REQUIREMENT 2: AGGREGATE DATA (Debug Mode)")
        print("=" * 100)

        result = {'success': False, 'message': '', 'aggregated_data': None}

        try:
            # Copia de trabajo
            df_work = df.copy()

            print(f"📦 Total de registros recibidos: {len(df_work):,}")
            print(f"🧭 Columnas originales: {df_work.columns.tolist()}")
            print(f"➡️ Cliente: '{customer_col}' | Cantidad: '{quantity_col}' | Fecha: '{date_col}' | Año: '{year_col}' | Mes: '{month_col}'")

            # ------------------------------------------------------------------
            # 🔍 Validación inicial: columna de cantidad
            if quantity_col not in df_work.columns:
                # Fallback común
                posibles = [c for c in df_work.columns if 'venta' in c.lower() or 'ton' in c.lower() or 'kg' in c.lower()]
                result['message'] = f"❌ La columna de cantidad '{quantity_col}' no existe. Posibles columnas: {posibles}"
                print(result['message'])
                return result

            # ------------------------------------------------------------------
            # 🧮 Conversión numérica segura
            df_work[quantity_col] = (
                df_work[quantity_col]
                .astype(str)
                .str.replace(',', '.', regex=False)
                .str.replace(' ', '', regex=False)
            )
            df_work[quantity_col] = pd.to_numeric(df_work[quantity_col], errors='coerce').fillna(0)

            print("\n⚖️ Escala de la columna de cantidad antes de agregar:")
            print(df_work[quantity_col].describe())

            # ------------------------------------------------------------------
            # 🗓️ Creación de columna de fecha
            try:
                if year_col and month_col and year_col in df_work.columns and month_col in df_work.columns:
                    df_work['date'] = pd.to_datetime(
                        df_work[year_col].astype(str) + '-' + df_work[month_col].astype(str).str.zfill(2) + '-01',
                        errors='coerce'
                    )
                elif date_col and date_col in df_work.columns:
                    df_work['date'] = pd.to_datetime(df_work[date_col], errors='coerce')
                else:
                    raise ValueError("No se pudo determinar columna de fecha válida.")

                print("\n🕓 Vista previa de fechas creadas:")
                print(df_work[['date', customer_col, quantity_col]].head(10))
                print(f"Fechas nulas: {df_work['date'].isna().sum():,}")

            except Exception as e:
                result['message'] = f"❌ Error al crear la columna de fecha: {str(e)}"
                print(result['message'])
                return result

            # ------------------------------------------------------------------
            # 🧩 Cálculo del período (mes, trimestre, año)
            period_map = {'month': 'M', 'quarter': 'Q', 'year': 'Y'}
            if period in period_map:
                df_work['period'] = df_work['date'].dt.to_period(period_map[period])
            elif period == 'custom' and custom_period:
                df_work['period'] = df_work['date'].dt.to_period(custom_period)
            else:
                result['message'] = "❌ Período inválido especificado."
                print(result['message'])
                return result

            # ------------------------------------------------------------------
            # 📊 Agregación
            print("\n🔄 Iniciando agregación por cliente y período...")

            aggregated = (
                df_work.groupby([customer_col, 'period'])
                .agg({quantity_col: 'sum'})
                .round(4)
                .reset_index()
            )
            aggregated.rename(columns={quantity_col: 'total_kg'}, inplace=True)

            # ------------------------------------------------------------------
            # ⚙️ Cálculo de toneladas con validación de magnitud
            max_val = aggregated['total_kg'].max()
            if max_val <= 50:
                print("⚠️ Los valores parecen estar en TONELADAS — se omite la división entre 1000.")
                aggregated['total_tons'] = aggregated['total_kg']
            else:
                aggregated['total_tons'] = aggregated['total_kg'] / 1000

            aggregated['period'] = aggregated['period'].astype(str)

            # ------------------------------------------------------------------
            # 🔍 Diagnóstico final
            total_sum = aggregated['total_tons'].sum()
            zero_percent = (aggregated['total_tons'] == 0).mean() * 100

            print("\n📋 RESUMEN DE AGREGACIÓN")
            print(f"   Total de registros agregados: {len(aggregated):,}")
            print(f"   Total de clientes únicos: {aggregated[customer_col].nunique():,}")
            print(f"   Suma total de toneladas: {total_sum:,.2f}")
            print(f"   Porcentaje de registros con 0 ventas: {zero_percent:.2f}%")

            if total_sum == 0:
                print("🚨 ALERTA: TODAS LAS VENTAS SON 0 — verifica la columna de cantidad o las fechas.")

            print("\n✅ Columnas finales que se enviarán al modelo:", aggregated.columns.tolist())

            # ------------------------------------------------------------------
            # ✅ Resultado
            result['success'] = True
            result['message'] = f"Aggregation successful: {len(aggregated):,} records"
            result['aggregated_data'] = aggregated

            print("\n🎉 AGGREGATION COMPLETED SUCCESSFULLY")
            print("=" * 100)

        except Exception as e:
            result['message'] = f"Error in aggregation: {str(e)}"
            print(f"❌ Error: {result['message']}")
            print("=" * 100)

        return result