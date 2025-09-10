# Test Cases Detailed Table - Functional Requirements 1 and 2

## Complete Test Cases Specification

| Test ID | Test Name | Description | Acceptance Criteria | Steps to Reproduce | Expected Result |
|---------|-----------|-------------|-------------------|-------------------|-----------------|
| **1.1** | **test_upload_data_success_csv** | Verify successful CSV data upload with valid file | - File loads successfully<br>- All required columns detected<br>- Data validation passes<br>- Correct number of records loaded | 1. Execute `python risk_prediction.py`<br>2. Select option 1<br>3. Press Enter to use default file<br>4. Observe output |  Success message<br> "File loaded successfully"<br> "Required fields validation: SUCCESSFUL"<br>✅ "🎉 UPLOAD COMPLETED SUCCESSFULLY"<br> 5 records loaded |
| **1.2** | **test_upload_data_file_not_found** | Verify error handling when file doesn't exist | - Error handled gracefully<br>- Appropriate error message<br>- No system crash<br>- Returns failure status | 1. Execute `python risk_prediction.py`<br>2. Select option 1<br>3. Enter non-existent file path<br>4. Observe error handling | Error message: "does not exist"<br> Success = False<br>No crash occurs<br>Graceful error handling |
| **1.3** | **test_upload_data_invalid_format** | Verify rejection of unsupported file formats | - Invalid format rejected<br>- Clear error message<br>- Only CSV/XLSX accepted<br>- No data corruption | 1. Create .txt file with test data<br>2. Execute `python risk_prediction.py`<br>3. Select option 1<br>4. Enter .txt file path | Error message: "Only CSV or XLSX formats"<br> Success = False<br>Format validation fails<br>No data loaded |
| **1.4** | **test_upload_data_missing_required_fields** | Verify validation of mandatory fields | - Missing fields detected<br>- Validation errors generated<br>- Clear error messages<br>- No partial data loading | 1. Create CSV without required fields<br>2. Execute `python risk_prediction.py`<br>3. Select option 1<br>4. Enter invalid CSV path | Error message: "Required fields not found"<br>Validation errors list<br>Success = False<br>Fields identified as missing |
| **1.5** | **test_column_detection** | Verify automatic column detection | - Customer column detected<br>- Date columns detected<br>- Quantity column detected<br>- Correct column mapping | 1. Execute `python risk_prediction.py`<br>2. Select option 1<br>3. Use default file<br>4. Check column detection output | Customer column: CLIENTE_ANONIMO<br>Date columns: ANIO, MES<br> Quantity column: VENTAS_KG<br>All columns detected correctly |
| **2.1** | **test_aggregation_monthly_success** | Verify successful monthly data aggregation | - Aggregation completes successfully<br>- Correct data structure<br>- Totals validation passes<br>- Metrics calculated correctly | 1. Load data first (option 1)<br>2. Select option 2<br>3. Enter "month" as period<br>4. Observe aggregation results | "Aggregation completed"<br> "Totals validation: SUCCESSFUL"<br>Correct data structure<br>All metrics calculated<br>"AGGREGATION COMPLETED SUCCESSFULLY" |
| **2.2** | **test_aggregation_quarterly_success** | Verify successful quarterly data aggregation | - Quarterly aggregation works<br>- Record count reduced appropriately<br>- Total kg preserved<br>- Correct period grouping | 1. Load data first (option 1)<br>2. Select option 2<br>3. Enter "quarter" as period<br>4. Observe quarterly results | "Aggregation completed"<br> "Totals validation: SUCCESSFUL"<br>Reduced record count<br>Total kg preserved<br>Quarterly grouping correct |
| **2.3** | **test_aggregation_yearly_success** | Verify successful annual data aggregation | - Annual aggregation works<br>- Year consolidation correct<br>- Total kg preserved<br>- Proper year grouping | 1. Load data first (option 1)<br>2. Select option 2<br>3. Enter "year" as period<br>4. Observe annual results | "Aggregation completed"<br>"Totals validation: SUCCESSFUL"<br> Year consolidation correct<br>Total kg preserved<br>Annual grouping proper |
| **2.4** | **test_aggregation_without_data** | Verify error handling when no data loaded | - Error handled gracefully<br>- Clear error message<br>- No system crash<br>- Prevents invalid operations | 1. Execute `python risk_prediction.py`<br>2. Select option 2 directly<br>3. Observe error handling | Error message: "Must load data first"<br>Success = False<br>No crash occurs<br>Graceful error handling |
| **2.5** | **test_aggregation_invalid_period** | Verify rejection of invalid aggregation periods | - Invalid period rejected<br>- Clear error message<br>- Only valid periods accepted<br>- No partial processing | 1. Load data first (option 1)<br>2. Select option 2<br>3. Enter "invalid_period"<br>4. Observe error handling | Error message: "Invalid period"<br>Success = False<br>Period validation fails<br>No aggregation performed |
| **2.6** | **test_aggregation_metrics_calculation** | Verify accuracy of aggregated metrics calculations | - Conversion to tons correct<br>- Averages calculated properly<br>- Purchase counts accurate<br>- All metrics precise | 1. Load data first (option 1)<br>2. Select option 2<br>3. Enter "month" as period<br>4. Verify metric calculations | Tons conversion: kg/1000<br>Averages calculated correctly<br>Purchase counts accurate<br> All metrics precise<br>Mathematical accuracy verified |
| **2.7** | **test_aggregation_validation_totals** | Verify totals validation in aggregation | - Original total = Aggregated total<br>- Difference within tolerance<br>- Validation passes<br>- Data integrity maintained | 1. Load data first (option 1)<br>2. Select option 2<br>3. Enter "month" as period<br>4. Check totals validation | "Totals validation: SUCCESSFUL"<br> Original total = Aggregated total<br>Difference ≤ 0.01% tolerance<br>Data integrity maintained<br>Validation passes |

## Test Execution Summary

### Functional Requirement 1 (Data Upload) - 5 Tests
- **1.1** Success case with valid CSV
- **1.2** Error handling for missing file
- **1.3** Error handling for invalid format
- **1.4** Error handling for missing fields
- **1.5** Automatic column detection

### Functional Requirement 2 (Data Aggregation) - 7 Tests
- **2.1** Monthly aggregation success
- **2.2** Quarterly aggregation success
- **2.3** Annual aggregation success
- **2.4** Error handling without data
- **2.5** Error handling for invalid period
- **2.6** Metrics calculation accuracy
- **2.7** Totals validation

## Test Data Used

All tests use synthetic data with the following structure:
```csv
CLIENTE_ANONIMO,ANIO,MES,VENTAS_KG
CLT_001,2023,1,1000
CLT_002,2023,1,1500
CLT_001,2023,2,1200
CLT_003,2023,2,800
CLT_002,2024,1,2000
```

## Expected Test Results

### Success Criteria
- **Total Tests**: 12
- **Expected Success Rate**: 100%
- **Expected Failures**: 0
- **Expected Errors**: 0

### Validation Points
- File upload functionality
- Data validation
- Error handling
- Aggregation functionality
- Metrics calculation
- Data integrity
- Edge case handling

## How to Execute Tests

### Option 1: Direct Test Execution
```bash
python test_functional_requirements.py
```

### Option 2: Through Main Menu
```bash
python risk_prediction.py
# Select option 3
```

### Option 3: Unit Testing
```bash
python -m unittest test_functional_requirements.TestFunctionalRequirements
```

### Option 4: Dedicated Script
```bash
python run_tests.py
```

## Test Coverage

### Positive Test Cases (Success Scenarios)
- Valid file upload
- Successful aggregations
- Correct metric calculations
- Proper data validation

### Negative Test Cases (Error Scenarios)
- Missing files
- Invalid formats
- Missing required fields
- Invalid periods
- Operations without data

### Edge Cases
- Empty files
- Invalid data types
- Boundary conditions
- Error recovery

This comprehensive test suite ensures complete coverage of both functional requirements with robust validation of success and error scenarios.