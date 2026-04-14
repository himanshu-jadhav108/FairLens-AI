from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ..state import get_store, update_store
from ..ml_pipeline import compute_shap_values

router = APIRouter()


@router.post("/explain")
def explain_model():
    """
    Compute SHAP feature importance values for the trained model.
    """
    store = get_store()
    model = store.get("model")
    scaler = store.get("scaler")
    X_train = store.get("X_train")
    X_test_scaled = store.get("X_test_scaled")
    feature_names = store.get("feature_names")

    if model is None:
        raise HTTPException(status_code=400, detail="SESSION_EXPIRED: No model found. Please run /analyze first.")

    try:
        import numpy as np
        X_train_scaled = scaler.transform(X_train)
        shap_result = compute_shap_values(
            model,
            X_train_scaled,
            X_test_scaled,
            feature_names,
            max_samples=150
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SHAP computation failed: {str(e)}")

    update_store(shap_values=shap_result)

    return JSONResponse({
        "success": True,
        "method": shap_result["method"],
        "feature_importance": shap_result["feature_importance"],
    })


@router.post("/ai-explain")
def ai_explain():
    """
    Generate a human-readable explanation of the bias findings.
    Uses a structured template (Gemini API placeholder).
    """
    store = get_store()
    metrics = store.get("original_metrics")
    sensitive_col = store.get("sensitive_col")
    target_col = store.get("target_col")
    shap_values = store.get("shap_values")

    if metrics is None:
        raise HTTPException(status_code=400, detail="SESSION_EXPIRED: No metrics found. Please run /analyze first.")

    dpd = metrics.get("demographic_parity_difference", 0)
    eod = metrics.get("equalized_odds_difference", 0)
    acc = metrics.get("accuracy", 0)

    # Determine severity
    def severity(val):
        if val < 0.05:
            return "low"
        elif val < 0.15:
            return "moderate"
        else:
            return "high"

    dpd_sev = severity(dpd)
    eod_sev = severity(eod)

    top_features = []
    if shap_values:
        top_features = [f["feature"] for f in shap_values["feature_importance"][:3]]

    # Build structured explanation
    explanation = f"""## 🔍 FairLens AI Bias Analysis Report

### Model Overview
The model is a **Logistic Regression classifier** trained to predict **{target_col}**, with **{sensitive_col}** identified as the sensitive attribute being audited. Overall model accuracy: **{acc * 100:.1f}%**.

### Detected Bias Signals

**Demographic Parity Difference: {dpd:.4f}** — {dpd_sev.upper()} bias
> This measures whether the model predicts positive outcomes at equal rates across groups defined by `{sensitive_col}`. A value of {dpd:.4f} means there is a **{dpd * 100:.1f} percentage point gap** in positive prediction rates between the most and least favored groups.

**Equalized Odds Difference: {eod:.4f}** — {eod_sev.upper()} bias
> This measures whether the model's true positive and false positive rates are consistent across groups. A difference of {eod:.4f} indicates that the model is {'nearly fair' if eod < 0.05 else 'moderately unfair' if eod < 0.15 else 'significantly unfair'} in how it handles different groups' true outcomes.

### Key Contributing Features
{f"The top features driving predictions are: **{', '.join(top_features)}**. These features may carry historical bias from the training data, which propagates into the model's decisions." if top_features else "Run the SHAP explainer to identify the top contributing features."}

### Interpretation
{"✅ The model appears relatively fair across groups — bias metrics are within acceptable thresholds." if dpd < 0.05 and eod < 0.05 else f"⚠️ The model exhibits **{max(dpd_sev, eod_sev, key=lambda x: ['low','moderate','high'].index(x))} bias**. The sensitive attribute `{sensitive_col}` appears to influence model outcomes unequally. This could reflect systemic patterns in the training data."}

### Recommended Actions
1. **Apply reweighting mitigation** — balance training samples across sensitive groups
2. **Drop the sensitive feature** — prevent direct use of `{sensitive_col}` in predictions
3. **Audit training data** — inspect whether historical data reflects real-world inequities
4. **Post-processing calibration** — adjust decision thresholds per group

---
*⚡ Powered by FairLens AI — Gemini-enhanced explanation (placeholder)*
"""

    return JSONResponse({
        "success": True,
        "explanation": explanation,
        "summary": {
            "demographic_parity_severity": dpd_sev,
            "equalized_odds_severity": eod_sev,
            "overall_verdict": "fair" if dpd < 0.05 and eod < 0.05 else "biased",
        }
    })
