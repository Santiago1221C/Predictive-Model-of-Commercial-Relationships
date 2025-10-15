# api.py
# IMPORTANTE: Este archivo espera que el orquestador esté en processing/analyzer.py

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import sys
import os

# Agregar el directorio actual al path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from processing.analyzer import FunctionalRequirementsAnalyzer
from datetime import datetime
from werkzeug.utils import secure_filename
import warnings

# Suprimir advertencias de sklearn/pandas para una consola más limpia
warnings.filterwarnings('ignore')

app = Flask(__name__)
# Permite que el frontend React se comunique con el API
CORS(app) 
analyzer = FunctionalRequirementsAnalyzer()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =======================================================
# UTILITY
# =======================================================

def load_default_data_if_needed():
    """Carga los datos por defecto si el analizador no tiene un DataFrame cargado."""
    global analyzer
    if analyzer.df is None:
        print("\n[INFO] Analyzer initialized without data. Attempting to load 'ventas_anonimizadas.csv'...")
        
        # Construir la ruta relativa al directorio raíz del proyecto:
        # (Directorio de api.py -> subir un nivel -> nombre del archivo)
        default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ventas_anonimizadas.csv')
        
        # Cargar los datos. Asumimos que el archivo existe en la ruta.
        result = analyzer.upload_historical_data(default_path)
        
        if not result['success']:
            print(f"[ERROR] Failed to load default data: {result['message']}")
            return False
        return True
    return True

# =======================================================
# API ENDPOINTS
# =======================================================

@app.route('/api/upload', methods=['POST'])
def handle_upload():
    """FR1: Carga datos desde un archivo CSV subido por el usuario o usa el archivo predeterminado."""
    global analyzer
    
    # Verificar si se debe usar el archivo predeterminado
    if request.is_json:
        data = request.get_json()
        if data.get('use_default', False):
            # Usar archivo predeterminado
            default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ventas_anonimizadas.csv')
            
            if not os.path.exists(default_path):
                return jsonify({'success': False, 'message': 'Archivo predeterminado no encontrado'})
            
            # Reiniciar el analizador y cargar el archivo predeterminado
            analyzer = FunctionalRequirementsAnalyzer()
            result = analyzer.upload_historical_data(default_path)

            if result['success'] and analyzer.df is not None:
                result['message'] = 'Datos predeterminados cargados exitosamente'
                result['filename'] = 'ventas_anonimizadas.csv'
                customers = analyzer.df[analyzer.customer_col].unique().tolist()
                result['customers'] = customers

            return jsonify(result)
    
    # Lógica original para archivos subidos
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    # Asegurar nombre seguro y ruta temporal
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, filename)
    file.save(file_path)

    # Reiniciar el analizador y cargar el archivo
    analyzer = FunctionalRequirementsAnalyzer()
    result = analyzer.upload_historical_data(file_path)

    # Agregar lista de clientes
    if result['success'] and analyzer.df is not None:
        customers = analyzer.df[analyzer.customer_col].unique().tolist()
        result['customers'] = customers
        result['filename'] = filename

    return jsonify(result)

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Obtiene la lista de clientes disponibles."""
    global analyzer
    
    if analyzer.df is None:
        if not load_default_data_if_needed():
            return jsonify({'success': False, 'message': 'No data available.'})
    
    result = analyzer.get_available_customers()
    return jsonify(result)

@app.route('/api/aggregate', methods=['POST'])
def handle_aggregate():
    """FR2: Agrega los datos por cliente y período especificado."""
    global analyzer
    
    # Cargar datos por defecto si es necesario
    if analyzer.df is None:
        if not load_default_data_if_needed():
            return jsonify({'success': False, 'message': 'No data available. Please upload data first.'})
    
    data = request.get_json()
    period = data.get('period', 'month')
    
    result = analyzer.aggregate_customer_data(period)
    return jsonify(result)

@app.route('/api/visualize', methods=['POST'])
def visualize():
    """FR3: Visualiza tendencias de compra por cliente con filtros de fecha."""
    global analyzer
    
    try:
        # Cargar datos por defecto si es necesario
        if analyzer.aggregated_df is None:
            return jsonify({'success': False, 'error': 'No hay datos agregados disponibles. Por favor, agregue los datos primero.'}), 400
        
        payload = request.get_json()
        chart_type = payload.get('chart_type', 'line')
        customer_id = payload.get('customer_id', None)
        start_date = payload.get('start_date', None)
        end_date = payload.get('end_date', None)
        
        if not customer_id:
            return jsonify({'success': False, 'error': 'El ID del cliente es requerido'}), 400
        
        # Usar el nombre correcto de la columna del cliente desde analyzer.customer_col
        customer_col = analyzer.customer_col
        
        # Obtener lista de clientes disponibles
        available_customers = analyzer.aggregated_df[customer_col].unique().tolist()
        
        # Validar que el cliente existe
        if customer_id not in available_customers:
            return jsonify({
                'success': False, 
                'error': f'Cliente "{customer_id}" no encontrado en los datos agregados.',
                'available_customers': available_customers[:10],  # Mostrar primeros 10
                'total_customers': len(available_customers)
            }), 404
        
        # Debug: Imprimir las columnas disponibles
        print(f"Available columns: {analyzer.aggregated_df.columns.tolist()}")
        print(f"Searching for customer: {customer_id}")
        
        # Filtrar datos agregados por cliente
        customer_data = analyzer.aggregated_df[analyzer.aggregated_df[customer_col] == customer_id].copy()
        
        if customer_data.empty:
            return jsonify({
                'success': False, 
                'error': f'No se encontraron datos para el cliente: {customer_id}'
            }), 404
        
        # Convertir period_dt a datetime si no lo está
        import pandas as pd
        customer_data['period_dt'] = pd.to_datetime(customer_data['period_dt'])
        
        # Guardar el rango de fechas original
        original_min_date = customer_data['period_dt'].min()
        original_max_date = customer_data['period_dt'].max()
        original_count = len(customer_data)
        
        print(f"Original data range: {original_min_date} to {original_max_date} ({original_count} records)")
        
        # Aplicar filtro de fechas si se proporcionan
        if start_date:
            start_date_dt = pd.to_datetime(start_date)
            customer_data = customer_data[customer_data['period_dt'] >= start_date_dt]
            print(f"After start_date filter: {len(customer_data)} records")
        
        if end_date:
            end_date_dt = pd.to_datetime(end_date)
            customer_data = customer_data[customer_data['period_dt'] <= end_date_dt]
            print(f"After end_date filter: {len(customer_data)} records")
        
        # Validar que haya datos después del filtro
        if customer_data.empty:
            return jsonify({
                'success': False, 
                'error': f'No se encontraron datos en el rango de fechas especificado.\n\n' +
                         f'Rango disponible: {original_min_date.strftime("%Y-%m-%d")} a {original_max_date.strftime("%Y-%m-%d")}\n' +
                         f'Rango solicitado: {start_date or "Inicio"} a {end_date or "Fin"}\n' +
                         f'Total de registros sin filtro: {original_count}',
                'available_date_range': {
                    'min': original_min_date.strftime("%Y-%m-%d"),
                    'max': original_max_date.strftime("%Y-%m-%d"),
                    'total_records': original_count
                }
            }), 404
        
        # Ordenar por fecha
        customer_data = customer_data.sort_values('period_dt')
        
        # Convertir period_dt a string para JSON
        customer_data['period_dt'] = customer_data['period_dt'].dt.strftime('%Y-%m-%d')
        
        # Determinar el nombre correcto de la columna de toneladas
        # Buscar columnas que contengan 'ton' o 'quantity' o 'cantidad'
        tons_col = None
        for col in customer_data.columns:
            col_lower = col.lower()
            if 'ton' in col_lower or 'quantity' in col_lower or 'cantidad' in col_lower:
                tons_col = col
                break
        
        # Si no se encuentra, usar la primera columna numérica después de period_dt y customer_col
        if tons_col is None:
            numeric_cols = customer_data.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                tons_col = numeric_cols[0]
        
        if tons_col is None:
            return jsonify({'success': False, 'error': 'No se encontró ninguna columna numérica para visualizar'}), 500
        
        print(f"Using column for visualization: {tons_col}")
        
        # Preparar datos para el gráfico
        chart_data = customer_data[['period_dt', tons_col]].copy()
        chart_data = chart_data.rename(columns={tons_col: 'total_tons'})
        chart_data = chart_data.to_dict('records')
        
        return jsonify({
            'success': True,
            'data': chart_data,
            'chart_type': chart_type,
            'customer_id': customer_id,
            'total_records': len(chart_data),
            'date_range': {
                'start': customer_data['period_dt'].iloc[0] if len(customer_data) > 0 else None,
                'end': customer_data['period_dt'].iloc[-1] if len(customer_data) > 0 else None
            }
        })
    
    except Exception as e:
        print(f"Error in visualize: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Error interno del servidor: {str(e)}'}), 500


@app.route('/api/identify-risk', methods=['POST'])
def handle_identify_risk():
    """FR4: Identifica los 10 clientes con mayor riesgo."""
    global analyzer
    
    # Cargar datos por defecto si es necesario
    if analyzer.aggregated_df is None:
        return jsonify({'success': False, 'message': 'No aggregated data available. Please aggregate data first.'})
    
    data = request.get_json()
    threshold_pct = data.get('thresholdPct')
    threshold_value = data.get('thresholdValue')
    
    result = analyzer.identify_at_risk_customers(threshold_pct, threshold_value)
    return jsonify(result)

@app.route('/api/predict-risk', methods=['POST'])
def handle_predict_risk():
    """FR5: Predice los 10 clientes con mayor riesgo usando ML."""
    global analyzer
    
    # Cargar datos por defecto si es necesario
    if analyzer.aggregated_df is None:
        return jsonify({'success': False, 'message': 'No aggregated data available. Please aggregate data first.'})
    
    result = analyzer.predict_churn_risk()
    return jsonify(result)

@app.route('/api/flag-drops', methods=['POST'])
def handle_flag_drops():
    """FR6: Marca clientes con caídas significativas en compras."""
    global analyzer
    
    # Cargar datos por defecto si es necesario
    if analyzer.aggregated_df is None:
        return jsonify({'success': False, 'message': 'No aggregated data available. Please aggregate data first.'})
    
    data = request.get_json()
    threshold_pct = data.get('thresholdPct', 30.0)
    threshold_value = data.get('thresholdValue', None)
    
    result = analyzer.flag_significant_drops(threshold_pct, threshold_value)
    return jsonify(result)

@app.route('/api/download-flags', methods=['GET'])
def download_flags():
    """Descarga el reporte de clientes marcados como CSV."""
    global analyzer
    
    if not hasattr(analyzer, 'flagged_customers') or analyzer.flagged_customers is None:
        return jsonify({'success': False, 'message': 'No flagged customers available. Please run flag-drops first.'})
    
    # Generar CSV en memoria
    from io import StringIO
    import pandas as pd
    
    output = StringIO()
    analyzer.flagged_customers.to_csv(output, index=False)
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=flagged_customers.csv"}
    )

if __name__ == '__main__':
    # No se intenta cargar datos por defecto aquí, la carga se realiza en los endpoints si es necesario.
    print("Starting Flask API server...")
    # Ejecutar en el puerto 5000
    app.run(debug=True, port=5000)