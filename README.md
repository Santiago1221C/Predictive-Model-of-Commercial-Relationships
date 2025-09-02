# Customer Churn Risk Analysis System

## Project Description

System to analyze customer sales data and detect risk patterns. Currently implements basic data loading and column detection for the `ventas_anonimizadas.csv` dataset.

## Current Implementation (FIRST COMMIT)

### 1. Data Loading and Analysis
- **Complete dataset loading** - Loads ALL data from CSV file
- **Comprehensive analysis** - Shows total rows, columns, file size
- **Column information** - Displays all column names and data types
- **Sample data** - Shows first 10 and last 10 rows
- **Dataset statistics** - Complete descriptive statistics
- **Missing values check** - Identifies any data quality issues
- **Unique values count** - Shows data distribution per column

### 2. Automatic Column Detection
- **Customer ID detection** - Automatically finds CLT_001, CLT_002, etc. columns
- **Date column detection** - Identifies fecha/date columns
- **Quantity column detection** - Finds cantidad columns
- **Smart column mapping** - Stores detected columns for future use

### 3. Unit Conversion
- **KG to Tons conversion** - Converts quantity columns from kg to tons
- **Automatic column search** - Finds kg columns automatically
- **Range display** - Shows min/max values in both units

## Technologies Used

- **Python 3.8+**
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical calculations
- **Matplotlib** - Data visualization (imported but not yet used)
- **Scikit-learn** - Machine Learning (imported but not yet used)

## Installation and Usage

### Dependencies
```bash
pip install pandas numpy matplotlib scikit-learn
```

### Execution
```bash
python prediccion_abandono.py
```

### Current Status
The system currently loads and analyzes data but does not have a main menu or user interface implemented yet.

## What the System Currently Does

### FUNCTIONAL:
- Loads entire CSV dataset completely
- Shows comprehensive dataset information
- Automatically detects customer ID columns (CLT_ pattern)
- Detects date and quantity columns
- Converts kg to tons when requested
- Provides detailed data analysis

### NOT YET IMPLEMENTED:
- Main menu system
- Customer monthly analysis
- Random Forest model training
- Customer list display
- User interaction interface

## Project Status

- **Status**: First commit - Data loading and analysis foundation
- **Progress**: 20% (basic data operations completed)
- **Current Focus**: Data exploration and column detection
- **Next Priority**: Implement main menu and user interface

## Team Development Path

### Immediate Next Steps:
1. **Main Menu** - Implement user interface with options
2. **Customer Analysis** - Add monthly purchase analysis per customer
3. **Random Forest** - Complete ML model implementation
4. **Customer List** - Show all available customers

### Future Enhancements:
- Web dashboard with Streamlit
- Advanced risk metrics
- Performance optimization
- Testing and validation

---

## Ready for Team Development

First commit provides a solid foundation with:
- Complete data loading and analysis
- Automatic column detection
- Unit conversion capability
- Framework ready for user interface
- ML model structure prepared

The team needs to implement the main menu system and user interaction to make the current functionality accessible.