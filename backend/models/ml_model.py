# models/ml_model.py

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')

class MLModel:
    """Clase para modelos de Machine Learning para predicción de churn."""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
    
    def train_and_predict(self, aggregated_df, customer_col):
        """
        Entrena un modelo Random Forest y predice clientes en riesgo.
        Retorna los top 10 clientes con mayor probabilidad de churn.
        
        Args:
            aggregated_df (DataFrame): Datos agregados
            customer_col (str): Columna de cliente
            
        Returns:
            dict: Top 10 predicciones y métricas del modelo
        """
        try:
            print("Preparing data for ML model...")
            
            # Preparar características por cliente
            features_df = self._prepare_features(aggregated_df, customer_col)
            
            if len(features_df) < 10:
                return {'success': False, 'message': 'Insuficientes datos para entrenar el modelo ML (mínimo 10 clientes)'}
            
            # Crear etiquetas de churn (simplificado)
            features_df['churn'] = self._create_churn_labels(features_df)
            
            # Separar características y etiquetas
            X = features_df[self.feature_columns]
            y = features_df['churn']
            
            print(f"Training model with {len(X)} samples and {len(self.feature_columns)} features")
            print(f"Churn distribution: {y.value_counts().to_dict()}")
            
            # Dividir datos
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42, stratify=y
            )
            
            # Escalar características
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Entrenar modelo
            self.model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                class_weight='balanced'
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Hacer predicciones
            y_pred = self.model.predict(X_test_scaled)
            y_pred_proba = self.model.predict_proba(X_test_scaled)
            
            # Calcular métricas
            accuracy = accuracy_score(y_test, y_pred)
            class_report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            
            # Predecir todos los clientes
            X_all_scaled = self.scaler.transform(X)
            all_predictions = self.model.predict_proba(X_all_scaled)
            
            # Crear DataFrame con predicciones
            prediction_results = features_df.copy()
            prediction_results['churn_probability'] = all_predictions[:, 1]
            
            # Obtener top 10 clientes con mayor probabilidad de churn
            top_risk_customers = prediction_results.nlargest(10, 'churn_probability')
            
            # Preparar datos de salida
            prediction_data = []
            for _, row in top_risk_customers.iterrows():
                prediction_data.append({
                    'Customer': row[customer_col],
                    'Churn Probability (%)': round(row['churn_probability'] * 100, 2),
                    'Avg Quantity (Tons)': round(row['avg_quantity'] / 1000, 2),
                    'Quantity Trend': round(row['quantity_trend'], 3),
                    'Purchase Frequency': round(row['purchase_frequency'], 2),
                    'Periods Active': int(row['periods_active']),
                    'Risk Level': self._get_risk_level(row['churn_probability'])
                })
            
            # Obtener importancia de características
            feature_importance = dict(zip(self.feature_columns, self.model.feature_importances_))
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                'success': True,
                'predictions': prediction_data,
                'evaluation': {
                    'accuracy': accuracy,
                    'report': class_report,
                    'total_customers': len(features_df),
                    'high_risk_customers': len(top_risk_customers)
                },
                'model_info': {
                    'algorithm': 'Random Forest',
                    'features_used': self.feature_columns,
                    'training_samples': len(X_train),
                    'test_samples': len(X_test),
                    'top_features': top_features
                }
            }
            
        except Exception as e:
            error_msg = f'Error en modelo ML: {str(e)}'
            print(f"❌ {error_msg}")
            return {'success': False, 'message': error_msg}
    
    def _get_risk_level(self, probability):
        """Determina el nivel de riesgo basado en la probabilidad."""
        if probability >= 0.8:
            return 'Very High'
        elif probability >= 0.6:
            return 'High'
        elif probability >= 0.4:
            return 'Medium'
        else:
            return 'Low'
    
    def _prepare_features(self, aggregated_df, customer_col):
        """Prepara características por cliente para el modelo."""
        try:
            # Agregar por cliente
            customer_features = aggregated_df.groupby(customer_col).agg({
                'total_quantity': ['mean', 'std', 'sum', 'count'],
                'transaction_count': ['mean', 'sum'],
                'period_dt': ['count']
            })
            
            # Aplanar columnas
            customer_features.columns = [
                'avg_quantity', 'std_quantity', 'total_quantity', 'period_count',
                'avg_transactions', 'total_transactions', 'periods_active'
            ]
            
            customer_features = customer_features.reset_index()
            
            # Calcular características adicionales
            customer_features['quantity_cv'] = customer_features['std_quantity'] / customer_features['avg_quantity']
            customer_features['quantity_cv'] = customer_features['quantity_cv'].fillna(0)
            
            customer_features['purchase_frequency'] = customer_features['total_transactions'] / customer_features['periods_active']
            
            # Calcular tendencia de cantidad
            trend_data = []
            for customer in customer_features[customer_col]:
                customer_data = aggregated_df[aggregated_df[customer_col] == customer].sort_values('period_dt')
                if len(customer_data) > 1:
                    # Correlación simple con el tiempo
                    x = np.arange(len(customer_data))
                    y = customer_data['total_quantity'].values
                    trend = np.corrcoef(x, y)[0, 1] if len(set(y)) > 1 else 0
                else:
                    trend = 0
                trend_data.append(trend)
            
            customer_features['quantity_trend'] = trend_data
            customer_features['quantity_trend'] = customer_features['quantity_trend'].fillna(0)
            
            # Definir columnas de características
            self.feature_columns = [
                'avg_quantity', 'std_quantity', 'period_count',
                'avg_transactions', 'quantity_cv', 'purchase_frequency',
                'quantity_trend', 'periods_active'
            ]
            
            # Rellenar valores nulos
            for col in self.feature_columns:
                customer_features[col] = customer_features[col].fillna(0)
            
            return customer_features
            
        except Exception as e:
            raise Exception(f"Error preparando características: {str(e)}")
    
    def _create_churn_labels(self, features_df):
        """Crea etiquetas de churn basadas en heurísticas."""
        try:
            # Definir churn basado en múltiples criterios
            churn_conditions = (
                (features_df['quantity_trend'] < -0.3) |  # Tendencia negativa fuerte
                (features_df['period_count'] < 2) |       # Muy pocos períodos
                (features_df['purchase_frequency'] < 0.5) # Baja frecuencia
            )
            
            # Asegurar distribución balanceada (al menos 20% positivos)
            churn_labels = churn_conditions.astype(int)
            if churn_labels.mean() < 0.2:
                # Si hay muy pocos positivos, usar percentiles
                threshold = features_df['quantity_trend'].quantile(0.3)
                churn_labels = (features_df['quantity_trend'] <= threshold).astype(int)
            
            return churn_labels
            
        except Exception as e:
            raise Exception(f"Error creando etiquetas de churn: {str(e)}")