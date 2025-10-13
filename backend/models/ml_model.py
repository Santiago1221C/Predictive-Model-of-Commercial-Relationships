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
        self.granularity: str = 'M'  # Por defecto mensual

    def train_and_predict_churn_with_rf(
        self, 
        aggregated_df: pd.DataFrame, 
        customer_col: str, 
        test_size: float = 0.2,
        granularity: str = 'M'
    ) -> Dict:
        """
        Entrena un modelo Random Forest para predecir el riesgo de abandono.
        
        Args:
            aggregated_df: DataFrame con datos agregados
            customer_col: Nombre de la columna de cliente
            test_size: Proporción de datos para testing
            granularity: 'M' para mensual, 'Q' para trimestral
        """
        self.granularity = granularity
        granularity_name = 'mensual' if granularity == 'M' else 'trimestral'
        period_days = 30 if granularity == 'M' else 90
        
        print("=" * 80)
        print(f"FR5: TRAIN MODEL AND PREDICT RISK (RANDOM FOREST) - Análisis {granularity_name.upper()}")
        print("=" * 80)

        try:
            # --- FASE 1: Ingeniería de Características ---
            print(f"[INFO] Configurando análisis con granularidad: {granularity_name}")
            
            # Resample de datos para tener una fila por cliente por período, rellenando vacíos con 0
            df_model = aggregated_df.set_index(['period', customer_col])['total_tons'].unstack(fill_value=0).asfreq(granularity, fill_value=0).stack().reset_index()
            df_model.columns = ['period', customer_col, 'total_tons']
            df_model = df_model.sort_values([customer_col, 'period'])

            # Ajustar ventanas de análisis según granularidad
            window_size = 3 if granularity == 'M' else 4  # 3 meses o 4 trimestres
            
            # Cálculo de características (basadas en Recencia, Frecuencia)
            df_model['avg_tons_last_n'] = df_model.groupby(customer_col)['total_tons'].transform(
                lambda x: x.rolling(window_size, 1).mean().shift(1)
            )
            df_model['std_tons_last_n'] = df_model.groupby(customer_col)['total_tons'].transform(
                lambda x: x.rolling(window_size, 1).std().shift(1)
            )
            
            last_purchase = df_model.loc[df_model['total_tons'] > 0].groupby(customer_col)['period'].max()
            df_model['last_purchase_period'] = df_model[customer_col].map(last_purchase)
            
            # Períodos desde la última compra (ajustado a granularidad)
            df_model['periods_since_last_purchase'] = (
                pd.to_datetime(df_model['period']) - pd.to_datetime(df_model['last_purchase_period'])
            ).dt.days // period_days
            
            df_model = df_model.fillna(0)

            # --- Definición del Objetivo de Abandono (Umbral Dinámico) ---
            inactive_periods = df_model[df_model['periods_since_last_purchase'] > 0]['periods_since_last_purchase']
            # Ajustar umbral según granularidad
            base_quantile = 0.75 if granularity == 'M' else 0.70
            dynamic_threshold = inactive_periods.quantile(base_quantile) if not inactive_periods.empty else (3 if granularity == 'M' else 2)
            inactivity_periods_adjusted = max(1, round(dynamic_threshold))
            
            print(f"[INFO] Umbral dinámico de inactividad calculado: {inactivity_periods_adjusted:.0f} períodos {granularity_name}es se considerarán como abandono.")

            df_model['churn'] = (df_model['periods_since_last_purchase'] >= inactivity_periods_adjusted).astype(int)

            # ========== DIAGNÓSTICO COMPLETO ==========

            print(f"\n{'='*80}")
            print(f"📊 DIAGNÓSTICO DETALLADO DEL DATASET")
            print(f"{'='*80}")

            # 1. Balance de clases
            churn_counts = df_model['churn'].value_counts()
            print(f"\n BALANCE DE CLASES:")
            print(f"Total registros: {len(df_model):,}")
            print(f"Churn = 1 (abandonaron): {churn_counts.get(1, 0):,} ({churn_counts.get(1, 0)/len(df_model)*100:.2f})")
            print(f"Churn = 0 (activos): {churn_counts.get(0, 0):,} ({churn_counts.get(0, 0)/len(df_model)*100:.2f})")

            # 2. Distribución de periodos de inactividad
            print(f"\n DISTRIBUCIÓN DE PERÍODOS DE INACTIVIDAD:")
            print(f"Mínimo: {df_model['periods_since_last_purchase'].min():.1f} períodos")
            print(f"Máximo: {df_model['periods_since_last_purchase'].max():.1f} períodos")
            print(f"Promedio: {df_model['periods_since_last_purchase'].mean():.1f} períodos")
            print(f"Mediana: {df_model['periods_since_last_purchase'].median():.1f} períodos")

            # 3. Clientes únicos y su comportamiento
            unique_customers = df_model[customer_col].nunique()
            print(f"\n ANÁLISIS DE CLIENTES")
            print(f"Clientes únicos: {unique_customers:,}")
            print(f"Registros por cliente (promedio): {len(df_model)/unique_customers:.1f}")

            # 4. Distribución de inactividad por perecentiles
            print(f"\n PERCENTILES DE INACTIVIDAD:")
            for p in [25, 50, 75, 90, 95, 99]:
                value = df_model['periods_since_last_purchase'].quantile(p/100)
                print(f"{p}%: {value:.1f} períodos")
            
            # 5. Clientes realmente inactivos
            inactive_threshold = df_model['periods_since_last_purchase'].quantile(0.75)
            really_inactive = df_model[df_model['periods_since_last_purchase'] > inactive_threshold]
            print(f"\n CLIENTES CON INACTIVIDAD ALTA (>75 percentil = {inactive_threshold:.1f}):")
            print(f"Cantidad: {len(really_inactive):,}")
            print(f"Porcentaje: {len(really_inactive)/len(df_model)*100:.2f}%")

            print(f"\n{'='*80}\n")

            # --- FASE 2: Entrenamiento del Modelo ---
            features = ['total_tons', 'avg_tons_last_n', 'std_tons_last_n', 'periods_since_last_purchase']
            target = 'churn'
            
            # Asegurar que haya suficientes datos para entrenar
            X = df_model.dropna(subset=features)
            X = X[X[target].isin([0, 1])].copy()
            
            if X.shape[0] < 20:
                raise Exception(f"Insufficient data for training after feature engineering (rows: {X.shape[0]}).")
                
            y = X[target]
            X = X[features]
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
            self.model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
            self.model.fit(X_train, y_train)

            # --- FASE 3: Evaluación ---
            y_pred = self.model.predict(X_test)
            report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            conf_matrix_result = confusion_matrix(y_test, y_pred)  # ← Cambio de nombre
            feature_importances = pd.Series(self.model.feature_importances_, index=features).sort_values(ascending=False)
            
            # --- FASE 4: Predicción para Clientes Actuales ---
            df_current = df_model.loc[df_model.groupby(customer_col)['period'].idxmax()].copy()
            
            if df_current.empty:
                raise Exception("No current records found for prediction.")

            # Aplicar predicción
            probabilities = self.model.predict_proba(df_current[features])
            df_current['churn_probability'] = probabilities[:, 1] if probabilities.shape[1] == 2 else 0
            
            # Ordenar por probabilidad
            all_current_predictions = df_current.sort_values('churn_probability', ascending=False)
            
            # --- FASE 5: Análisis Automático ---
            from models.churn_analyzer import ChurnAnalyzer
            
            analyzer = ChurnAnalyzer(granularity=granularity)
            analysis = analyzer.generate_comprehensive_analysis(
                predictions=all_current_predictions[[customer_col, 'churn_probability', 'periods_since_last_purchase', 'total_tons']].to_dict('records'),
                model_metrics={'report': report, 'confusion_matrix': conf_matrix_result.tolist()},  # ← Usar la variable correcta
                feature_importances=feature_importances.to_dict()
            )
            
            print(f"\n🎉 PREDICCIÓN COMPLETADA EXITOSAMENTE - Análisis {granularity_name.upper()}")
            print(f"📊 {analysis['executive_summary']['total_customers']} clientes analizados")
            print(f"⚠️  {analysis['executive_summary']['high_risk_count']} en riesgo alto ({analysis['executive_summary']['high_risk_percentage']}%)")
            
            return {
                'success': True,
                'granularity': granularity,
                'granularity_name': granularity_name,
                'evaluation': { 
                    'report': report, 
                    'confusion_matrix': conf_matrix_result.tolist()  # ← Usar la variable correcta
                },
                'feature_importances': feature_importances.to_dict(),
                'predictions': all_current_predictions[[customer_col, 'churn_probability', 'periods_since_last_purchase', 'total_tons']].to_dict('records'),
                'analysis': analysis  # ← NUEVO: Análisis automático completo
            }
            
        except Exception as e:
            print(f"\n--- An error occurred during model training or prediction ---\nError details: {e}")
            return {'success': False, 'message': str(e)}