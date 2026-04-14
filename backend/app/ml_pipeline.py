"""
Core ML pipeline for FairLens AI.
Handles model training, fairness metric computation, SHAP, and mitigation.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score
from typing import Tuple, Dict, Any, Optional
import warnings
warnings.filterwarnings("ignore")


# ─── Data Preparation ────────────────────────────────────────────────────────

def prepare_dataset(
    df: pd.DataFrame,
    target_col: str,
    sensitive_col: str,
    drop_sensitive: bool = False
) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Prepare dataset for ML training.
    Returns: X (features), y (target), sensitive (sensitive attribute series)
    """
    df = df.copy()

    # Encode target if categorical
    if df[target_col].dtype == object:
        le = LabelEncoder()
        df[target_col] = le.fit_transform(df[target_col])

    # Encode sensitive attribute
    sensitive = df[sensitive_col].copy()
    if sensitive.dtype == object:
        le = LabelEncoder()
        sensitive = pd.Series(le.fit_transform(sensitive), name=sensitive_col)

    # Encode all remaining categorical columns
    for col in df.select_dtypes(include="object").columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))

    y = df[target_col]

    if drop_sensitive:
        X = df.drop(columns=[target_col, sensitive_col], errors="ignore")
    else:
        X = df.drop(columns=[target_col], errors="ignore")

    # Fill NaN
    X = X.fillna(X.median(numeric_only=True))
    X = X.fillna(0)

    return X, y, sensitive


def train_logistic_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> Tuple[LogisticRegression, StandardScaler]:
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_scaled, y_train)
    return model, scaler


# ─── Fairness Metrics ─────────────────────────────────────────────────────────

def compute_demographic_parity_difference(
    y_pred: np.ndarray,
    sensitive: np.ndarray
) -> float:
    """
    Demographic Parity Difference = |P(Y_hat=1|A=0) - P(Y_hat=1|A=1)|
    """
    groups = np.unique(sensitive)
    if len(groups) < 2:
        return 0.0
    rates = []
    for g in groups:
        mask = sensitive == g
        rate = np.mean(y_pred[mask]) if mask.sum() > 0 else 0.0
        rates.append(rate)
    return float(max(rates) - min(rates))


def compute_equalized_odds_difference(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    sensitive: np.ndarray
) -> float:
    """
    Equalized Odds Difference = max over {0,1} of |TPR_group0 - TPR_group1|
    """
    groups = np.unique(sensitive)
    if len(groups) < 2:
        return 0.0

    max_diff = 0.0
    for label in [0, 1]:
        rates = []
        for g in groups:
            mask = (sensitive == g) & (y_true == label)
            if mask.sum() == 0:
                continue
            rate = np.mean(y_pred[mask] == label)
            rates.append(rate)
        if len(rates) >= 2:
            diff = max(rates) - min(rates)
            max_diff = max(max_diff, diff)

    return float(max_diff)


def compute_group_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    sensitive: np.ndarray,
    sensitive_col: str
) -> Dict[str, Any]:
    """Compute per-group prediction rates for visualization."""
    groups = np.unique(sensitive)
    group_stats = []
    for g in groups:
        mask = sensitive == g
        count = int(mask.sum())
        pos_rate = float(np.mean(y_pred[mask])) if count > 0 else 0.0
        accuracy = float(accuracy_score(y_true[mask], y_pred[mask])) if count > 0 else 0.0
        group_stats.append({
            "group": str(g),
            "count": count,
            "positive_rate": round(pos_rate, 4),
            "accuracy": round(accuracy, 4),
        })
    return {"groups": group_stats, "sensitive_col": sensitive_col}


def run_full_analysis(
    df: pd.DataFrame,
    target_col: str,
    sensitive_col: str,
    drop_sensitive: bool = False
) -> Dict[str, Any]:
    """
    Full pipeline: prepare → split → train → predict → metrics.
    Returns all artifacts needed by the API.
    """
    X, y, sensitive = prepare_dataset(df, target_col, sensitive_col, drop_sensitive)

    X_train, X_test, y_train, y_test, s_train, s_test = train_test_split(
        X, y, sensitive, test_size=0.3, random_state=42, stratify=y if y.nunique() <= 10 else None
    )

    model, scaler = train_logistic_model(X_train, y_train)
    X_test_scaled = scaler.transform(X_test)
    y_pred = model.predict(X_test_scaled)

    acc = float(accuracy_score(y_test, y_pred))
    dpd = compute_demographic_parity_difference(y_pred, s_test.values)
    eod = compute_equalized_odds_difference(y_test.values, y_pred, s_test.values)
    group_stats = compute_group_metrics(y_test.values, y_pred, s_test.values, sensitive_col)

    return {
        "model": model,
        "scaler": scaler,
        "X_train": X_train,
        "X_test": X_test,
        "X_test_scaled": X_test_scaled,
        "y_train": y_train,
        "y_test": y_test,
        "s_test": s_test,
        "y_pred": y_pred,
        "feature_names": list(X.columns),
        "metrics": {
            "accuracy": round(acc, 4),
            "demographic_parity_difference": round(dpd, 4),
            "equalized_odds_difference": round(eod, 4),
            "group_stats": group_stats,
        },
    }


# ─── SHAP Explainability ──────────────────────────────────────────────────────

def compute_shap_values(
    model: LogisticRegression,
    X_train_scaled: np.ndarray,
    X_test_scaled: np.ndarray,
    feature_names: list,
    max_samples: int = 100
) -> Dict[str, Any]:
    """
    Compute SHAP feature importances using LinearExplainer (fast for logistic regression).
    Falls back to mean absolute coefficients if SHAP fails.
    """
    try:
        import shap
        # Use LinearExplainer for logistic regression - much faster than KernelExplainer
        explainer = shap.LinearExplainer(model, X_train_scaled, feature_perturbation="correlation_dependent")
        sample = X_test_scaled[:min(max_samples, len(X_test_scaled))]
        shap_vals = explainer.shap_values(sample)

        if isinstance(shap_vals, list):
            # Binary classification returns list of 2 arrays
            shap_vals = shap_vals[1]

        mean_abs = np.abs(shap_vals).mean(axis=0)
        importance = [
            {"feature": feat, "importance": round(float(imp), 6)}
            for feat, imp in zip(feature_names, mean_abs)
        ]
        importance.sort(key=lambda x: x["importance"], reverse=True)
        return {"method": "SHAP LinearExplainer", "feature_importance": importance}

    except Exception as e:
        # Fallback: use |coefficients| as proxy
        coefs = np.abs(model.coef_[0])
        importance = [
            {"feature": feat, "importance": round(float(imp), 6)}
            for feat, imp in zip(feature_names, coefs)
        ]
        importance.sort(key=lambda x: x["importance"], reverse=True)
        return {"method": "Logistic Regression |Coefficients| (SHAP fallback)", "feature_importance": importance}


# ─── Bias Mitigation ─────────────────────────────────────────────────────────

def apply_reweighting_mitigation(
    df: pd.DataFrame,
    target_col: str,
    sensitive_col: str
) -> Dict[str, Any]:
    """
    Mitigation strategy: reweight samples to equalize group representation,
    then retrain model without the sensitive feature.
    """
    X, y, sensitive = prepare_dataset(df, target_col, sensitive_col, drop_sensitive=True)

    # Compute sample weights to balance groups
    groups = sensitive.values
    unique_groups = np.unique(groups)
    n = len(groups)
    sample_weights = np.ones(n)

    for g in unique_groups:
        mask = groups == g
        group_size = mask.sum()
        target_size = n / len(unique_groups)
        sample_weights[mask] = target_size / group_size

    X_train, X_test, y_train, y_test, s_train, s_test, w_train, _ = train_test_split(
        X, y, sensitive, sample_weights, test_size=0.3, random_state=42,
        stratify=y if y.nunique() <= 10 else None
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train_scaled, y_train, sample_weight=w_train)

    y_pred = model.predict(X_test_scaled)
    acc = float(accuracy_score(y_test, y_pred))
    dpd = compute_demographic_parity_difference(y_pred, s_test.values)
    eod = compute_equalized_odds_difference(y_test.values, y_pred, s_test.values)
    group_stats = compute_group_metrics(y_test.values, y_pred, s_test.values, sensitive_col)

    return {
        "metrics": {
            "accuracy": round(acc, 4),
            "demographic_parity_difference": round(dpd, 4),
            "equalized_odds_difference": round(eod, 4),
            "group_stats": group_stats,
        },
        "strategy": "Reweighting + Drop Sensitive Feature",
    }
