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
def handle_visualize():
    """FR3: Visualiza las tendencias agregadas por cliente específico."""
    global analyzer
    
    # Cargar datos por defecto si es necesario
    if analyzer.aggregated_df is None:
        return jsonify({'success': False, 'message': 'No aggregated data available. Please aggregate data first.'})
    
    data = request.get_json()
    chart_type = data.get('chart_type', 'line')
    customer_id = data.get('customer_id', None)
    
    result = analyzer.visualize_trends(chart_type, customer_id)
    return jsonify(result)

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