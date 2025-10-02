# models/ml_model.py

import pandas as pd
from typing import Dict, Optional
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import warnings

warnings.filterwarnings('ignore')

class ChurnPredictor:
    """FR5: Maneja el entrenamiento y la predicción de abandono de clientes utilizando Random Forest."""

    def __init__(self):
        self.model: Optional[RandomForestClassifier] = None

    def train_and_predict_churn_with_rf(self, aggregated_df: pd.DataFrame, customer_col: str, test_size: float = 0.2) -> Dict:
        """Entrena un modelo Random Forest para predecir el riesgo de abandono."""
        print("=" * 80)
        print("FR5: TRAIN MODEL AND PREDICT RISK (RANDOM FOREST)")
        print("=" * 80)

        try:
            # --- FASE 1: Ingeniería de Características ---
            # Resample de datos para tener una fila por cliente por período, rellenando vacíos con 0
            df_model = aggregated_df.set_index(['period', customer_col])['total_tons'].unstack(fill_value=0).asfreq('M', fill_value=0).stack().reset_index()
            df_model.columns = ['period', customer_col, 'total_tons']
            df_model = df_model.sort_values([customer_col, 'period'])

            # Cálculo de características (basadas en Recencia, Frecuencia)
            df_model['avg_tons_last_3'] = df_model.groupby(customer_col)['total_tons'].transform(lambda x: x.rolling(3, 1).mean().shift(1))
            df_model['std_tons_last_3'] = df_model.groupby(customer_col)['total_tons'].transform(lambda x: x.rolling(3, 1).std().shift(1))
            
            last_purchase = df_model.loc[df_model['total_tons'] > 0].groupby(customer_col)['period'].max()
            df_model['last_purchase_period'] = df_model[customer_col].map(last_purchase)
            # Días desde la última compra, convertido a períodos de 30 días
            df_model['periods_since_last_purchase'] = (pd.to_datetime(df_model['period']) - pd.to_datetime(df_model['last_purchase_period'])).dt.days // 30
            df_model = df_model.fillna(0)

            # --- Definición del Objetivo de Abandono (Umbral Dinámico) ---
            inactive_periods = df_model[df_model['periods_since_last_purchase'] > 0]['periods_since_last_purchase']
            # Definir abandono como el 75 percentil de inactividad observada
            dynamic_threshold = inactive_periods.quantile(0.75) if not inactive_periods.empty else 3 
            inactivity_periods_adjusted = max(1, round(dynamic_threshold))
            print(f"[INFO] Dynamic inactivity threshold calculated: {inactivity_periods_adjusted:.0f} periods will be considered for churn.")

            df_model['churn'] = (df_model['periods_since_last_purchase'] >= inactivity_periods_adjusted).astype(int)

            # --- FASE 2: Entrenamiento del Modelo ---
            features = ['total_tons', 'avg_tons_last_3', 'std_tons_last_3', 'periods_since_last_purchase']
            target = 'churn'
            X = df_model.dropna(subset=features)[features]
            y = df_model.dropna(subset=features)[target]
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
            self.model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
            self.model.fit(X_train, y_train)

            # --- FASE 3: Evaluación ---
            y_pred = self.model.predict(X_test)
            report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            feature_importances = pd.Series(self.model.feature_importances_, index=features).sort_values(ascending=False)
            
            # --- FASE 4: Predicción para Clientes Actuales ---
            # Obtener el registro más reciente para cada cliente
            df_current = df_model.loc[df_model.groupby(customer_col)['period'].idxmax()].copy()
            probabilities = self.model.predict_proba(df_current[features])
            df_current['churn_probability'] = probabilities[:, 1] if probabilities.shape[1] == 2 else 0
            
            at_risk_customers = df_current[df_current['churn_probability'] > 0.5].sort_values('churn_probability', ascending=False)
            
            print("🎉 PREDICTION COMPLETED SUCCESSFULLY")
            return {
                'success': True,
                'evaluation': { 
                    'report': report, 
                    'confusion_matrix': confusion_matrix(y_test, y_pred).tolist() 
                },
                'feature_importances': feature_importances.to_dict(),
                'predictions': at_risk_customers[[customer_col, 'churn_probability', 'periods_since_last_purchase', 'total_tons']].to_dict('records')
            }
        except Exception as e:
            print(f"\n--- An error occurred during model training or prediction ---\nError details: {e}")
            return {'success': False, 'message': str(e)}
