# api.py
# IMPORTANTE: Este archivo espera que el orquestador esté en processing/analyzer.py

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import pandas as pd
from processing.analyzer import FunctionalRequirementsAnalyzer
import warnings
import os
import io
from datetime import datetime
from zoneinfo import ZoneInfo
from werkzeug.utils import secure_filename
import json
import numpy as np

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
            # Si falla, el analizador.df seguirá siendo None y el endpoint devolverá 400.
            print(f"[WARNING] Failed to load default data: {result['message']}")


# =======================================================
# API ENDPOINTS
# =======================================================

@app.route('/api/upload', methods=['POST'])
def handle_upload():
    """FR1: Carga datos desde un archivo CSV subido por el usuario."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part in request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400

    # Asegurar nombre seguro y ruta temporal
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, filename)
    file.save(file_path)

    # Reiniciar el analizador y cargar el archivo
    global analyzer
    analyzer = FunctionalRequirementsAnalyzer()
    result = analyzer.upload_historical_data(file_path)

    # Agregar lista de clientes
    if result['success'] and analyzer.df is not None:
        customer_col = analyzer.customer_col
        if customer_col:
            result['customers'] = analyzer.df[customer_col].unique().tolist()
        else:
            result['success'] = False
            result['message'] = "File loaded, but customer column could not be detected."

    # Opcional: eliminar el archivo temporal después de cargarlo
    try:
        os.remove(file_path)
    except OSError:
        pass

    return jsonify(result)


@app.route('/api/aggregate', methods=['POST'])
def handle_aggregate():
    """FR2: Agrega datos por período (mes, trimestre, año)."""
    load_default_data_if_needed() 
    if analyzer.df is None:
        return jsonify({'success': False, 'message': 'No data loaded. Please upload data first.'}), 400
        
    body = request.get_json()
    period = body.get('period', 'month')
    custom_period = body.get('customPeriod')
    
    result = analyzer.aggregate_purchases_by_customer_and_period(period, custom_period)

    if result['success'] and result['aggregated_data'] is not None:
        # Eliminamos 'aggregated_data' del resultado JSON, solo necesitamos el estado de éxito.
        del result['aggregated_data'] 
        result['message'] += f" | Period: {period}"

    return jsonify(result)

@app.route('/api/visualize', methods=['POST'])
def handle_visualize():
    """FR3: Devuelve datos de tendencia para un cliente específico."""
    load_default_data_if_needed()
    if analyzer.aggregated_df is None:
        # Si no hay df agregado, se asume que aún no se ha agregado la data por primera vez. 
        # Si load_default_data_if_needed() fue exitoso, el df ya no es None.
        return jsonify({'success': False, 'message': 'Data must be aggregated before visualization.'}), 400
        
    body = request.get_json()
    df_trends = analyzer.visualize_customer_trends(
        customer_id=body.get('customerId'),
        start_date_str=body.get('startDate'),
        end_date_str=body.get('endDate')
    )
    if not df_trends.empty:
        df_trends['period_dt'] = df_trends['period_dt'].dt.strftime('%Y-%m-%d')
        # Solo necesitamos el período y el total de toneladas para el gráfico
        return jsonify(df_trends[['period_dt', 'total_tons']].to_dict('records'))
        
    return jsonify({'success': True, 'data': [], 'message': 'No trend data found for this customer/period.'})

@app.route('/api/identify-risk', methods=['POST'])
def handle_identify_risk():
    """FR4: Identifica clientes en riesgo utilizando reglas de umbral simple (caída vs. promedio anterior)."""
    try:
        load_default_data_if_needed()
        if analyzer.df is None:
            return jsonify({'success': False, 'message': 'No data loaded. Please upload data first.'}), 400
        
        if analyzer.aggregated_df is None:
            return jsonify({'success': False, 'message': 'Data must be aggregated before identifying risk.'}), 400
            
        body = request.get_json()
        print(f"[DEBUG] Request body: {body}")
        
        # Validar y convertir parámetros
        threshold_pct = body.get('thresholdPct')
        threshold_value = body.get('thresholdValue')
        
        # Convertir a float si es string, manejar valores None o vacíos
        try:
            threshold_pct = float(threshold_pct) if threshold_pct not in [None, '', 0] else None
        except (ValueError, TypeError):
            threshold_pct = None
            
        try:
            threshold_value = float(threshold_value) if threshold_value not in [None, '', 0] else None
        except (ValueError, TypeError):
            threshold_value = None
        
        print(f"[DEBUG] Risk analysis parameters - Percentage: {threshold_pct}, Value: {threshold_value}")
        print(f"[DEBUG] Aggregated data shape: {analyzer.aggregated_df.shape}")
        print(f"[DEBUG] Customer column: {analyzer.customer_col}")
        
        df_risk = analyzer.identify_at_risk_customers(
            threshold_pct=threshold_pct,
            threshold_value=threshold_value
        )
        
        print(f"[DEBUG] Risk customers found: {len(df_risk)}")
        
        if not df_risk.empty:
            # Preparar datos para el frontend
            display_cols = {
                analyzer.customer_col: 'Client', 
                'period': 'Last Period', 
                'total_tons': 'Last Purchase (Tons)',
                'avg_last_3_tons': 'Previous Avg (Tons)', 
                'drop_pct': '% Drop', 
                'drop_value': 'Drop (Tons)'
            }
            
            # Convertir period a string para JSON serialization
            df_risk = df_risk.copy()
            df_risk['period'] = df_risk['period'].dt.strftime('%Y-%m-%d') if pd.api.types.is_datetime64_any_dtype(df_risk['period']) else df_risk['period'].astype(str)
            
            # Seleccionar y renombrar columnas
            risk_data = df_risk[list(display_cols.keys())].rename(columns=display_cols).to_dict('records')
            
            result = {
                'success': True, 
                'data': risk_data, 
                'customer_col': analyzer.customer_col,
                'total_at_risk': len(risk_data),
                'message': f'Found {len(risk_data)} customers at risk'
            }
            print(f"[DEBUG] Returning success result with {len(risk_data)} customers")
            return jsonify(result)
            
        result = {
            'success': True, 
            'data': [], 
            'total_at_risk': 0,
            'message': 'No customers met the specified risk criteria.'
        }
        print(f"[DEBUG] No customers at risk found")
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] Exception in identify_risk: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Error processing risk analysis: {str(e)}'
        }), 500

@app.route('/api/predict-risk', methods=['POST'])
def handle_predict_risk():
    """FR5: Entrena el modelo ML y predice la probabilidad de abandono con análisis automático."""
    import numpy as np
    import json
    
    load_default_data_if_needed()
    if analyzer.aggregated_df is None:
        return jsonify({'success': False, 'message': 'Data must be aggregated before ML prediction.'}), 400
    
    # Obtener granularidad desde el request
    body = request.get_json() or {}
    granularity = body.get('granularity', 'M')
    
    # Validar granularidad
    if granularity not in ['M', 'Q']:
        return jsonify({'success': False, 'message': 'Invalid granularity. Use "M" for monthly or "Q" for quarterly.'}), 400
    
    print(f"[INFO] Iniciando predicción con granularidad: {granularity}")
    result = analyzer.train_and_predict_churn_with_rf(granularity=granularity)
    
    if result['success']:
        # Función para limpiar NaN/Inf recursivamente
        def clean_data(obj):
            if isinstance(obj, float):
                if np.isnan(obj) or np.isinf(obj):
                    return 0
            elif isinstance(obj, dict):
                return {k: clean_data(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_data(item) for item in obj]
            elif isinstance(obj, pd.DataFrame):
                return clean_data(obj.fillna(0).replace([np.inf, -np.inf], 0).to_dict('records'))
            return obj
        
        # Limpiar predictions
        if 'predictions' in result:
            predictions_df = pd.DataFrame(result['predictions'])
            predictions_df = predictions_df.fillna(0).replace([np.inf, -np.inf], 0)
            predictions_df['churn_probability_formatted'] = predictions_df['churn_probability'].apply(lambda x: f"{x*100:.2f}%")
            predictions_df['total_tons'] = predictions_df['total_tons'].round(2)
            result['predictions_formatted'] = predictions_df.to_dict('records')
        
        # Limpiar evaluation report
        if 'evaluation' in result and 'report' in result['evaluation']:
            report_df = pd.DataFrame(result['evaluation']['report']).T.reset_index()
            report_df.columns = ['Metric', 'Precision', 'Recall', 'F1-Score', 'Support']
            report_df = report_df.fillna(0).replace([np.inf, -np.inf], 0)
            result['evaluation_report'] = report_df.to_dict('records')
        
        # Limpiar todo el resultado
        result = clean_data(result)
        
        print(f"[SUCCESS] Análisis completado y limpiado")
    
    # Convertir a JSON string y luego de vuelta para asegurar validez
    try:
        json_str = json.dumps(result, allow_nan=False, default=str)
        return Response(json_str, mimetype='application/json')
    except ValueError as e:
        print(f"[ERROR] JSON serialization error: {e}")
        return jsonify({'success': False, 'message': f'Error serializing result: {str(e)}'}), 500

@app.route('/api/flag-drops', methods=['POST'])
def handle_flag_drops():
    """Flag customers with significant purchase drops."""
    load_default_data_if_needed()
    if analyzer.aggregated_df is None:
        return jsonify({'success': False, 'message': 'Data must be aggregated first.'}), 400

    body = request.get_json()
    drop_pct = float(body.get('thresholdPct', 30.0))
    drop_value = float(body.get('thresholdValue', 5.0))

    df_flags = analyzer.flag_significant_drops(drop_pct_threshold=drop_pct, drop_value_threshold=drop_value)
    if df_flags.empty:
        return jsonify({'success': True, 'data': [], 'message': 'No significant drops detected.'})

    return jsonify(df_flags.to_dict(orient='records'))

@app.route('/api/download-flags', methods=['GET'])
def download_flags():
    """Descargar flags generados como CSV."""
    if not hasattr(analyzer.flagger, "flags") or not analyzer.flagger.flags:
        return jsonify({"error": "No flags generated yet"}), 400

    df_flags = pd.DataFrame(analyzer.flagger.flags)
    csv_buffer = io.StringIO()
    df_flags.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    csv_buffer.seek(0)

    filename = f"flags_{datetime.now(ZoneInfo('America/Bogota')).strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(csv_buffer.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})

@app.route('/api/get-analysis', methods=['GET'])
def handle_get_analysis():
    """Obtiene el último análisis generado sin re-entrenar el modelo."""
    if not hasattr(analyzer, 'predictor') or analyzer.predictor is None:
        return jsonify({
            'success': False, 
            'message': 'No analysis available. Please run prediction first.'
        }), 400
    
    if not hasattr(analyzer.predictor, 'analyzer') or analyzer.predictor.analyzer is None:
        return jsonify({
            'success': False,
            'message': 'Analysis not found. Please run prediction again.'
        }), 400
    
    # Aquí podrías almacenar el último resultado en una variable de instancia
    # Por ahora, indica que deben llamar al endpoint de predicción
    return jsonify({
        'success': False,
        'message': 'Please call /api/predict-risk to generate fresh analysis.'
    }), 400

if __name__ == '__main__':
    # No se intenta cargar datos por defecto aquí, la carga se realiza en los endpoints si es necesario.
    print("Starting Flask API server...")
    # Ejecutar en el puerto 5000
    app.run(debug=True, port=5000)