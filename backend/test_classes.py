import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from data.data_loader import DataLoader
    print("✅ DataLoader imported successfully")
    
    loader = DataLoader()
    print("✅ DataLoader instantiated successfully")
    
    # Verificar que el método existe
    if hasattr(loader, 'load_csv'):
        print("✅ load_csv method exists")
    else:
        print("❌ load_csv method missing")
    
    from data.data_aggregator import DataAggregator
    print("✅ DataAggregator imported successfully")
    
    from models.ml_model import MLModel
    print("✅ MLModel imported successfully")
    
    from processing.analysis_reporter import AnalysisReporter
    print("✅ AnalysisReporter imported successfully")
    
    from processing.flag_reporter import FlagReporter
    print("✅ FlagReporter imported successfully")
    
    from processing.analyzer import FunctionalRequirementsAnalyzer
    print("✅ FunctionalRequirementsAnalyzer imported successfully")
    
    analyzer = FunctionalRequirementsAnalyzer()
    print("✅ FunctionalRequirementsAnalyzer instantiated successfully")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()