# Se importan las librerías necesarias.
import pandas as pd
import numpy as np
import os
from typing import Dict, Optional, Tuple
import warnings
#matplotlib para poder generar y mostrar gráficos.
import matplotlib.pyplot as plt
#librerías de Scikit-learn para Machine Learning ---
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix, classification_report

warnings.filterwarnings('ignore')


class FunctionalRequirementsAnalyzer:
    def __init__(self, csv_file: Optional[str] = None):
        self.csv_file = csv_file
        self.df = None
        self.aggregated_df = None 
        self.customer_col = None
        self.date_col = None
        self.quantity_col = None
        self.year_col = None
        self.month_col = None
    
    # ==================== FUNCTIONAL REQUIREMENT 1: UPLOAD DATA ====================
    def upload_historical_data(self, file_path: str) -> Dict[str, any]:
        print("=" * 80)
        print("FUNCTIONAL REQUIREMENT 1: UPLOAD HISTORICAL DATA")
        print("=" * 80)
        
        result = {
            'success': False, 'message': '', 'data': None, 'validation_errors': []
        }
        
        try:
            if not os.path.exists(file_path):
                result['message'] = f"Error: File {file_path} does not exist"
                return result
            
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension not in ['csv', 'xlsx']:
                result['message'] = "Error: Only CSV or XLSX formats are accepted"
                return result
            
            print(f"Loading file: {file_path}")
            if file_extension == 'csv':
                self.df = pd.read_csv(file_path)
            else:
                self.df = pd.read_excel(file_path)
            
            print(f"File loaded successfully")
            print(f"Rows: {self.df.shape[0]:,}, Columns: {self.df.shape[1]}")
            
            validation_result = self._validate_required_fields()
            if not validation_result['valid']:
                result['validation_errors'] = validation_result['errors']
                result['message'] = "Error: Required fields not found"
                return result
            
            print("Required fields validation: SUCCESSFUL")
            
            result['success'] = True
            result['message'] = f"Data loaded successfully: {self.df.shape[0]:,} records"
            result['data'] = self.df.copy()
            
            print("🎉 UPLOAD COMPLETED SUCCESSFULLY")
            print("=" * 80)
            
        except Exception as e:
            result['message'] = f"Error loading file: {str(e)}"
            print(f"Error: {result['message']}")
        
        return result
    
    def _validate_required_fields(self) -> Dict[str, any]:
        validation = {'valid': True, 'errors': []}
        if self.df is None:
            validation['valid'] = False; validation['errors'].append("Dataset not loaded"); return validation
        self._detect_columns()
        if not self.customer_col:
            validation['valid'] = False; validation['errors'].append("Customer field not found (looks for: cliente, clt, customer, client)")
        if not self.date_col:
            validation['valid'] = False; validation['errors'].append("Date field not found (looks for: fecha, date, anio, mes, year, month)")
        if not self.quantity_col:
            validation['valid'] = False; validation['errors'].append("Quantity field not found (looks for: ventas_kg, cantidad, kg, quantity, sales)")
        if not validation['valid']:
            validation['errors'].append(f"Available columns: {list(self.df.columns)}")
        return validation
    
    def _detect_columns(self):
        if self.df is None: return False
        for col in self.df.columns:
            if any(keyword in col.lower() for keyword in ['cliente', 'clt', 'customer', 'client']): self.customer_col = col; break
        date_columns = []
        for col in self.df.columns:
            if any(keyword in col.lower() for keyword in ['fecha', 'date', 'anio', 'mes', 'year', 'month']): date_columns.append(col)
        if 'ANIO' in self.df.columns and 'MES' in self.df.columns:
            self.date_col = 'ANIO'; self.year_col = 'ANIO'; self.month_col = 'MES'
        elif date_columns:
            self.date_col = date_columns[0]
        for col in self.df.columns:
            if any(keyword in col.lower() for keyword in ['ventas_kg', 'cantidad', 'kg', 'quantity', 'sales']): self.quantity_col = col; break
        return True
    
    # ==================== FUNCTIONAL REQUIREMENT 2: AGGREGATE DATA ====================
    def aggregate_purchases_by_customer_and_period(self, period: str = 'month', custom_period: Optional[str] = None) -> Dict[str, any]:
        print("=" * 80)
        print("FUNCTIONAL REQUIREMENT 2: AGGREGATE DATA")
        print("=" * 80)
        
        result = {'success': False, 'message': '', 'aggregated_data': None, 'validation_passed': False}
        
        try:
            if self.df is None:
                result['message'] = "Error: Must load data first"; return result
            
            print(f"Aggregating data by customer and period: {period}")
            df_work = self.df.copy()
            
            if hasattr(self, 'year_col') and self.year_col and self.month_col in df_work.columns:
                df_work['date'] = pd.to_datetime(df_work[self.year_col].astype(str) + '-' + df_work[self.month_col].astype(str).str.zfill(2) + '-01')
            elif self.date_col in df_work.columns:
                df_work['date'] = pd.to_datetime(df_work[self.date_col])
            else:
                result['message'] = "Cannot create date column."; return result
            
            if period == 'month': df_work['period'] = df_work['date'].dt.to_period('M'); period_label = 'Month'
            elif period == 'quarter': df_work['period'] = df_work['date'].dt.to_period('Q'); period_label = 'Quarter'
            elif period == 'year': df_work['period'] = df_work['date'].dt.to_period('Y'); period_label = 'Year'
            elif period == 'custom' and custom_period: df_work['period'] = df_work['date'].dt.to_period(custom_period); period_label = f'Period ({custom_period})'
            else: result['message'] = "Invalid period."; return result
            
            aggregated = df_work.groupby([self.customer_col, 'period']).agg({self.quantity_col: ['sum']}).round(4)
            aggregated.columns = ['total_kg']
            aggregated = aggregated.reset_index()
            aggregated['total_tons'] = aggregated['total_kg'] / 1000

            self.aggregated_df = aggregated.copy()
            
            result['success'] = True
            result['message'] = f"Aggregation successful: {len(aggregated):,} records"
            result['aggregated_data'] = aggregated
            
            print("🎉 AGGREGATION COMPLETED SUCCESSFULLY")
            print("=" * 80)
            
        except Exception as e:
            result['message'] = f"Error in aggregation: {str(e)}"; print(f"Error: {result['message']}")
        
        return result

    # ==================== FUNCTIONAL REQUIREMENT 3: VISUALIZE CUSTOMER TRENDS ====================
    def visualize_customer_trends(self, customer_id: str, chart_type: str = 'line', start_date_str: Optional[str] = None, end_date_str: Optional[str] = None):
        
        print("=" * 80)
        print(f"FUNCTIONAL REQUIREMENT 3: VISUALIZING TRENDS FOR CUSTOMER {customer_id}")
        print("=" * 80)

        if self.aggregated_df is None:
            print("Error: Primero debes agregar los datos (opción 2)."); return

        customer_data = self.aggregated_df[self.aggregated_df[self.customer_col] == customer_id].copy()

        if customer_data.empty:
            print(f"Error: No se encontraron datos para el cliente ID '{customer_id}'."); return

        customer_data['period_dt'] = customer_data['period'].dt.to_timestamp()
        
        try:
            if start_date_str:
                start_date = pd.to_datetime(start_date_str)
                customer_data = customer_data[customer_data['period_dt'] >= start_date]
            if end_date_str:
                end_date = pd.to_datetime(end_date_str)
                customer_data = customer_data[customer_data['period_dt'] <= end_date]
        except ValueError:
            print("Advertencia: Formato de fecha inválido (debe ser YYYY-MM). Se ignorará el filtro de fecha.")

        if customer_data.empty:
            print(f"Error: No se encontraron datos para el cliente '{customer_id}' en el rango de fechas especificado."); return
            
        customer_data = customer_data.sort_values('period_dt')

        plt.figure(figsize=(12, 6))
        
        if chart_type == 'bar':
            plt.bar(customer_data['period_dt'], customer_data['total_tons'], color='skyblue', label=f'Compras (Toneladas) de {customer_id}')
        else:
            plt.plot(customer_data['period_dt'], customer_data['total_tons'], marker='o', linestyle='-', color='b', label=f'Compras (Toneladas) de {customer_id}')

        plt.title(f'Tendencia de Compras (Toneladas) para Cliente: {customer_id}')
        plt.xlabel('Período'); plt.ylabel('Total Comprado (Toneladas)')
        plt.grid(True, linestyle='--', linewidth=0.5); plt.xticks(rotation=45)
        plt.legend(); plt.tight_layout()

        print("Mostrando gráfico... Cierra la ventana del gráfico para continuar.")
        plt.show()

    # ==================== FUNCTIONAL REQUIREMENT 4: IDENTIFY AT-RISK ====================
    def identify_at_risk_customers(self, threshold_pct: Optional[float] = None, threshold_value: Optional[float] = None):
        
        print("=" * 80)
        print("FUNCTIONAL REQUIREMENT 4: IDENTIFYING AT-RISK CUSTOMERS")
        if threshold_pct is not None:
            print(f"Umbral de caída porcentual definido: {threshold_pct}%")
        if threshold_value is not None:
            print(f"Umbral de caída de valor definido: {threshold_value} toneladas")
        print("=" * 80)

        if self.aggregated_df is None:
            print("Error: Primero debes agregar los datos (opción 2)."); return

        df_risk = self.aggregated_df.copy()
        df_risk = df_risk.sort_values([self.customer_col, 'period'])

        df_risk['avg_last_3_tons'] = df_risk.groupby(self.customer_col)['total_tons'].transform(
            lambda x: x.rolling(window=3, min_periods=1).mean().shift(1)
        )
        
        latest_purchases = df_risk.loc[df_risk.groupby(self.customer_col)['period'].idxmax()].copy()
        
        latest_purchases['drop_pct'] = np.where(
            latest_purchases['avg_last_3_tons'] > 0,
            ((latest_purchases['avg_last_3_tons'] - latest_purchases['total_tons']) / latest_purchases['avg_last_3_tons']) * 100,
            0
        )
        latest_purchases['drop_value'] = latest_purchases['avg_last_3_tons'] - latest_purchases['total_tons']

        at_risk = pd.DataFrame()
        if threshold_pct is not None:
            at_risk = latest_purchases[latest_purchases['drop_pct'] >= threshold_pct]
        elif threshold_value is not None:
            at_risk = latest_purchases[latest_purchases['drop_value'] >= threshold_value]

        print("\n--- ¡ALERTA! Clientes en Riesgo Detectados ---")
        if not at_risk.empty:
            display_cols = {
                self.customer_col: 'Cliente', 'period': 'Último Período',
                'total_tons': 'Última Compra (Ton)', 'avg_last_3_tons': 'Promedio Anterior (Ton)',
                'drop_pct': '% Caída', 'drop_value': 'Caída (Ton)'
            }
            print(at_risk[list(display_cols.keys())].rename(columns=display_cols).to_string(index=False))
        else:
            print("No se encontraron clientes que cumplan con el criterio de riesgo.")
        print("=" * 80)

    # ==================== FUNCTIONAL REQUIREMENT 4: TRAIN AND PREDICT RISK - RANDOM FOREST ====================
    def train_and_predict_churn_with_rf(self, inactivity_periods: int = 3, test_size: float = 0.2):
        """
        Implementa el ciclo completo de Machine Learning para predecir el riesgo de abandono.
        """
        print("=" * 80)
        print("FR5: TRAIN MODEL AND PREDICT RISK (RANDOM FOREST)")
        print("=" * 80)

        if self.aggregated_df is None:
            print("Error: You must aggregate data first (option 2).")
            return
        
        period_frequency = self.aggregated_df['period'].iloc[0].freq.name
        if period_frequency not in ['M', 'ME']:
            print("\nError: The Random Forest model requires data to be aggregated monthly.")
            print(f"Current aggregation is based on a '{period_frequency}' period.")
            print("--> Please run option 2 again and choose the 'month' aggregation before running the model.")
            return

        try:
            # --- FASE 1: INGENIERÍA DE CARACTERÍSTICAS ---
            print("[PHASE 1] Creating features from aggregated data...")
            
            df_model = self.aggregated_df.set_index(['period', self.customer_col])['total_tons'].unstack(fill_value=0).asfreq('M', fill_value=0).stack().reset_index()
            
            df_model.columns = ['period', self.customer_col, 'total_tons']
            df_model = df_model.sort_values([self.customer_col, 'period'])

            df_model['avg_tons_last_3'] = df_model.groupby(self.customer_col)['total_tons'].transform(lambda x: x.rolling(3, 1).mean().shift(1))
            df_model['std_tons_last_3'] = df_model.groupby(self.customer_col)['total_tons'].transform(lambda x: x.rolling(3, 1).std().shift(1))
            
            last_purchase = df_model.loc[df_model['total_tons'] > 0].groupby(self.customer_col)['period'].max()
            df_model['last_purchase_period'] = df_model[self.customer_col].map(last_purchase)
            df_model['periods_since_last_purchase'] = (df_model['period'] - df_model['last_purchase_period']).apply(lambda x: x.n if pd.notna(x) else 0)

            df_model['churn'] = (df_model['periods_since_last_purchase'] >= inactivity_periods).astype(int)
            df_model = df_model.fillna(0)

            # --- FASE 2: PREPARACIÓN Y ENTRENAMIENTO ---
            print("\n[PHASE 2] Preparing data and training Random Forest model...")
            features = ['total_tons', 'avg_tons_last_3', 'std_tons_last_3', 'periods_since_last_purchase']
            target = 'churn'
            X = df_model[features]
            y = df_model[target]
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
            
            model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
            model.fit(X_train, y_train)
            
            # --- FASE 3: EVALUACIÓN ---
            print("\n[PHASE 3] Evaluating model performance...")
            y_pred = model.predict(X_test)
            print("\n--- Model Evaluation Report ---")
            print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
            print(classification_report(y_test, y_pred))
            print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
            print("---------------------------------")
            
            feature_importances = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
            print("\nFeature Importances for Churn Prediction:")
            print(feature_importances)
            
            # --- FASE 4: PREDICCIÓN ---
            print("\n[PHASE 4] Predicting churn risk for current customers...")
            df_current = df_model.loc[df_model.groupby(self.customer_col)['period'].idxmax()].copy()
            current_predictions_proba = model.predict_proba(df_current[features])[:, 1]
            df_current['churn_probability'] = current_predictions_proba
            at_risk_customers = df_current[df_current['churn_probability'] > 0.5].sort_values('churn_probability', ascending=False)

            print("\n--- ACTION REQUIRED! Customers with High Churn Risk ---")
            if not at_risk_customers.empty:
                display_cols = [self.customer_col, 'churn_probability', 'periods_since_last_purchase', 'total_tons']
                print(at_risk_customers[display_cols].to_string(index=False))
            else:
                print("Good news! No customers show a high risk of churn at this moment.")
            print("=" * 80)
            
        except Exception as e:
            print("\n--- An error occurred during model training or prediction ---")
            print(f"Error details: {e}")
            print("Please check your data or the model parameters.")


def main():
    """
    Función principal actualizada para incluir el modelo de Machine Learning.
    """
    print("CUSTOMER CHURN RISK ANALYSIS SYSTEM")
    print("=" * 80)
    
    analyzer = FunctionalRequirementsAnalyzer()
    
    while True:
        print("\n" + "=" * 80)
        print("FUNCTIONAL REQUIREMENTS MENU")
        print("=" * 80)
        print("1. Upload historical data (CSV/XLSX)")
        print("2. Aggregate data by customer and period")
        print("3. Visualize customer purchase trends")
        print("4. Identify at-risk customers (Rule-Based)")
        print("5. Predict churn risk (Random Forest Model)")
        print("6. Exit")
        print("=" * 80)
        
        option = input("\nSelect an option (1-6): ").strip()
        
        if option == "1":
            print("\n--- UPLOAD HISTORICAL DATA ---")
            file_path = input("Enter file path (or press Enter for 'ventas_anonimizadas.csv'): ").strip()
            if not file_path: file_path = 'ventas_anonimizadas.csv'
            analyzer.upload_historical_data(file_path)
            
        elif option == "2":
            print("\n--- AGGREGATE DATA ---")
            if analyzer.df is None: print("Must load data first (option 1)"); continue
            print("Available periods: month, quarter, year, custom")
            period = input("Select period (default 'month'): ").strip().lower()
            if not period: period = 'month'
            custom_period = None
            if period == 'custom': custom_period = input("Enter custom period (e.g., W, 2W): ").strip()
            analyzer.aggregate_purchases_by_customer_and_period(period, custom_period)

        elif option == "3":
            print("\n--- VISUALIZE CUSTOMER TRENDS ---")
            if analyzer.aggregated_df is None: print("You must aggregate data first (option 2)."); continue
            customer_id = input("Enter the Customer ID to visualize: ").strip()
            if not customer_id: print("Customer ID cannot be empty."); continue
            
            start_date = input("Enter start date (YYYY-MM, optional, press Enter to skip): ").strip()
            end_date = input("Enter end date (YYYY-MM, optional, press Enter to skip): ").strip()

            chart_type = input("Enter chart type ('line' or 'bar', default 'line'): ").strip().lower()
            if chart_type not in ['line', 'bar']: chart_type = 'line'
            analyzer.visualize_customer_trends(customer_id, chart_type, start_date, end_date)

        elif option == "4":
            print("\n--- IDENTIFY AT-RISK CUSTOMERS ---")
            if analyzer.aggregated_df is None: print("You must aggregate data first (option 2)."); continue
            
            threshold_type = input("Choose threshold type ('percentage' or 'value', default 'percentage'): ").strip().lower()
            
            try:
                if threshold_type == 'value':
                    threshold_str = input("Enter the purchase drop threshold in Tons (e.g., 50): ").strip()
                    threshold = float(threshold_str)
                    analyzer.identify_at_risk_customers(threshold_value=threshold)
                else:
                    threshold_str = input("Enter the purchase drop threshold % (default 30.0): ").strip()
                    threshold = float(threshold_str) if threshold_str else 30.0
                    analyzer.identify_at_risk_customers(threshold_pct=threshold)
            except ValueError:
                print("Invalid threshold. Please enter a valid number.")

        elif option == "5":
            print("\n--- PREDICT CHURN RISK (RANDOM FOREST) ---")
            if analyzer.aggregated_df is None: print("You must aggregate data first (option 2)."); continue
            
            try:
                inactivity_str = input("Enter inactivity periods to define churn (default 3): ").strip()
                inactivity = int(inactivity_str) if inactivity_str else 3
                
                analyzer.train_and_predict_churn_with_rf(inactivity_periods=inactivity)
            except ValueError:
                print("Invalid number. Please enter an integer.")

        elif option == "6":
            print("\nThank you for using the system!")
            break
            
        else:
            print("Invalid option. Please select a valid option.")


if __name__ == "__main__":
    main()

