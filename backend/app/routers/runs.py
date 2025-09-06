from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db import get_db
from app.allocation import run_allocation

router = APIRouter(prefix="/run", tags=["allocation"])

@router.post("/")
async def run_now(db: AsyncSession = Depends(get_db)):
    rid = await run_allocation(db)
    return {"run_id": rid, "status": "SUCCESS"}

@router.get("/{run_id}/results")
async def run_results(run_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text("""
        SELECT mr.run_id, s.student_id, s.name AS student_name, s.email,
               i.internship_id, i.title AS internship_title,
               COALESCE(i.org_name, o.org_name) AS organization,
               i.location, i.pincode, mr.final_score, mr.component_json, mr.created_at
        FROM match_result mr
        JOIN student s ON s.student_id = mr.student_id
        JOIN internship i ON i.internship_id = mr.internship_id
        LEFT JOIN organization o ON o.org_id = i.org_id
        WHERE mr.run_id = :rid
        ORDER BY mr.final_score DESC
    """), {"rid": run_id})).mappings().all()
    return {"count": len(rows), "results": [dict(r) for r in rows]}

@router.get("/latest")
async def latest_run(db: AsyncSession = Depends(get_db)):
    rid = (await db.execute(text("""
        SELECT run_id FROM alloc_run WHERE status='SUCCESS'
        ORDER BY created_at DESC LIMIT 1
    """))).scalar()
    if not rid:
        raise HTTPException(404, "No successful run yet")
    return {"run_id": int(rid)}