"""
Random Forest model configuration
"""
from sklearn.ensemble import RandomForestClassifier

# Model hyperparameters
RANDOM_FOREST_CONFIG = {
    'n_estimators': 100,
    'random_state': 42,
    'class_weight': 'balanced',
    'max_depth': None,
    'min_samples_split': 2,
    'min_samples_leaf': 1,
    'max_features': 'sqrt',
    'bootstrap': True,
    'n_jobs': -1
}

# Training configuration
TRAINING_CONFIG = {
    'test_size': 0.2,
    'random_state': 42,
    'stratify': True
}

# Feature configuration
FEATURE_CONFIG = {
    'rolling_window': 3,  # For calculating rolling averages
    'inactivity_threshold_percentile': 0.75,  # For dynamic churn threshold
    'min_inactivity_periods': 1,  # Minimum periods to consider as churn
    'churn_probability_threshold': 0.5  # Threshold for high-risk customers
}

# Model evaluation configuration
EVALUATION_CONFIG = {
    'cv_folds': 5,  # Cross-validation folds
    'scoring_metrics': ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
}

# Model persistence configuration
PERSISTENCE_CONFIG = {
    'model_format': 'joblib',  # or 'pickle'
    'save_metadata': True,
    'version_format': 'v{major}.{minor}.{patch}'
}

