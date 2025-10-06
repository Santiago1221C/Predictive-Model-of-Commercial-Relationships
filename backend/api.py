# api.py
# IMPORTANTE: Este archivo espera que el orquestador esté en processing/analyzer.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from processing.analyzer import FunctionalRequirementsAnalyzer
import warnings
import os

# Suprimir advertencias de sklearn/pandas para una consola más limpia
warnings.filterwarnings('ignore')

app = Flask(__name__)
# Permite que el frontend React se comunique con el API
CORS(app) 
analyzer = FunctionalRequirementsAnalyzer()

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
    """FR1: Carga datos y devuelve los IDs de cliente disponibles."""
    body = request.get_json()
    # Usar 'ventas_anonimizadas.csv' como valor por defecto
    file_path = body.get('filePath', 'ventas_anonimizadas.csv')
    
    # Si el frontend envía solo el nombre del archivo por defecto, construimos la ruta absoluta
    if file_path == 'ventas_anonimizadas.csv':
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', file_path)
    
    # Resetear el analizador para una nueva carga
    global analyzer
    analyzer = FunctionalRequirementsAnalyzer()
    
    result = analyzer.upload_historical_data(file_path)
    
    if result['success'] and analyzer.df is not None:
        customer_col = analyzer.customer_col
        if customer_col:
            customers = analyzer.df[customer_col].unique().tolist()
            result['customers'] = customers
        else:
            result['message'] = "Data loaded but customer column was not detected. Check file format."
            result['success'] = False
            
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
    """FR5: Entrena el modelo ML y predice la probabilidad de abandono."""
    load_default_data_if_needed()
    if analyzer.aggregated_df is None:
        return jsonify({'success': False, 'message': 'Data must be aggregated before ML prediction.'}), 400
        
    result = analyzer.train_and_predict_churn_with_rf()
    
    if result['success']:
        predictions_df = pd.DataFrame(result['predictions'])
        predictions_df['churn_probability'] = predictions_df['churn_probability'].apply(lambda x: f"{x*100:.2f}%")
        predictions_df['total_tons'] = predictions_df['total_tons'].round(2)
        
        # Agregar los datos formateados al resultado para el frontend
        result['predictions_formatted'] = predictions_df.to_dict('records')
        
        # Formatear el reporte de evaluación para una tabla en el frontend
        report_df = pd.DataFrame(result['evaluation']['report']).T.reset_index()
        report_df.columns = ['Metric', 'Precision', 'Recall', 'F1-Score', 'Support']
        result['evaluation_report'] = report_df.to_dict('records')
        
    return jsonify(result)

if __name__ == '__main__':
    # No se intenta cargar datos por defecto aquí, la carga se realiza en los endpoints si es necesario.
    print("Starting Flask API server...")
    # Ejecutar en el puerto 5000
    app.run(debug=True, port=5000)