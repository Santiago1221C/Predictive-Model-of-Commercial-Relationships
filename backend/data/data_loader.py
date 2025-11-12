import pandas as pd
import os
from typing import Dict, List, Optional


class DataLoader:
    """Maneja la carga de archivos y la detección/validación inicial de columnas (FR1).
       Versión mejorada con soporte para centro operativo, validación robusta y logs claros.
    """

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.customer_col: Optional[str] = None
        self.date_col: Optional[str] = None
        self.quantity_col: Optional[str] = None
        self.year_col: Optional[str] = None
        self.month_col: Optional[str] = None
        self.operational_center_col: Optional[str] = None

    # --------------------------------------------------------------------------
    def _detect_columns(self, df: pd.DataFrame) -> bool:
        """Detecta heurísticamente las columnas de cliente, fecha, cantidad y centro operativo."""

        # Estandarizar nombres de columnas
        df.columns = [col.strip().lower() for col in df.columns]
        self.df = df

        # --- Detectar columna de cliente ---
        candidates_customer = ['cliente', 'client', 'customer', 'id_cliente', 'cod_cliente']
        self.customer_col = next((col for col in df.columns if any(k in col for k in candidates_customer)), None)

        # --- Detectar columnas de fecha ---
        date_candidates = ['fecha', 'date', 'periodo', 'period', 'anio', 'año', 'mes', 'month', 'year']
        detected_dates = [col for col in df.columns if any(k in col for k in date_candidates)]

        if 'anio' in df.columns and 'mes' in df.columns:
            self.year_col, self.month_col = 'anio', 'mes'
        elif 'year' in df.columns and 'month' in df.columns:
            self.year_col, self.month_col = 'year', 'month'
        elif 'fecha' in df.columns:
            self.date_col = 'fecha'
        elif 'date' in df.columns:
            self.date_col = 'date'
        elif detected_dates:
            self.date_col = detected_dates[0]

        # --- Detectar columna de cantidad ---
        candidates_quantity = ['ventas_kg', 'venta_kg', 'cantidad', 'kg', 'quantity', 'sales', 'kilos']
        self.quantity_col = next((col for col in df.columns if any(k in col for k in candidates_quantity)), None)

        # --- Detectar columna de centro operativo ---
        candidates_center = ['centro_operativo', 'operational_center']
        self.operational_center_col = next((col for col in df.columns if any(k in col for k in candidates_center)), None)

        # Validar detección
        return all([
            self.customer_col,
            (self.date_col or (self.year_col and self.month_col)),
            self.quantity_col,
            self.operational_center_col
        ])

    # --------------------------------------------------------------------------
    def upload_historical_data(self, file_path: str) -> Dict[str, any]:
        """Carga datos históricos y valida los campos requeridos."""
        print("=" * 80)
        print("FUNCTIONAL REQUIREMENT 1: UPLOAD HISTORICAL DATA (Optimized + Operational Center)")
        print("=" * 80)

        result = {'success': False, 'message': '', 'data': None, 'validation_errors': []}

        try:
            if not os.path.exists(file_path):
                result['message'] = f"File not found: {file_path}"
                return result

            ext = file_path.lower().split('.')[-1]
            if ext not in ['csv', 'xlsx']:
                result['message'] = "Only CSV or XLSX formats are accepted"
                return result

            df = pd.read_csv(file_path) if ext == 'csv' else pd.read_excel(file_path)

            # Estandarizar nombres
            df.columns = [c.strip().lower() for c in df.columns]

            # Detectar columnas automáticamente
            if not self._detect_columns(df):
                errors = self._get_validation_errors()
                result['validation_errors'] = errors
                result['message'] = "Required fields not found"
                return result

            # --- Limpieza y validación de cantidad ---
            if self.quantity_col in df.columns:
                df[self.quantity_col] = (
                    df[self.quantity_col]
                    .astype(str)
                    .str.replace(',', '.', regex=False)
                    .str.replace(' ', '', regex=False)
                )
                df[self.quantity_col] = pd.to_numeric(df[self.quantity_col], errors='coerce').fillna(0)

            # Guardar DataFrame en el objeto
            self.df = df

            # ------------------------------------------------------------------
            print(f"Columns detected:")
            print(f"   Customer: '{self.customer_col}'")
            if self.date_col:
                print(f"   Date: '{self.date_col}'")
            else:
                print(f"   Year: '{self.year_col}', Month: '{self.month_col}'")
            print(f"   Quantity: '{self.quantity_col}'")
            print(f"   Operational Center: '{self.operational_center_col}'")

            print("\nSample of loaded data:")
            print(df.head(5))

            result['success'] = True
            result['message'] = f"Data loaded successfully: {df.shape[0]:,} records"
            result['data'] = {
                'total_rows': df.shape[0],
                'total_columns': df.shape[1],
                'columns': list(df.columns),
            }

            print("\nUPLOAD COMPLETED SUCCESSFULLY\n" + "=" * 80)
            return result

        except Exception as e:
            result['message'] = f"Error loading file: {str(e)}"
            print(f"Error: {result['message']}")
            return result

    # --------------------------------------------------------------------------
    def _get_validation_errors(self) -> List[str]:
        """Devuelve una lista de campos obligatorios faltantes."""
        errors = []
        if not self.customer_col:
            errors.append("Customer field not found")
        if not (self.date_col or (self.year_col and self.month_col)):
            errors.append("Date/Year/Month field not found")
        if not self.quantity_col:
            errors.append("Quantity field not found")
        if not self.operational_center_col:
            errors.append("Operational center field not found")
        return errors
