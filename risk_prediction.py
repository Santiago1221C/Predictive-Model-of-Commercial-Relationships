import pandas as pd
import numpy as np
import os
from typing import Dict, Optional
import warnings
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

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
        self.model = None

    # FUNCTIONAL REQUIREMENT 1: UPLOAD HISTORICAL DATA
    def upload_historical_data(self, file_path: str) -> Dict[str, any]:
        print("="*80)
        print("FUNCTIONAL REQUIREMENT 1: UPLOAD HISTORICAL DATA")
        print("="*80)
        result = {'success': False, 'message': '', 'data': None, 'validation_errors': []}
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
            print(f"File loaded successfully\nRows: {self.df.shape[0]:,}, Columns: {self.df.shape[1]}")
            validation_result = self._validate_required_fields()
            if not validation_result['valid']:
                result['validation_errors'] = validation_result['errors']
                result['message'] = "Error: Required fields not found"
                return result
            print("Required fields validation: SUCCESSFUL")
            result['success'] = True
            result['message'] = f"Data loaded successfully: {self.df.shape[0]:,} records"
            result['data'] = {
                'totalRows': self.df.shape[0], 'totalColumns': self.df.shape[1], 'columns': list(self.df.columns)
            }
            print("🎉 UPLOAD COMPLETED SUCCESSFULLY\n" + "="*80)
        except Exception as e:
            result['message'] = f"Error loading file: {str(e)}"
            print(f"Error: {result['message']}")
        return result

    # ==================== FUNCTIONAL REQUIREMENT 2: AGGREGATE DATA ====================
    def aggregate_purchases_by_customer_and_period(self, period: str = 'month', custom_period: Optional[str] = None) -> Dict[str, any]:
        print("=" * 80)
        print("FUNCTIONAL REQUIREMENT 2: AGGREGATE DATA")
        print("=" * 80)
        
        result = {'success': False, 'message': '', 'aggregated_data': None}
        
        try:
            if self.df is None:
                result['message'] = "Error: Must load data first"
                return result
            
            print(f"Aggregating data by customer and period: {period}")
            df_work = self.df.copy()
            
            if hasattr(self, 'year_col') and self.year_col and self.month_col in df_work.columns:
                df_work['date'] = pd.to_datetime(df_work[self.year_col].astype(str) + '-' + df_work[self.month_col].astype(str).str.zfill(2) + '-01')
            elif self.date_col in df_work.columns:
                df_work['date'] = pd.to_datetime(df_work[self.date_col])
            else:
                result['message'] = "Cannot create date column."
                return result
            
            period_map = {'month': 'M', 'quarter': 'Q', 'year': 'Y'}
            if period in period_map:
                df_work['period'] = df_work['date'].dt.to_period(period_map[period])
            elif period == 'custom' and custom_period:
                df_work['period'] = df_work['date'].dt.to_period(custom_period)
            else:
                result['message'] = "Invalid period."
                return result
            
            aggregated = df_work.groupby([self.customer_col, 'period']).agg({self.quantity_col: 'sum'}).round(4)
            aggregated.columns = ['total_kg']
            aggregated = aggregated.reset_index()
            aggregated['total_tons'] = aggregated['total_kg'] / 1000

            if 'period' in aggregated.columns:
                aggregated['period'] = aggregated['period'].astype(str)

            self.aggregated_df = aggregated.copy()
            
            result['success'] = True
            result['message'] = f"Aggregation successful: {len(aggregated):,} records"
            result['aggregated_data'] = aggregated
            
            print("🎉 AGGREGATION COMPLETED SUCCESSFULLY")
            print("=" * 80)
            
        except Exception as e:
            result['message'] = f"Error in aggregation: {str(e)}"
            print(f"Error: {result['message']}")
        
        return result

    # FUNCTIONAL REQUIREMENT 3: VISUALIZE CUSTOMER TRENDS
    def visualize_customer_trends(self, customer_id: str, start_date_str: Optional[str] = None, end_date_str: Optional[str] = None) -> pd.DataFrame:
        print(f"Getting trend data for customer {customer_id}...")

        if self.aggregated_df is None:
            return pd.DataFrame()

        customer_data = self.aggregated_df[self.aggregated_df[self.customer_col] == customer_id].copy()

        if customer_data.empty:
            return pd.DataFrame()

        customer_data['period_dt'] = pd.to_datetime(customer_data['period'])
        
        try:
            if start_date_str:
                start_date = pd.to_datetime(start_date_str)
                customer_data = customer_data[customer_data['period_dt'] >= start_date]
            if end_date_str:
                end_date = pd.to_datetime(end_date_str)
                customer_data = customer_data[customer_data['period_dt'] <= end_date]
        except ValueError:
            print("Warning: Invalid date format. Date filter will be ignored.")

        if customer_data.empty:
            return pd.DataFrame()

        return customer_data.sort_values('period_dt')

    # FUNCTIONAL REQUIREMENT 4: IDENTIFY AT-RISK CUSTOMERS
    def identify_at_risk_customers(self, threshold_pct: Optional[float] = None, threshold_value: Optional[float] = None) -> pd.DataFrame:
        print("Identifying at-risk customers...")
        if self.aggregated_df is None:
            return pd.DataFrame()
        df_risk = self.aggregated_df.copy().sort_values([self.customer_col, 'period'])
        df_risk['avg_last_3_tons'] = df_risk.groupby(self.customer_col)['total_tons'].transform(lambda x: x.rolling(3, 1).mean().shift(1))
        latest_purchases = df_risk.loc[df_risk.groupby(self.customer_col)['period'].idxmax()].copy()
        latest_purchases['drop_pct'] = np.where(latest_purchases['avg_last_3_tons'] > 0, ((latest_purchases['avg_last_3_tons'] - latest_purchases['total_tons']) / latest_purchases['avg_last_3_tons']) * 100, 0)
        latest_purchases['drop_value'] = latest_purchases['avg_last_3_tons'] - latest_purchases['total_tons']
        if threshold_pct is not None:
            return latest_purchases[latest_purchases['drop_pct'] >= threshold_pct]
        if threshold_value is not None:
            return latest_purchases[latest_purchases['drop_value'] >= threshold_value]
        return pd.DataFrame()

    # ==================== FUNCTIONAL REQUIREMENT 5: TRAIN AND PREDICT RISK - RANDOM FOREST ====================
    def train_and_predict_churn_with_rf(self, test_size: float = 0.2) -> Dict:
        print("=" * 80)
        print("FR5: TRAIN MODEL AND PREDICT RISK (RANDOM FOREST)")
        print("=" * 80)

        if self.aggregated_df is None:
            return {'success': False, 'message': "Error: You must aggregate data first."}
        
        try:
            print("[PHASE 1] Creating features from aggregated data...")
            df_model = self.aggregated_df.set_index(['period', self.customer_col])['total_tons'].unstack(fill_value=0).asfreq('M', fill_value=0).stack().reset_index()
            df_model.columns = ['period', self.customer_col, 'total_tons']
            df_model = df_model.sort_values([self.customer_col, 'period'])

            df_model['avg_tons_last_3'] = df_model.groupby(self.customer_col)['total_tons'].transform(lambda x: x.rolling(3, 1).mean().shift(1))
            df_model['std_tons_last_3'] = df_model.groupby(self.customer_col)['total_tons'].transform(lambda x: x.rolling(3, 1).std().shift(1))
            last_purchase = df_model.loc[df_model['total_tons'] > 0].groupby(self.customer_col)['period'].max()
            df_model['last_purchase_period'] = df_model[self.customer_col].map(last_purchase)
            df_model['periods_since_last_purchase'] = (pd.to_datetime(df_model['period']) - pd.to_datetime(df_model['last_purchase_period'])).dt.days // 30
            df_model = df_model.fillna(0)

            inactive_periods = df_model[df_model['periods_since_last_purchase'] > 0]['periods_since_last_purchase']
            
            if not inactive_periods.empty:
                dynamic_threshold = inactive_periods.quantile(0.75)
            else:
                dynamic_threshold = 3 

            inactivity_periods_adjusted = max(1, dynamic_threshold)
            print(f"\n[INFO] Dynamic inactivity threshold calculated: {inactivity_periods_adjusted:.0f} periods will be considered for churn.")

            df_model['churn'] = (df_model['periods_since_last_purchase'] >= inactivity_periods_adjusted).astype(int)

            print("\n[PHASE 2] Preparing data and training Random Forest model...")
            features = ['total_tons', 'avg_tons_last_3', 'std_tons_last_3', 'periods_since_last_purchase']
            target = 'churn'
            X = df_model[features]
            y = df_model[target]
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
            self.model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
            self.model.fit(X_train, y_train)

            print("\n[PHASE 3] Evaluating model performance...")
            y_pred = self.model.predict(X_test)
            report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            feature_importances = pd.Series(self.model.feature_importances_, index=features).sort_values(ascending=False)
            
            print("\n[PHASE 4] Predicting churn risk for current customers...")
            df_current = df_model.loc[df_model.groupby(self.customer_col)['period'].idxmax()].copy()
            probabilities = self.model.predict_proba(df_current[features])
            df_current['churn_probability'] = probabilities[:, 1] if probabilities.shape[1] == 2 else 0
            at_risk_customers = df_current[df_current['churn_probability'] > 0.5].sort_values('churn_probability', ascending=False)
            
            print("🎉 PREDICTION COMPLETED SUCCESSFULLY")
            return {
                'success': True,
                'evaluation': { 'report': report, 'confusion_matrix': confusion_matrix(y_test, y_pred).tolist() },
                'feature_importances': feature_importances.to_dict(),
                'predictions': at_risk_customers[[self.customer_col, 'churn_probability', 'periods_since_last_purchase', 'total_tons']].to_dict('records')
            }
        except Exception as e:
            print(f"\n--- An error occurred during model training or prediction ---\nError details: {e}")
            return {'success': False, 'message': str(e)}

    def _validate_required_fields(self) -> Dict[str, any]:
        validation = {'valid': True, 'errors': []}
        if self.df is None:
            validation['valid'] = False
            validation['errors'].append("Dataset not loaded")
            return validation
        self._detect_columns()
        if not self.customer_col:
            validation['valid'] = False
            validation['errors'].append("Customer field not found")
        if not self.date_col:
            validation['valid'] = False
            validation['errors'].append("Date field not found")
        if not self.quantity_col:
            validation['valid'] = False
            validation['errors'].append("Quantity field not found")
        return validation

    def _detect_columns(self):
        if self.df is None:
            return False
        for col in self.df.columns:
            if any(keyword in col.lower() for keyword in ['cliente', 'clt', 'customer', 'client']):
                self.customer_col = col
                break
        date_columns = [col for col in self.df.columns if any(keyword in col.lower() for keyword in ['fecha', 'date', 'anio', 'mes', 'year', 'month'])]
        if 'ANIO' in self.df.columns and 'MES' in self.df.columns:
            self.date_col = 'ANIO'
            self.year_col = 'ANIO'
            self.month_col = 'MES'
        elif date_columns:
            self.date_col = date_columns[0]
        for col in self.df.columns:
            if any(keyword in col.lower() for keyword in ['ventas_kg', 'cantidad', 'kg', 'quantity', 'sales']):
                self.quantity_col = col
                break
        return True

def main():
    pass

if __name__ == "__main__":
    pass