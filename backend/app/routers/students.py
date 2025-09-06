from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import pandas as pd
from app.db import get_db
from app.allocation import run_allocation

router = APIRouter(prefix="/upload", tags=["students"])

REQUIRED = ["name", "email", "category_code", "disability_code"]

@router.post("/students")
async def upload_students(file: UploadFile, auto_allocate: bool = True,
                          db: AsyncSession = Depends(get_db)):
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(400, f"Invalid CSV: {e}")

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise HTTPException(400, f"Missing required columns: {missing}")

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "name": str(r.get("name","")).strip(),
            "email": str(r.get("email","")).strip(),
            "phone": (None if pd.isna(r.get("phone")) else str(r.get("phone"))),
            "highest_qualification": (None if pd.isna(r.get("highest_qualification")) else str(r.get("highest_qualification"))),
            "cgpa": (None if pd.isna(r.get("cgpa")) else float(r.get("cgpa"))),
            "tenth_percent": (None if pd.isna(r.get("tenth_percent")) else float(r.get("tenth_percent"))),
            "twelfth_percent": (None if pd.isna(r.get("twelfth_percent")) else float(r.get("twelfth_percent"))),
            "location_pref": (None if pd.isna(r.get("location_pref")) else str(r.get("location_pref"))),
            "pincode": (None if pd.isna(r.get("pincode")) else str(r.get("pincode"))),
            "category_code": str(r.get("category_code") or "GEN"),
            "disability_code": str(r.get("disability_code") or "NONE"),
            "languages_json": r.get("languages_json") or '["hi"]',
            "skills_text": (None if pd.isna(r.get("skills_text")) else str(r.get("skills_text")))
        })

    await db.execute(text("""
        INSERT INTO student
            (name, email, phone, highest_qualification, cgpa, tenth_percent, twelfth_percent,
             location_pref, pincode, category_code, disability_code, languages_json, skills_text)
        VALUES
            (:name, :email, :phone, :highest_qualification, :cgpa, :tenth_percent, :twelfth_percent,
             :location_pref, :pincode, :category_code, :disability_code, CAST(:languages_json AS JSON), :skills_text)
    """), rows)
    await db.commit()

    run_id = await run_allocation(db) if auto_allocate else None
    return {"status": "success", "uploaded": len(rows), "run_id": run_id}