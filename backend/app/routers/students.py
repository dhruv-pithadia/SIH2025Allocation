# app/routers/students.py
from fastapi import APIRouter, UploadFile, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import pandas as pd
from app.db import get_db
from app.allocation import run_allocation

router = APIRouter(prefix="/upload", tags=["students"])

REQUIRED = ["name", "email", "category_code", "disability_code"]


@router.post("/students")
async def upload_students(
    file: UploadFile,
    auto_allocate: bool = True,
    mode: str = Query("upsert", regex="^(skip|upsert|replace_all)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a CSV of students and (optionally) auto-allocate them.

    mode=skip        -> INSERT IGNORE (keep existing emails as-is)
    mode=upsert      -> INSERT ... ON DUPLICATE KEY UPDATE (update existing emails)
    mode=replace_all -> TRUNCATE dependent tables and student, then fresh load
    """

    # Parse CSV
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(400, f"Invalid CSV: {e}")

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise HTTPException(400, f"Missing required columns: {missing}")

    # Normalize rows
    rows = []
    emails = []
    for _, r in df.iterrows():
        email = str(r.get("email", "")).strip()
        emails.append(email)
        rows.append({
            "name": str(r.get("name", "")).strip(),
            "email": email,
            "phone": None if pd.isna(r.get("phone")) else str(r.get("phone")),
            "highest_qualification": None if pd.isna(r.get("highest_qualification")) else str(r.get("highest_qualification")),
            "cgpa": None if pd.isna(r.get("cgpa")) else float(r.get("cgpa")),
            "tenth_percent": None if pd.isna(r.get("tenth_percent")) else float(r.get("tenth_percent")),
            "twelfth_percent": None if pd.isna(r.get("twelfth_percent")) else float(r.get("twelfth_percent")),
            "location_pref": None if pd.isna(r.get("location_pref")) else str(r.get("location_pref")),
            "pincode": None if pd.isna(r.get("pincode")) else str(r.get("pincode")),
            "category_code": str(r.get("category_code") or "GEN"),
            "disability_code": str(r.get("disability_code") or "NONE"),
            "languages_json": r.get("languages_json") or '["hi"]',
            "skills_text": None if pd.isna(r.get("skills_text")) else str(r.get("skills_text")),
        })
    if not rows:
        raise HTTPException(400, "CSV has no rows")

    # Optional: replace all
    if mode == "replace_all":
        # careful: TRUNCATE requires privileges
        for tbl in ("match_result", "student_availability", "student_skill", "preference"):
            await db.execute(text(f"TRUNCATE TABLE {tbl}"))
        await db.execute(text("TRUNCATE TABLE student"))
        await db.commit()

    # Build INSERT statement per mode
    if mode == "skip":
        insert_sql = text("""
            INSERT IGNORE INTO student
              (name, email, phone, highest_qualification, cgpa, tenth_percent, twelfth_percent,
               location_pref, pincode, category_code, disability_code, languages_json, skills_text)
            VALUES
              (:name, :email, :phone, :highest_qualification, :cgpa, :tenth_percent, :twelfth_percent,
               :location_pref, :pincode, :category_code, :disability_code, CAST(:languages_json AS JSON), :skills_text)
        """)
        result = await db.execute(insert_sql, rows)
        await db.commit()
        inserted = result.rowcount or 0
        updated = 0
        skipped = len(rows) - inserted

    elif mode == "upsert":
        insert_sql = text("""
            INSERT INTO student
              (name, email, phone, highest_qualification, cgpa, tenth_percent, twelfth_percent,
               location_pref, pincode, category_code, disability_code, languages_json, skills_text)
            VALUES
              (:name, :email, :phone, :highest_qualification, :cgpa, :tenth_percent, :twelfth_percent,
               :location_pref, :pincode, :category_code, :disability_code, CAST(:languages_json AS JSON), :skills_text)
            AS new
            ON DUPLICATE KEY UPDATE
              name                  = COALESCE(new.name, student.name),
              phone                 = COALESCE(new.phone, student.phone),
              highest_qualification = COALESCE(new.highest_qualification, student.highest_qualification),
              cgpa                  = COALESCE(new.cgpa, student.cgpa),
              tenth_percent         = COALESCE(new.tenth_percent, student.tenth_percent),
              twelfth_percent       = COALESCE(new.twelfth_percent, student.twelfth_percent),
              location_pref         = COALESCE(new.location_pref, student.location_pref),
              pincode               = COALESCE(new.pincode, student.pincode),
              category_code         = COALESCE(new.category_code, student.category_code),
              disability_code       = COALESCE(new.disability_code, student.disability_code),
              languages_json        = COALESCE(CAST(new.languages_json AS JSON), student.languages_json),
              skills_text           = COALESCE(new.skills_text, student.skills_text),
              updated_at            = CURRENT_TIMESTAMP
        """)
        result = await db.execute(insert_sql, rows)
        await db.commit()
        affected = result.rowcount or 0
        existing = (await db.execute(text("""
            SELECT email FROM student WHERE email IN :emails
        """), {"emails": tuple(emails)})).scalars().all()
        existing_set = set(existing)
        updated = sum(1 for r in rows if r["email"] in existing_set)
        inserted = len(rows) - updated
        skipped = 0

    else:  # replace_all inserts
        insert_sql = text("""
            INSERT INTO student
              (name, email, phone, highest_qualification, cgpa, tenth_percent, twelfth_percent,
               location_pref, pincode, category_code, disability_code, languages_json, skills_text)
            VALUES
              (:name, :email, :phone, :highest_qualification, :cgpa, :tenth_percent, :twelfth_percent,
               :location_pref, :pincode, :category_code, :disability_code, CAST(:languages_json AS JSON), :skills_text)
        """)
        result = await db.execute(insert_sql, rows)
        await db.commit()
        inserted = result.rowcount or len(rows)
        updated = 0
        skipped = 0

    # Run allocation only for these emails, keeping existing matches frozen
    run_id = None
    if auto_allocate:
        run_id = await run_allocation(db, scope_emails=emails, respect_existing=True)

    return {
        "status": "success",
        "mode": mode,
        "uploaded_rows": len(rows),
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "run_id": run_id,
    }