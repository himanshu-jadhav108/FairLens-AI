"""
In-memory session store for uploaded datasets and model state.
In production, replace with Redis or a database.
"""
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

# Global state (per process - good enough for hackathon MVP)
_store: Dict[str, Any] = {
    "dataframe": None,
    "target_col": None,
    "sensitive_col": None,
    "model": None,
    "X_test": None,
    "y_test": None,
    "sensitive_test": None,
    "y_pred": None,
    "feature_names": None,
    "original_metrics": None,
    "fixed_metrics": None,
    "shap_values": None,
    "filename": None,
}


def get_store() -> Dict[str, Any]:
    return _store


def update_store(**kwargs):
    for k, v in kwargs.items():
        _store[k] = v


def reset_store():
    for k in _store:
        _store[k] = None
