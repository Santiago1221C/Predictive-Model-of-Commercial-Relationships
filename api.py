# api.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from risk_prediction import FunctionalRequirementsAnalyzer
import pandas as pd

app = Flask(__name__)
CORS(app)
analyzer = FunctionalRequirementsAnalyzer()

@app.route('/api/upload', methods=['POST'])
def handle_upload():
    body = request.get_json()
    file_path = body.get('filePath', 'ventas_anonimizadas.csv')
    result = analyzer.upload_historical_data(file_path)
    if result['success'] and analyzer.df is not None:
        customers = analyzer.df[analyzer.customer_col].unique().tolist()
        result['customers'] = customers
    return jsonify(result)

@app.route('/api/aggregate', methods=['POST'])
def handle_aggregate():
    body = request.get_json()
    period = body.get('period', 'month')
    custom_period = body.get('customPeriod')
    result = analyzer.aggregate_purchases_by_customer_and_period(period, custom_period)

    if result['success'] and result['aggregated_data'] is not None:
        df = result['aggregated_data']

        if 'period' in df.columns:
            df['period'] = df['period'].astype(str)
        
        result['aggregated_data'] = df.to_dict(orient='records')

    return jsonify(result)

@app.route('/api/visualize', methods=['POST'])
def handle_visualize():
    body = request.get_json()
    df_trends = analyzer.visualize_customer_trends(
        customer_id=body.get('customerId'),
        start_date_str=body.get('startDate'),
        end_date_str=body.get('endDate')
    )
    if not df_trends.empty:
        df_trends['period_dt'] = df_trends['period_dt'].dt.strftime('%Y-%m-%d')
        return jsonify(df_trends.to_dict('records'))
    return jsonify([])

@app.route('/api/identify-risk', methods=['POST'])
def handle_identify_risk():
    body = request.get_json()
    df_risk = analyzer.identify_at_risk_customers(
        threshold_pct=body.get('thresholdPct'),
        threshold_value=body.get('thresholdValue')
    )
    if not df_risk.empty:
        display_cols = {
            analyzer.customer_col: 'Client', 'period': 'Last Period', 'total_tons': 'Last Purchase (Tons)',
            'avg_last_3_tons': 'Previous Average (Tons)', 'drop_pct': '% Drop', 'drop_value': 'Drop (Tons)'
        }
        df_risk['period'] = df_risk['period'].astype(str)
        return jsonify(df_risk[list(display_cols.keys())].rename(columns=display_cols).to_dict('records'))
    return jsonify([])

@app.route('/api/predict-risk', methods=['POST'])
def handle_predict_risk():
    result = analyzer.train_and_predict_churn_with_rf()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)