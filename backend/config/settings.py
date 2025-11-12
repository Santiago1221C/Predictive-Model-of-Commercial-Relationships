"""
General system settings and configurations
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent

# Data paths
DATA_DIR = BASE_DIR / "data"
TRAINED_MODELS_DIR = BASE_DIR / "trained_models"
LOGS_DIR = BASE_DIR / "logs"

# Default data file
DEFAULT_DATA_FILE = "ventas_anonimizadas.csv"
DEFAULT_DATA_PATH = BASE_DIR / DEFAULT_DATA_FILE

# API settings
API_HOST = "127.0.0.1"
API_PORT = 5000
API_DEBUG = True

# CORS settings
CORS_ENABLED = True

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Data validation settings
SUPPORTED_FILE_FORMATS = ['csv', 'xlsx']
MAX_FILE_SIZE_MB = 500

# Column detection patterns
CUSTOMER_COLUMN_PATTERNS = ['cliente', 'clt', 'customer', 'client']
DATE_COLUMN_PATTERNS = ['fecha', 'date', 'anio', 'mes', 'year', 'month']
QUANTITY_COLUMN_PATTERNS = ['ventas_kg', 'cantidad', 'kg', 'quantity', 'sales']

# Unit conversion
KG_TO_TONS_FACTOR = 1000