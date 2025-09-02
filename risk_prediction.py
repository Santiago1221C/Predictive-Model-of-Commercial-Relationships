import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

class CustomerAnalyzer:
    """Customer analysis class that loads all data and shows monthly purchases"""
    
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.df = None
        self.rf_model = None
        self.customer_col = None
        self.date_col = None
        self.quantity_col = None
        
    def detect_columns(self):
        """Automatically detects the correct columns in the dataset"""
        print("=" * 80)
        print("AUTOMATIC COLUMN DETECTION")
        print("=" * 80)
        
        if self.df is None:
            print("Dataset not loaded yet")
            return False
            
        # Detect customer column (CLT_001, CLT_002, etc.)
        for col in self.df.columns:
            if 'clt' in col.lower():
                self.customer_col = col
                break
        
        # Detect date column
        for col in self.df.columns:
            if 'fecha' in col.lower() or 'date' in col.lower():
                self.date_col = col
                break
        
        # Detect quantity column
        for col in self.df.columns:
            if 'cantidad' in col.lower():
                self.quantity_col = col
                break
        
        print("Detected columns:")
        print(f"  Customer ID: {self.customer_col}")
        print(f"  Date: {self.date_col}")
        print(f"  Quantity: {self.quantity_col}")
        
        if not all([self.customer_col, self.date_col, self.quantity_col]):
            print("\nERROR: Could not detect all necessary columns")
            print("Available columns:")
            for i, col in enumerate(self.df.columns, 1):
                print(f"  {i:2d}. {col}")
            return False
        
        return True
    
    def load_all_data(self):
        """Loads and analyzes ALL the dataset completely"""
        print("=" * 80)
        print("COMPLETE DATASET ANALYSIS")
        print("=" * 80)
        
        try:
            self.df = pd.read_csv(self.csv_file)
            print(f"Dataset loaded successfully")
            print(f"Total rows: {self.df.shape[0]:,}")
            print(f"Total columns: {self.df.shape[1]}")
            print(f"File size: {self.df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
            
            print("\nALL COLUMNS IN THE DATASET:")
            for i, col in enumerate(self.df.columns, 1):
                print(f"{i:2d}. {col}")
            
            print("\nFIRST 10 ROWS:")
            print(self.df.head(10))
            
            print("\nLAST 10 ROWS:")
            print(self.df.tail(10))
            
            print("\nDATASET INFORMATION:")
            print(self.df.info())
            
            print("\nCOMPLETE DESCRIPTIVE STATISTICS:")
            print(self.df.describe())
            
            print("\nMISSING VALUES:")
            missing = self.df.isnull().sum()
            if missing.sum() > 0:
                for col, count in missing[missing > 0].items():
                    print(f"  {col}: {count} ({count/len(self.df)*100:.1f}%)")
            else:
                print("  No missing values found")
            
            print("\nUNIQUE VALUES PER COLUMN:")
            for col in self.df.columns:
                unique_count = self.df[col].nunique()
                print(f"  {col}: {unique_count:,} unique values")
            
            # Auto-detect columns after loading
            print("\n" + "=" * 80)
            if self.detect_columns():
                print("Column detection successful!")
            else:
                print("Column detection failed - manual review needed")
                
            return True
            
        except Exception as e:
            print(f"Error loading dataset: {e}")
            return False
    
    def convert_kg_to_tons(self):
        """Converts kg columns to tons"""
        if self.df is None:
            print("You must load the dataset first")
            return False
            
        print("\n" + "=" * 80)
        print("CONVERSION FROM KG TO TONS")
        print("=" * 80)
        
        kg_columns = [col for col in self.df.columns if 'kg' in col.lower()]
        
        if kg_columns:
            print(f"Columns found with kg: {kg_columns}")
            
            for col in kg_columns:
                new_col = f'{col}_tons'
                self.df[new_col] = self.df[col] / 1000
                print(f"Converted: {col} -> {new_col}")
                print(f"  Range: {self.df[col].min():.2f} kg - {self.df[col].max():.2f} kg")
                print(f"  Range: {self.df[new_col].min():.4f} tons - {self.df[new_col].max():.4f} tons")
        else:
            print("No columns with kg found")
            print("Available columns:")
            for col in self.df.columns:
                print(f"  - {col}")
        
        return True
    
    def analyze_customer_monthly(self, customer_id):
        """Analyzes a specific customer and shows ALL their purchases by month"""
        if self.df is None:
            print("You must load the dataset first")
            return None
        
        if not self.detect_columns():
            print("Cannot analyze customer - column detection failed")
            return None
            
        print(f"\n" + "=" * 80)
        print(f"CUSTOMER MONTHLY ANALYSIS: {customer_id}")
        print("=" * 80)
        
        print(f"Using customer column: {self.customer_col}")
        
        # Filter customer data
        customer_data = self.df[self.df[self.customer_col] == customer_id]
        
        if len(customer_data) == 0:
            print(f"No data found for customer {customer_id}")
            print(f"Available customers in {self.customer_col}:")
            available_customers = self.df[self.customer_col].unique()[:10]
            for cust in available_customers:
                print(f"  - {cust}")
            if len(self.df[self.customer_col].unique()) > 10:
                print(f"  ... and {len(self.df[self.customer_col].unique()) - 10} more customers")
            return None
        
        print(f"Customer data found: {len(customer_data)} records")
        
        try:
            # Convert to datetime
            customer_data[self.date_col] = pd.to_datetime(customer_data[self.date_col])
            
            # Create month and year columns
            customer_data['month'] = customer_data[self.date_col].dt.month
            customer_data['year'] = customer_data[self.date_col].dt.year
            customer_data['month_name'] = customer_data[self.date_col].dt.strftime('%B')
            customer_data['quarter'] = customer_data[self.date_col].dt.quarter
            
            # Create tons column if it doesn't exist
            if 'cantidad_tons' not in customer_data.columns:
                customer_data['cantidad_tons'] = customer_data[self.quantity_col] / 1000
            
            # Group by month and year
            monthly_purchases = customer_data.groupby(['year', 'month', 'month_name']).agg({
                self.quantity_col: ['sum', 'mean', 'count'],
                'cantidad_tons': ['sum', 'mean']
            }).round(4)
            
            # Flatten column names
            monthly_purchases.columns = ['_'.join(col).strip() for col in monthly_purchases.columns]
            monthly_purchases = monthly_purchases.reset_index()
            
            print(f"\nMONTHLY PURCHASES FOR CUSTOMER {customer_id}:")
            print("=" * 60)
            print("Year | Month | Total Quantity | Avg Quantity | Purchase Count | Total Tons | Avg Tons")
            print("-" * 80)
            
            for idx, row in monthly_purchases.iterrows():
                print(f"{row['year']:4d} | {row['month_name']:9s} | {row['sum']:14.2f} | {row['mean']:12.2f} | {row['count']:14d} | {row['sum_1']:10.4f} | {row['mean_1']:8.4f}")
            
            # Quarterly summary
            quarterly_purchases = customer_data.groupby(['year', 'quarter']).agg({
                self.quantity_col: 'sum',
                'cantidad_tons': 'sum'
            }).round(4)
            
            print(f"\nQUARTERLY SUMMARY:")
            print("=" * 40)
            print("Year | Quarter | Total Quantity | Total Tons")
            print("-" * 40)
            
            for idx, row in quarterly_purchases.iterrows():
                quarter_name = f"Q{row.name[1]}"
                print(f"{row.name[0]:4d} | {quarter_name:7s} | {row[self.quantity_col]:14.2f} | {row['cantidad_tons']:10.4f}")
            
            # Create visualization
            plt.figure(figsize=(15, 8))
            
            # Monthly purchases over time
            plt.subplot(2, 1, 1)
            monthly_purchases['date_label'] = monthly_purchases['year'].astype(str) + '-' + monthly_purchases['month'].astype(str).str.zfill(2)
            plt.plot(monthly_purchases['date_label'], monthly_purchases['sum'], marker='o', linewidth=2, markersize=8)
            plt.title(f'Monthly Purchases - Customer {customer_id}')
            plt.xlabel('Year-Month')
            plt.ylabel('Total Quantity')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            
            # Monthly purchase count
            plt.subplot(2, 1, 2)
            plt.bar(monthly_purchases['date_label'], monthly_purchases['count'], alpha=0.7, color='orange')
            plt.title(f'Monthly Purchase Frequency - Customer {customer_id}')
            plt.xlabel('Year-Month')
            plt.ylabel('Number of Purchases')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
            
            # Show all individual purchases
            print(f"\nALL INDIVIDUAL PURCHASES FOR CUSTOMER {customer_id}:")
            print("=" * 80)
            print("Date | Quantity | Quantity (tons) | Month | Quarter")
            print("-" * 80)
            
            sorted_purchases = customer_data.sort_values(self.date_col)
            for idx, row in sorted_purchases.iterrows():
                print(f"{row[self.date_col].strftime('%Y-%m-%d')} | {row[self.quantity_col]:8.2f} | {row['cantidad_tons']:15.4f} | {row['month_name']:5s} | Q{row['quarter']}")
            
        except Exception as e:
            print(f"Error processing data: {e}")
            import traceback
            traceback.print_exc()
        
        return customer_data
    
    def show_customer_list(self):
        """Shows list of all customers in the dataset"""
        if self.df is None:
            print("You must load the dataset first")
            return
        
        if not self.detect_columns():
            print("Cannot show customers - column detection failed")
            return
        
        print("\n" + "=" * 80)
        print("ALL CUSTOMERS IN THE DATASET")
        print("=" * 80)
        
        print(f"Using customer column: {self.customer_col}")
        
        # Get unique customers
        customers = self.df[self.customer_col].unique()
        print(f"Total unique customers: {len(customers):,}")
        
        # Show first 20 customers
        print(f"\nFirst 20 customers:")
        for i, customer in enumerate(customers[:20], 1):
            print(f"{i:2d}. {customer}")
        
        if len(customers) > 20:
            print(f"... and {len(customers) - 20:,} more customers")
        
        # Customer statistics
        customer_stats = self.df.groupby(self.customer_col).size().describe()
        print(f"\nCustomer purchase statistics:")
        print(f"  Average purchases per customer: {customer_stats['mean']:.2f}")
        print(f"  Minimum purchases per customer: {customer_stats['min']:.0f}")
        print(f"  Maximum purchases per customer: {customer_stats['max']:.0f}")
    
    def train_random_forest(self):
        """Trains basic Random Forest model"""
        if self.df is None:
            print("You must load the dataset first")
            return False
        
        if not self.detect_columns():
            print("Cannot train model - column detection failed")
            return False
            
        print("\n" + "=" * 80)
        print("RANDOM FOREST TRAINING")
        print("=" * 80)
        
        try:
            print(f"Using columns:")
            print(f"  Date: {self.date_col}")
            print(f"  Customer: {self.customer_col}")
            print(f"  Quantity: {self.quantity_col}")
            
            # Create basic features
            self.df[self.date_col] = pd.to_datetime(self.df[self.date_col])
            
            if 'cantidad_tons' not in self.df.columns:
                self.df['cantidad_tons'] = self.df[self.quantity_col] / 1000
            
            # Features per customer
            features = self.df.groupby(self.customer_col).agg({
                'cantidad_tons': ['mean', 'std', 'count']
            }).round(4)
            
            features.columns = ['quantity_mean', 'quantity_std', 'num_purchases']
            features = features.reset_index()
            
            # Target: customer at risk (decrease > 20%)
            self.df['variation'] = self.df.groupby(self.customer_col)['cantidad_tons'].pct_change() * 100
            risk = self.df.groupby(self.customer_col)['variation'].apply(
                lambda x: 1 if (x < -20).any() else 0
            ).reset_index()
            risk.columns = [self.customer_col, 'at_risk']
            
            # Join features with target
            X = features.merge(risk, on=self.customer_col)
            X_features = X[['quantity_mean', 'quantity_std', 'num_purchases']]
            y_target = X['at_risk']
            
            # Handle null values
            X_features = X_features.fillna(0)
            
            print(f"Features created: {X_features.shape[1]} columns")
            print(f"Customers analyzed: {len(X_features)}")
            print(f"Customers at risk: {y_target.sum()}")
            
            # Split and train
            X_train, X_test, y_train, y_test = train_test_split(
                X_features, y_target, test_size=0.2, random_state=42
            )
            
            # Random Forest
            self.rf_model = RandomForestClassifier(n_estimators=50, random_state=42)
            self.rf_model.fit(X_train, y_train)
            
            # Evaluate
            accuracy = self.rf_model.score(X_test, y_test)
            print(f"\nModel accuracy: {accuracy:.4f}")
            
            # Feature importance
            feature_importance = pd.DataFrame({
                'feature': X_features.columns,
                'importance': self.rf_model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print(f"\nFeature importance:")
            print(feature_importance)
            
            return True
            
        except Exception as e:
            print(f"Error in training: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main function"""
    print("CUSTOMER CHURN RISK ANALYSIS SYSTEM")
    print("FIRST COMMIT - Complete data analysis and monthly purchases")
    print("=" * 80)
    
    analyzer = CustomerAnalyzer('ventas_anonimizadas.csv')
    
    while True:
        print("\n" + "=" * 80)
        print("MAIN MENU")
        print("=" * 80)
        print("1. Load ALL dataset (complete analysis)")
        print("2. Convert kg to tons")
        print("3. Show all customers list")
        print("4. Analyze customer monthly purchases")
        print("5. Train Random Forest")
        print("6. Exit")
        print("=" * 80)
        
        option = input("\nSelect an option (1-6): ").strip()
        
        if option == "1":
            analyzer.load_all_data()
            
        elif option == "2":
            analyzer.convert_kg_to_tons()
            
        elif option == "3":
            analyzer.show_customer_list()
            
        elif option == "4":
            customer_id = input("Enter customer ID to analyze: ").strip()
            analyzer.analyze_customer_monthly(customer_id)
            
        elif option == "5":
            analyzer.train_random_forest()
            
        elif option == "6":
            print("Thank you for using the system")
            print("First commit completed - Complete data analysis implemented")
            break
            
        else:
            print("Invalid option. Please select 1-6.")

if __name__ == "__main__":
    main()