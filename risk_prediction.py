import pandas as pd
import numpy as np
import os
from typing import Dict, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class FunctionalRequirementsAnalyzer:
    def __init__(self, csv_file: Optional[str] = None):
        self.csv_file = csv_file
        self.df = None
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
            'success': False,
            'message': '',
            'data': None,
            'validation_errors': []
        }
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                result['message'] = f"Error: File {file_path} does not exist"
                return result
            
            # Detect file format
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension not in ['csv', 'xlsx']:
                result['message'] = "Error: Only CSV or XLSX formats are accepted"
                return result
            
            print(f"Loading file: {file_path}")
            print(f"Format detected: {file_extension.upper()}")
            
            # Load data according to format
            if file_extension == 'csv':
                self.df = pd.read_csv(file_path)
            else:  # xlsx
                self.df = pd.read_excel(file_path)
            
            print(f"File loaded successfully")
            print(f"Rows: {self.df.shape[0]:,}")
            print(f"Columns: {self.df.shape[1]}")
            
            # Validate required fields
            validation_result = self._validate_required_fields()
            if not validation_result['valid']:
                result['validation_errors'] = validation_result['errors']
                result['message'] = "Error: Required fields not found"
                return result
            
            print("Required fields validation: SUCCESSFUL")
            print(f"Customer column: {self.customer_col}")
            print(f"Date column: {self.date_col}")
            print(f"Quantity column: {self.quantity_col}")
            
            # Confirmation of successful load
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
        """Validates that required fields exist in the dataset"""
        validation = {
            'valid': True,
            'errors': []
        }
        
        if self.df is None:
            validation['valid'] = False
            validation['errors'].append("Dataset not loaded")
            return validation
        
        # Auto-detect columns
        self._detect_columns()
        
        # Check that all necessary columns were detected
        if not self.customer_col:
            validation['valid'] = False
            validation['errors'].append("Customer field not found (looks for: cliente, clt, customer, client)")
        
        if not self.date_col:
            validation['valid'] = False
            validation['errors'].append("Date field not found (looks for: fecha, date, anio, mes, year, month)")
        
        if not self.quantity_col:
            validation['valid'] = False
            validation['errors'].append("Quantity field not found (looks for: ventas_kg, cantidad, kg, quantity, sales)")
        
        # Show available columns if there are errors
        if not validation['valid']:
            validation['errors'].append(f"Available columns: {list(self.df.columns)}")
        
        return validation
    
    def _detect_columns(self):
        """Automatically detects the correct columns in the dataset"""
        if self.df is None:
            return False
            
        # Detect customer column (CLIENTE_ANONIMO, CLT_001, CLT_002, etc.)
        for col in self.df.columns:
            if any(keyword in col.lower() for keyword in ['cliente', 'clt', 'customer', 'client']):
                self.customer_col = col
                break
        
        # Detect date columns - we have ANIO and MES, so we'll create a date
        date_columns = []
        for col in self.df.columns:
            if any(keyword in col.lower() for keyword in ['fecha', 'date', 'anio', 'mes', 'year', 'month']):
                date_columns.append(col)
        
        # For this dataset, we have ANIO and MES columns
        if 'ANIO' in self.df.columns and 'MES' in self.df.columns:
            self.date_col = 'ANIO'  # We'll use ANIO as primary date column
            self.year_col = 'ANIO'
            self.month_col = 'MES'
        elif date_columns:
            self.date_col = date_columns[0]
        
        # Detect quantity column (VENTAS_KG, cantidad, kg, etc.)
        for col in self.df.columns:
            if any(keyword in col.lower() for keyword in ['ventas_kg', 'cantidad', 'kg', 'quantity', 'sales']):
                self.quantity_col = col
                break
        
        return True
    
    # ==================== FUNCTIONAL REQUIREMENT 2: AGGREGATE DATA ====================
    def aggregate_purchases_by_customer_and_period(self, period: str = 'month', custom_period: Optional[str] = None) -> Dict[str, any]:
        print("=" * 80)
        print("FUNCTIONAL REQUIREMENT 2: AGGREGATE DATA")
        print("=" * 80)
        
        result = {
            'success': False,
            'message': '',
            'aggregated_data': None,
            'validation_passed': False
        }
        
        try:
            if self.df is None:
                result['message'] = "Error: Must load data first"
                return result
            
            print(f"Aggregating data by customer and period: {period}")
            print(f"Unique customers: {self.df[self.customer_col].nunique():,}")
            
            # Prepare data for aggregation
            df_work = self.df.copy()
            
            # Create date column if we have ANIO and MES
            if hasattr(self, 'year_col') and hasattr(self, 'month_col') and self.year_col in df_work.columns and self.month_col in df_work.columns:
                # Create date of first day of month
                df_work['date'] = pd.to_datetime(df_work[self.year_col].astype(str) + '-' + df_work[self.month_col].astype(str).str.zfill(2) + '-01')
            elif self.date_col in df_work.columns:
                df_work['date'] = pd.to_datetime(df_work[self.date_col])
            else:
                result['message'] = "Cannot create date column. Need year and month columns or date column."
                return result
            
            # Create period columns
            if period == 'month':
                df_work['period'] = df_work['date'].dt.to_period('M')
                period_label = 'Month'
            elif period == 'quarter':
                df_work['period'] = df_work['date'].dt.to_period('Q')
                period_label = 'Quarter'
            elif period == 'year':
                df_work['period'] = df_work['date'].dt.to_period('Y')
                period_label = 'Year'
            elif period == 'custom' and custom_period:
                # For custom periods (e.g., week, biweekly)
                df_work['period'] = df_work['date'].dt.to_period(custom_period)
                period_label = f'Period ({custom_period})'
            else:
                result['message'] = "Invalid period. Use: 'month', 'quarter', 'year', or 'custom'"
                return result
            
            # Aggregation by customer and period
            print("Performing aggregation...")
            aggregated = df_work.groupby([self.customer_col, 'period']).agg({
                self.quantity_col: ['sum', 'mean', 'count'],
                'date': ['min', 'max']
            }).round(4)
            
            # Flatten column names
            aggregated.columns = ['total_kg', 'avg_kg', 'purchase_count', 'first_purchase', 'last_purchase']
            aggregated = aggregated.reset_index()
            
            # Convert to tons
            aggregated['total_tons'] = aggregated['total_kg'] / 1000
            aggregated['avg_tons'] = aggregated['avg_kg'] / 1000
            
            print(f"Aggregation completed")
            print(f"Aggregated records: {len(aggregated):,}")
            print(f"Unique periods: {aggregated['period'].nunique()}")
            
            # Validate that totals match
            validation_result = self._validate_aggregation_totals(df_work, aggregated)
            result['validation_passed'] = validation_result['valid']
            
            if validation_result['valid']:
                print("Totals validation: SUCCESSFUL")
                print(f"Original total: {validation_result['original_total']:,.2f} kg")
                print(f"Aggregated total: {validation_result['aggregated_total']:,.2f} kg")
                print(f"Difference: {validation_result['difference']:,.2f} kg")
            else:
                print("Totals validation: FAILED")
                print(f"Error: {validation_result['error']}")
            
            # Show summary
            print(f"\nAGGREGATION SUMMARY:")
            print(f"   Period: {period_label}")
            print(f"   Customers: {aggregated[self.customer_col].nunique():,}")
            print(f"   Periods: {aggregated['period'].nunique()}")
            print(f"   Total kg: {aggregated['total_kg'].sum():,.2f}")
            print(f"   Total tons: {aggregated['total_tons'].sum():,.4f}")
            
            result['success'] = True
            result['message'] = f"Aggregation successful: {len(aggregated):,} records"
            result['aggregated_data'] = aggregated
            
            print("AGGREGATION COMPLETED SUCCESSFULLY")
            print("=" * 80)
            
        except Exception as e:
            result['message'] = f"Error in aggregation: {str(e)}"
            print(f"Error: {result['message']}")
        
        return result
    
    def _validate_aggregation_totals(self, original_df: pd.DataFrame, aggregated_df: pd.DataFrame) -> Dict[str, any]:
        """Validates that aggregated totals match original data"""
        validation = {
            'valid': False,
            'original_total': 0,
            'aggregated_total': 0,
            'difference': 0,
            'error': ''
        }
        
        try:
            # Original total
            original_total = original_df[self.quantity_col].sum()
            
            # Aggregated total
            aggregated_total = aggregated_df['total_kg'].sum()
            
            # Difference
            difference = abs(original_total - aggregated_total)
            
            # Tolerance of 0.01% for rounding errors
            tolerance = original_total * 0.0001
            
            validation['original_total'] = original_total
            validation['aggregated_total'] = aggregated_total
            validation['difference'] = difference
            
            if difference <= tolerance:
                validation['valid'] = True
            else:
                validation['error'] = f"Difference exceeds tolerance: {difference:.2f} > {tolerance:.2f}"
            
        except Exception as e:
            validation['error'] = f"Error in validation: {str(e)}"
        
        return validation


def main():
    """Main function - implements only the first 2 functional requirements"""
    print("CUSTOMER CHURN RISK ANALYSIS SYSTEM")
    print("FUNCTIONAL REQUIREMENTS 1 & 2 ONLY")
    print("=" * 80)
    
    analyzer = FunctionalRequirementsAnalyzer()
    
    while True:
        print("\n" + "=" * 80)
        print("FUNCTIONAL REQUIREMENTS MENU")
        print("=" * 80)
        print("1. Upload historical data (CSV/XLSX) - Functional Requirement 1")
        print("2. Aggregate data by customer and period - Functional Requirement 2")
        print("3. Exit")
        print("=" * 80)
        
        option = input("\nSelect an option (1-3): ").strip()
        
        if option == "1":
            # Functional Requirement 1: Upload historical data
            print("\n" + "=" * 60)
            print("FUNCTIONAL REQUIREMENT 1: UPLOAD HISTORICAL DATA")
            print("=" * 60)
            
            file_path = input("Enter file path (CSV or XLSX): ").strip()
            if not file_path:
                file_path = 'ventas_anonimizadas.csv'  # Default file
            
            result = analyzer.upload_historical_data(file_path)
            
            if result['success']:
                print(f"\n{result['message']}")
                if result['validation_errors']:
                    print("Validation errors:")
                    for error in result['validation_errors']:
                        print(f"   - {error}")
            else:
                print(f"\n{result['message']}")
            
        elif option == "2":
            # Functional Requirement 2: Aggregate data
            print("\n" + "=" * 60)
            print("FUNCTIONAL REQUIREMENT 2: AGGREGATE DATA")
            print("=" * 60)
            
            if analyzer.df is None:
                print("Must load data first (option 1)")
                continue
            
            print("Available periods:")
            print("  - month: Monthly aggregation")
            print("  - quarter: Quarterly aggregation")
            print("  - year: Annual aggregation")
            print("  - custom: Custom period")
            
            period = input("Select period (month/quarter/year/custom): ").strip().lower()
            if not period:
                period = 'month'
            
            custom_period = None
            if period == 'custom':
                custom_period = input("Enter custom period (e.g., W, 2W, M): ").strip()
            
            result = analyzer.aggregate_purchases_by_customer_and_period(period, custom_period)
            
            if result['success']:
                print(f"\n{result['message']}")
                if result['validation_passed']:
                    print("Totals validation: SUCCESSFUL")
                else:
                    print("Totals validation: FAILED")
            else:
                print(f"\n{result['message']}")
            
        elif option == "3":
            print("\nThank you for using the system!")
            break
            
        else:
            print("Invalid option. Please select a valid option.")


if __name__ == "__main__":
    main()