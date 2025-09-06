from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import csv, io
from app.db import get_db

router = APIRouter(prefix="/download", tags=["export"])

@router.get("/{run_id}.csv")
async def download_csv(run_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text("""
        SELECT s.student_id, s.name AS student_name, s.email,
               i.internship_id, i.title AS internship_title,
               COALESCE(i.org_name, o.org_name) AS organization,
               i.location, i.pincode, mr.final_score
        FROM match_result mr
        JOIN student s ON s.student_id = mr.student_id
        JOIN internship i ON i.internship_id = mr.internship_id
        LEFT JOIN organization o ON o.org_id = i.org_id
        WHERE mr.run_id = :rid
        ORDER BY mr.final_score DESC
    """), {"rid": run_id})).mappings().all()

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["student_id","student_name","email","internship_id","internship_title","organization","location","pincode","final_score"])
    for r in rows:
        w.writerow([r["student_id"], r["student_name"], r["email"], r["internship_id"],
                    r["internship_title"], r["organization"], r["location"], r["pincode"], r["final_score"]])

    return Response(out.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="allocation_run_{run_id}.csv"'})