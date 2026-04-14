from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ..state import get_store, update_store
from ..ml_pipeline import apply_reweighting_mitigation

router = APIRouter()


@router.post("/fix")
def fix_bias():
    """
    Apply bias mitigation (reweighting + drop sensitive feature) and return updated metrics.
    """
    store = get_store()
    df = store.get("dataframe")
    target_col = store.get("target_col")
    sensitive_col = store.get("sensitive_col")
    original_metrics = store.get("original_metrics")

    if df is None:
        raise HTTPException(status_code=400, detail="SESSION_EXPIRED: No dataset found. Please upload and analyze first.")

    if target_col is None or sensitive_col is None:
        raise HTTPException(status_code=400, detail="SESSION_EXPIRED: No analysis found. Please run /analyze first.")

    try:
        result = apply_reweighting_mitigation(df, target_col, sensitive_col)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mitigation failed: {str(e)}")

    fixed_metrics = result["metrics"]
    update_store(fixed_metrics=fixed_metrics)

    # Compute improvements
    def improvement(before, after):
        if before == 0:
            return 0.0
        return round((before - after) / before * 100, 2)

    comparison = {
        "demographic_parity_difference": {
            "before": original_metrics["demographic_parity_difference"],
            "after": fixed_metrics["demographic_parity_difference"],
            "improvement_pct": improvement(
                original_metrics["demographic_parity_difference"],
                fixed_metrics["demographic_parity_difference"]
            ),
        },
        "equalized_odds_difference": {
            "before": original_metrics["equalized_odds_difference"],
            "after": fixed_metrics["equalized_odds_difference"],
            "improvement_pct": improvement(
                original_metrics["equalized_odds_difference"],
                fixed_metrics["equalized_odds_difference"]
            ),
        },
        "accuracy": {
            "before": original_metrics["accuracy"],
            "after": fixed_metrics["accuracy"],
            "change_pct": round(
                (fixed_metrics["accuracy"] - original_metrics["accuracy"]) / original_metrics["accuracy"] * 100, 2
            ),
        },
    }

    return JSONResponse({
        "success": True,
        "strategy": result["strategy"],
        "original_metrics": original_metrics,
        "fixed_metrics": fixed_metrics,
        "comparison": comparison,
    })
