from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ..state import get_store, update_store
from ..ml_pipeline import run_full_analysis

router = APIRouter()


class AnalyzeRequest(BaseModel):
    target_col: str
    sensitive_col: str


@router.post("/analyze")
def analyze_bias(req: AnalyzeRequest):
    """
    Train a logistic regression model and compute fairness metrics.
    """
    store = get_store()
    df = store.get("dataframe")

    if df is None:
        raise HTTPException(status_code=400, detail="SESSION_EXPIRED: No dataset uploaded. Please upload a CSV first.")

    if req.target_col not in df.columns:
        raise HTTPException(status_code=400, detail=f"Target column '{req.target_col}' not found.")

    if req.sensitive_col not in df.columns:
        raise HTTPException(status_code=400, detail=f"Sensitive column '{req.sensitive_col}' not found.")

    if req.target_col == req.sensitive_col:
        raise HTTPException(status_code=400, detail="Target and sensitive columns must be different.")

    try:
        result = run_full_analysis(df, req.target_col, req.sensitive_col)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Persist state for subsequent calls
    update_store(
        target_col=req.target_col,
        sensitive_col=req.sensitive_col,
        model=result["model"],
        scaler=result["scaler"],
        X_train=result["X_train"],
        X_test=result["X_test"],
        X_test_scaled=result["X_test_scaled"],
        y_test=result["y_test"],
        s_test=result["s_test"],
        y_pred=result["y_pred"],
        feature_names=result["feature_names"],
        original_metrics=result["metrics"],
    )

    return JSONResponse({
        "success": True,
        "target_col": req.target_col,
        "sensitive_col": req.sensitive_col,
        "metrics": result["metrics"],
        "model_info": {
            "type": "Logistic Regression",
            "features_used": len(result["feature_names"]),
            "test_samples": len(result["y_test"]),
        }
    })
