# data/data_loader.py

import pandas as pd
import os
from typing import Dict, List, Optional

class DataLoader:
    """Maneja la carga de archivos y la detección/validación inicial de columnas (FR1)."""

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.customer_col: Optional[str] = None
        self.date_col: Optional[str] = None
        self.quantity_col: Optional[str] = None
        self.year_col: Optional[str] = None
        self.month_col: Optional[str] = None

    def _detect_columns(self, df: pd.DataFrame) -> bool:
        """Detecta heurísticamente los nombres de las columnas requeridas (cliente, fecha, cantidad)."""
        self.df = df
        
        # 1. Detectar Columna de Cliente
        self.customer_col = next((col for col in df.columns if any(keyword in col.lower() for keyword in ['cliente', 'clt', 'customer', 'client'])), None)
        
        # 2. Detectar Columnas de Fecha/Período
        date_columns = [col for col in df.columns if any(keyword in col.lower() for keyword in ['fecha', 'date', 'anio', 'mes', 'year', 'month'])]
        
        if 'ANIO' in df.columns and 'MES' in df.columns:
            self.date_col = 'ANIO'
            self.year_col = 'ANIO'
            self.month_col = 'MES'
        elif date_columns:
            self.date_col = date_columns[0]
            
        # 3. Detectar Columna de Cantidad (asumimos que es en KG)
        self.quantity_col = next((col for col in df.columns if any(keyword in col.lower() for keyword in ['ventas_kg', 'cantidad', 'kg', 'quantity', 'sales'])), None)
        
        return all([self.customer_col, self.date_col, self.quantity_col])

    def upload_historical_data(self, file_path: str) -> Dict[str, any]:
        """Carga datos históricos y valida los campos requeridos."""
        print("="*80)
        print("FUNCTIONAL REQUIREMENT 1: UPLOAD HISTORICAL DATA")
        print("="*80)
        result = {'success': False, 'message': '', 'data': None, 'validation_errors': []}
        
        try:
            if not os.path.exists(file_path):
                result['message'] = f"Error: File {file_path} does not exist"
                return result
            
            file_extension = file_path.lower().split('.')[-1]
            if file_extension not in ['csv', 'xlsx']:
                result['message'] = "Error: Only CSV or XLSX formats are accepted"
                return result
            
            if file_extension == 'csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
                
            if not self._detect_columns(df):
                errors = self._get_validation_errors()
                result['validation_errors'] = errors
                result['message'] = "Error: Required fields not found"
                return result
                
            self.df = df
            result['success'] = True
            result['message'] = f"Data loaded successfully: {self.df.shape[0]:,} records"
            result['data'] = {
                'totalRows': self.df.shape[0], 'totalColumns': self.df.shape[1], 'columns': list(self.df.columns)
            }
            print(f"File loaded successfully. Columns detected: Customer='{self.customer_col}', Date='{self.date_col}', Quantity='{self.quantity_col}'")
            print("🎉 UPLOAD COMPLETED SUCCESSFULLY\n" + "="*80)
        except Exception as e:
            result['message'] = f"Error loading file: {str(e)}"
            print(f"Error: {result['message']}")
            
        return result
    
    def _get_validation_errors(self) -> List[str]:
        """Devuelve una lista de campos obligatorios faltantes."""
        errors = []
        if not self.customer_col: errors.append("Customer field not found")
        if not self.date_col: errors.append("Date field not found")
        if not self.quantity_col: errors.append("Quantity field not found")
        return errors
