import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from ..state import update_store, reset_store

router = APIRouter()


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload a CSV dataset. Stores it in memory and returns column names + preview.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    try:
        reset_store()
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV. Please ensure it is a valid comma-separated file. Error: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="Uploaded CSV is empty.")

    reset_store()
    update_store(dataframe=df, filename=file.filename)

    # Build column metadata
    col_info = []
    for col in df.columns:
        col_info.append({
            "name": col,
            "dtype": str(df[col].dtype),
            "unique_count": int(df[col].nunique()),
            "null_count": int(df[col].isnull().sum()),
        })

    # Preview: first 5 rows as list of dicts
    preview = df.head(5).fillna("").to_dict(orient="records")

    return JSONResponse({
        "success": True,
        "filename": file.filename,
        "rows": len(df),
        "columns": col_info,
        "preview": preview,
    })
