import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import os
from typing import Dict, List, Optional

warnings.filterwarnings('ignore')

class DataLoader:
    """Clase para cargar y validar datos desde archivos CSV."""
    
    def __init__(self):
        self.supported_formats = ['.csv']
        print("DataLoader initialized")
        
    def load_csv(self, file_path):
        """
        Carga un archivo CSV y detecta automáticamente las columnas principales.
        
        Args:
            file_path (str): Ruta al archivo CSV
            
        Returns:
            dict: Resultado con dataframe y metadatos
        """
        try:
            print(f"Loading CSV file: {file_path}")
            
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                return {'success': False, 'message': f'Archivo no encontrado: {file_path}'}
            
            # Leer el archivo CSV
            df = pd.read_csv(file_path)
            print(f"CSV loaded successfully. Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            if df.empty:
                return {'success': False, 'message': 'El archivo está vacío'}
            
            # Detectar columnas automáticamente
            column_mapping = self._detect_columns(df)
            
            if not column_mapping['success']:
                return column_mapping
            
            # Validar y limpiar datos
            cleaned_df = self._clean_data(df, column_mapping)
            
            print(f"Data cleaned successfully. Final shape: {cleaned_df.shape}")
            
            return {
                'success': True,
                'dataframe': cleaned_df,
                'customer_col': column_mapping['customer_col'],
                'date_col': column_mapping['date_col'],
                'quantity_col': column_mapping['quantity_col'],
                'total_rows': len(cleaned_df),
                'total_columns': len(cleaned_df.columns),
                'message': 'Datos cargados exitosamente'
            }
            
        except Exception as e:
            error_msg = f'Error al cargar archivo: {str(e)}'
            print(f"❌ {error_msg}")
            return {'success': False, 'message': error_msg}
    
    def _detect_columns(self, df):
        """Detecta automáticamente las columnas de cliente, fecha y cantidad."""
        columns = df.columns.tolist()
        print(f"Detecting columns from: {columns}")
        
        # Palabras clave para detectar columnas (más flexibles)
        customer_keywords = ['cliente', 'customer', 'client', 'anonimo', 'id', 'code', 'codigo']
        date_keywords = ['fecha', 'date', 'anio', 'year', 'periodo', 'period', 'time', 'año']
        quantity_keywords = ['cantidad', 'quantity', 'ventas', 'sales', 'kg', 'tons', 'peso', 'weight', 'volumen', 'volume']
        
        customer_col = None
        date_col = None
        quantity_col = None
        
        # Buscar columna de cliente (búsqueda más flexible)
        for col in columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in customer_keywords):
                customer_col = col
                print(f"Customer column detected: {customer_col}")
                break
        
        # Buscar columna de fecha
        for col in columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in date_keywords):
                date_col = col
                print(f"Date column detected: {date_col}")
                break
        
        # Buscar columna de cantidad
        for col in columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in quantity_keywords):
                quantity_col = col
                print(f"Quantity column detected: {quantity_col}")
                break
        
        # Si no se detectaron automáticamente, usar inferencia basada en tipos de datos
        if not customer_col:
            # Buscar columna de texto con muchos valores únicos
            for col in columns:
                if df[col].dtype == 'object' and df[col].nunique() > len(df) * 0.1:
                    customer_col = col
                    print(f"Customer column inferred: {customer_col}")
                    break
            
            # Si aún no se encuentra, usar la primera columna de texto
            if not customer_col:
                for col in columns:
                    if df[col].dtype == 'object':
                        customer_col = col
                        print(f"Customer column defaulted: {customer_col}")
                        break
        
        if not date_col:
            # Buscar columna de fecha por tipo de dato
            for col in columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    date_col = col
                    print(f"Date column inferred by dtype: {date_col}")
                    break
            
            # Si no hay datetime, buscar columna numérica que parezca año
            if not date_col:
                for col in columns:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        unique_values = df[col].unique()
                        # Verificar si parece un año (valores entre 1900 y 2100)
                        if all(1900 <= val <= 2100 for val in unique_values if pd.notna(val)):
                            date_col = col
                            print(f"Date column inferred as year: {date_col}")
                            break
        
        if not quantity_col:
            # Buscar columna numérica que no sea fecha
            for col in columns:
                if col != date_col and pd.api.types.is_numeric_dtype(df[col]):
                    quantity_col = col
                    print(f"Quantity column inferred: {quantity_col}")
                    break
        
        # Verificación final
        if not all([customer_col, date_col, quantity_col]):
            missing = []
            if not customer_col: missing.append('cliente')
            if not date_col: missing.append('fecha') 
            if not quantity_col: missing.append('cantidad')
            
            # Mostrar información de debug
            print("Column detection failed:")
            print(f"Available columns: {columns}")
            print(f"Data types: {dict(df.dtypes)}")
            print(f"Sample data:")
            print(df.head())
            
            return {
                'success': False, 
                'message': f'No se pudieron detectar las columnas: {", ".join(missing)}. Columnas disponibles: {columns}'
            }
        
        return {
            'success': True,
            'customer_col': customer_col,
            'date_col': date_col,
            'quantity_col': quantity_col
        }
    
    def _clean_data(self, df, column_mapping):
        """Limpia y valida los datos."""
        try:
            print("Cleaning data...")
            
            # Crear una copia del dataframe
            cleaned_df = df.copy()
            
            customer_col = column_mapping['customer_col']
            date_col = column_mapping['date_col']
            quantity_col = column_mapping['quantity_col']
            
            print(f"Original data shape: {cleaned_df.shape}")
            
            # Limpiar datos nulos
            initial_count = len(cleaned_df)
            cleaned_df = cleaned_df.dropna(subset=[customer_col, date_col, quantity_col])
            print(f"After removing nulls: {cleaned_df.shape} (removed {initial_count - len(cleaned_df)} rows)")
            
            # Convertir cantidad a numérico
            cleaned_df[quantity_col] = pd.to_numeric(cleaned_df[quantity_col], errors='coerce')
            initial_count = len(cleaned_df)
            cleaned_df = cleaned_df.dropna(subset=[quantity_col])
            print(f"After converting quantity to numeric: {cleaned_df.shape} (removed {initial_count - len(cleaned_df)} rows)")
            
            # Convertir fecha si es necesario
            if not pd.api.types.is_datetime64_any_dtype(cleaned_df[date_col]):
                try:
                    # Intentar convertir año a fecha
                    if cleaned_df[date_col].dtype in ['int64', 'float64']:
                        # Verificar si son años válidos
                        if cleaned_df[date_col].min() >= 1900 and cleaned_df[date_col].max() <= 2100:
                            cleaned_df[date_col] = pd.to_datetime(cleaned_df[date_col], format='%Y')
                        else:
                            cleaned_df[date_col] = pd.to_datetime(cleaned_df[date_col])
                    else:
                        cleaned_df[date_col] = pd.to_datetime(cleaned_df[date_col])
                    print("Date column converted successfully")
                except Exception as e:
                    print(f"Warning: Could not convert date column: {e}")
                    # Si falla, intentar convertir de otra manera
                    cleaned_df[date_col] = pd.to_datetime(cleaned_df[date_col], errors='coerce')
                    cleaned_df = cleaned_df.dropna(subset=[date_col])
            
            # Filtrar cantidades negativas
            initial_count = len(cleaned_df)
            cleaned_df = cleaned_df[cleaned_df[quantity_col] > 0]
            print(f"After removing negative quantities: {cleaned_df.shape} (removed {initial_count - len(cleaned_df)} rows)")
            
            if len(cleaned_df) == 0:
                raise Exception("No hay datos válidos después de la limpieza")
            
            return cleaned_df
            
        except Exception as e:
            raise Exception(f"Error limpiando datos: {str(e)}")