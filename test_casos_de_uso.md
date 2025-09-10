# Test Cases Documentation - Functional Requirements 1 and 2

## Summary
This document describes the test cases implemented to validate functional requirements 1 and 2 of the customer churn risk analysis system.

## File Structure

### Main Files
- **`risk_prediction.py`**: Contains the main logic for functional requirements 1 and 2
- **`test_functional_requirements.py`**: Contains all test cases organized in a unittest class
- **`run_tests.py`**: Auxiliary script to easily run the tests
- **`TEST_CASES_DOCUMENTATION.md`**: This complete documentation

### Separation of Responsibilities
- **Production code**: Separated in `risk_prediction.py`
- **Test code**: Separated in `test_functional_requirements.py`
- **Auxiliary scripts**: In `run_tests.py`
- **Documentation**: In `.md` files

## Functional Requirements Covered

### Functional Requirement 1: Historical Data Upload
**Objective**: Allow uploading historical data in CSV or XLSX format with automatic validation of required fields.

### Functional Requirement 2: Data Aggregation
**Objective**: Aggregate purchase data by customer and period (monthly, quarterly, annual) with totals validation.

## Implemented Test Cases

### For Functional Requirement 1 (Data Upload)

#### Test Case 1.1: Successful CSV Data Upload
- **Purpose**: Verify that CSV data upload works correctly
- **Test Data**: CSV file with 5 records and valid fields
- **Validations**:
  - ✅ Successful upload
  - ✅ Correct column detection
  - ✅ Required fields validation
  - ✅ 5 records loaded correctly

#### Test Case 1.2: File Not Found
- **Purpose**: Verify error handling when file doesn't exist
- **Test Data**: Non-existent file path
- **Validations**:
  - ✅ Error handled correctly
  - ✅ Appropriate error message
  - ✅ No system crash

#### Test Case 1.3: Invalid File Format
- **Purpose**: Verify rejection of unsupported formats
- **Test Data**: File with .txt extension
- **Validations**:
  - ✅ Format rejected correctly
  - ✅ Clear error message
  - ✅ Only accepts CSV and XLSX

#### Test Case 1.4: Missing Required Fields
- **Purpose**: Verify validation of mandatory fields
- **Test Data**: CSV without customer, date or quantity fields
- **Validations**:
  - ✅ Validation error detected
  - ✅ Error list generated
  - ✅ Missing fields identified

#### Test Case 1.5: Automatic Column Detection
- **Purpose**: Verify automatic detection of relevant columns
- **Test Data**: CSV with standard columns
- **Validations**:
  - ✅ Customer column detected (CLIENTE_ANONIMO)
  - ✅ Quantity column detected (VENTAS_KG)
  - ✅ Date columns detected (ANIO, MES)

### For Functional Requirement 2 (Data Aggregation)

#### Test Case 2.1: Successful Monthly Aggregation
- **Purpose**: Verify aggregation by monthly periods
- **Test Data**: 5 records with dates from different months
- **Validations**:
  - ✅ Successful aggregation
  - ✅ Correct data structure
  - ✅ Successful totals validation
  - ✅ Metrics calculated correctly

#### Test Case 2.2: Successful Quarterly Aggregation
- **Purpose**: Verify aggregation by quarters
- **Test Data**: Same test data
- **Validations**:
  - ✅ Quarterly aggregation functional
  - ✅ Record count reduced appropriately
  - ✅ Total kg preserved

#### Test Case 2.3: Successful Annual Aggregation
- **Purpose**: Verify aggregation by years
- **Test Data**: Same test data
- **Validations**:
  - ✅ Annual aggregation functional
  - ✅ Correct year consolidation
  - ✅ Total kg preserved

#### Test Case 2.4: Aggregation Without Loaded Data
- **Purpose**: Verify error handling when no data is available
- **Test Data**: No data loaded previously
- **Validations**:
  - ✅ Error handled correctly
  - ✅ Appropriate error message
  - ✅ No crash occurs

#### Test Case 2.5: Invalid Aggregation Period
- **Purpose**: Verify rejection of invalid periods
- **Test Data**: Period 'invalid_period'
- **Validations**:
  - ✅ Period rejected correctly
  - ✅ Clear error message
  - ✅ Only accepts valid periods

#### Test Case 2.6: Correct Metrics Calculation
- **Purpose**: Verify accuracy of aggregated calculations
- **Test Data**: Data with known values
- **Validations**:
  - ✅ Correct conversion to tons (kg/1000)
  - ✅ Averages calculated correctly
  - ✅ Accurate purchase counts

#### Test Case 2.7: Totals Validation
- **Purpose**: Verify that aggregated totals match originals
- **Test Data**: Standard test data
- **Validations**:
  - ✅ Original total = Aggregated total
  - ✅ Difference within tolerance (0.01%)
  - ✅ Successful validation

## Test Metrics

### Execution Summary
- **Total Tests**: 12
- **Successful Tests**: 12 (100%)
- **Failed Tests**: 0
- **Errors**: 0

### Functionality Coverage
- ✅ CSV file upload
- ✅ Format validation
- ✅ Automatic column detection
- ✅ Error handling
- ✅ Monthly aggregation
- ✅ Quarterly aggregation
- ✅ Annual aggregation
- ✅ Totals validation
- ✅ Metrics calculation
- ✅ Edge case handling

## How to Run the Tests

### Option 1: Direct Test File
```bash
python test_functional_requirements.py
```

### Option 2: Dedicated Script
```bash
python run_tests.py
```

### Option 3: Main Menu
```bash
python risk_prediction.py
# Select option 3: "Run test cases for Functional Requirements 1 & 2"
```

### Option 4: Unit Testing
```bash
python -m unittest test_functional_requirements.TestFunctionalRequirements
```

## Test Data Used

The test cases use synthetic data that simulates the real structure:

```csv
CLIENTE_ANONIMO,ANIO,MES,VENTAS_KG
CLT_001,2023,1,1000
CLT_002,2023,1,1500
CLT_001,2023,2,1200
CLT_003,2023,2,800
CLT_002,2024,1,2000
```

## Implemented Validations

### Upload Validations (FR1)
1. **File existence**
2. **Valid format** (CSV/XLSX only)
3. **Required fields present**:
   - Customer field (cliente, clt, customer, client)
   - Date field (fecha, date, anio, mes, year, month)
   - Quantity field (ventas_kg, cantidad, kg, quantity, sales)

### Aggregation Validations (FR2)
1. **Data loaded previously**
2. **Valid period** (month, quarter, year, custom)
3. **Totals preservation** (0.01% tolerance)
4. **Correct data structure**
5. **Precise metrics calculations**

## Conclusions

The implemented test cases provide complete coverage of functional requirements 1 and 2, including:

- ✅ **Success cases**: Verify normal functionality
- ✅ **Error cases**: Verify robust error handling
- ✅ **Edge cases**: Verify limits and special conditions
- ✅ **Validations**: Verify data integrity and calculations

The system is ready for delivery with a solid foundation of tests that guarantee the quality and reliability of the implemented functionalities.