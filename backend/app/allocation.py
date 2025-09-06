# app/allocation.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
import json
import numpy as np
from scipy.optimize import linear_sum_assignment
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

# -----------------------------
# Scoring helpers (tunable)
# -----------------------------

def _tokenize(text: Optional[str]) -> set[str]:
    if not text:
        return set()
    import re
    toks = re.split(r"[^a-zA-Z0-9+#]+", text.lower())
    return set(t for t in toks if t and len(t) > 1)

def _preference_bonus(ranked: Optional[int]) -> float:
    # lower rank = stronger boost
    if ranked is None:
        return 0.0
    return {1: 0.20, 2: 0.10, 3: 0.05}.get(int(ranked), 0.0)

# Weights for final score
WEIGHTS = {
    "exact": 0.55,   # structured skill overlap (student_skill vs job_skill_required)
    "sem":   0.20,   # simple semantic overlap from free-text (Jaccard over tokens)
    "pref":  0.15,   # preference bonus from 'preference.ranked'
    "loc":   0.10,   # rough locality proximity (pincode prefix match)
}

# -----------------------------
# Data fetch
# -----------------------------

async def _fetch_students(db: AsyncSession) -> List[Dict[str, Any]]:
    rows = (await db.execute(text("""
        SELECT student_id, name, email, highest_qualification, cgpa, pincode, category_code,
               disability_code, skills_text
        FROM student
    """))).mappings().all()
    return [dict(r) for r in rows]

async def _fetch_student_skills(db: AsyncSession) -> Dict[int, Dict[str, float]]:
    rows = (await db.execute(text("""
        SELECT student_id, skill_code, COALESCE(proficiency,0) AS proficiency
        FROM student_skill
    """))).mappings().all()
    by_student: Dict[int, Dict[str, float]] = {}
    for r in rows:
        by_student.setdefault(int(r["student_id"]), {})[r["skill_code"]] = float(r["proficiency"]) / 5.0
    return by_student

async def _fetch_internships(db: AsyncSession) -> List[Dict[str, Any]]:
    rows = (await db.execute(text("""
        SELECT internship_id, org_id, org_name, title, req_skills_text,
               min_cgpa, location, pincode, capacity
        FROM internship
        WHERE is_active = 1
    """))).mappings().all()
    return [dict(r) for r in rows]

async def _fetch_job_skill_weights(db: AsyncSession) -> Dict[int, Dict[str, float]]:
    rows = (await db.execute(text("""
        SELECT internship_id, skill_code, COALESCE(weight,1.0) AS weight
        FROM job_skill_required
    """))).mappings().all()
    weights: Dict[int, Dict[str, float]] = {}
    for r in rows:
        weights.setdefault(int(r["internship_id"]), {})[r["skill_code"]] = float(r["weight"])
    return weights

async def _fetch_preferences(db: AsyncSession) -> Dict[Tuple[int,int], int]:
    rows = (await db.execute(text("""
        SELECT student_id, internship_id, ranked
        FROM preference
    """))).mappings().all()
    return {(int(r["student_id"]), int(r["internship_id"])): int(r["ranked"]) for r in rows}

# -----------------------------
# Scoring per student–job pair
# -----------------------------

def _score_pair(
    s: Dict[str,Any],
    j: Dict[str,Any],
    s_struct: Dict[str,float],
    j_weights: Dict[str,float],
    pref_rank: Optional[int]
) -> Tuple[float, Dict[str, float], Optional[str]]:
    # CGPA gate (only if job has a min_cgpa > 0)
    cgpa = float(s["cgpa"]) if s.get("cgpa") is not None else None
    min_cgpa = float(j["min_cgpa"]) if j.get("min_cgpa") is not None else 0.0
    if min_cgpa > 0 and (cgpa is None or cgpa < min_cgpa):
        return 0.0, {"exact":0, "sem":0, "pref":0, "loc":0}, "cgpa_fail"

    # Structured skill overlap (weighted)
    total_w = sum(j_weights.values()) or 1.0
    exact = 0.0
    if j_weights and s_struct:
        for k, w in j_weights.items():
            exact += (s_struct.get(k, 0.0)) * w
        exact = min(exact / total_w, 1.0)

    # Semantic overlap via token Jaccard on free text
    sem = 0.0
    s_tokens = _tokenize(s.get("skills_text"))
    j_tokens = _tokenize(j.get("req_skills_text"))
    if s_tokens or j_tokens:
        sem = len(s_tokens & j_tokens) / float(len(s_tokens | j_tokens))

    # Preference
    pref = _preference_bonus(pref_rank)

    # Location proximity (same pincode prefix)
    loc = 0.0
    sp = (s.get("pincode") or "")[:3]
    jp = (j.get("pincode") or "")[:3]
    if sp and jp and sp == jp:
        loc = 1.0

    final = (
        WEIGHTS["exact"] * exact +
        WEIGHTS["sem"]   * sem   +
        WEIGHTS["pref"]  * pref  +
        WEIGHTS["loc"]   * loc
    )

    breakdown = {"exact": round(exact,3), "sem": round(sem,3), "pref": round(pref,3), "loc": round(loc,3)}
    return float(final), breakdown, None

# -----------------------------
# Capacity expansion
# -----------------------------

def _expand_internships(internships: List[Dict[str,Any]]) -> List[Dict[str,Any]]:
    slots: List[Dict[str,Any]] = []
    for j in internships:
        cap = int(j.get("capacity") or 1)
        for si in range(cap):
            slots.append({
                "internship_id": int(j["internship_id"]),
                "slot_index": si + 1,
                "title": j["title"],
                "pincode": j.get("pincode"),
                "min_cgpa": j.get("min_cgpa"),
                "req_skills_text": j.get("req_skills_text"),
            })
    return slots

# -----------------------------
# Main entry: run allocation
# -----------------------------

async def run_allocation(db: AsyncSession, params: Optional[Dict[str, Any]] = None) -> int:
    """
    Creates an alloc_run, computes scores, runs Hungarian assignment (capacity-aware),
    writes match_result rows, and updates alloc_run metrics. Returns run_id.
    """
    # 1) Start a run
    params_json = {
        "weights": WEIGHTS,
        "notes": "Initial production-ready allocation run",
    }
    if params:
        params_json.update(params)

    # NOTE: Using JSON_OBJECT requires MySQL-side construction; simpler is to store as text JSON via parameter
    run_id = (await db.execute(text("""
        INSERT INTO alloc_run (status, params_json, metrics_json)
        VALUES ('RUNNING', :params_json, NULL)
    """), {"params_json": json.dumps(params_json)})).lastrowid
    await db.commit()

    # 2) Fetch all data
    students = await _fetch_students(db)
    internships = await _fetch_internships(db)
    if not students or not internships:
        await db.execute(text("""
            UPDATE alloc_run SET status='FAILED', error_message=:msg WHERE run_id=:rid
        """), {"msg": "Insufficient data (students or internships missing)", "rid": run_id})
        await db.commit()
        return int(run_id)

    skills_by_student = await _fetch_student_skills(db)
    weights_by_job    = await _fetch_job_skill_weights(db)
    preferences       = await _fetch_preferences(db)

    # 3) Build cost matrix for Hungarian (minimize cost = 1 - score)
    slots = _expand_internships(internships)
    nS, nJ = len(students), len(slots)
    if nS == 0 or nJ == 0:
        await db.execute(text("""
            UPDATE alloc_run SET status='FAILED', error_message='No students or no capacity' WHERE run_id=:rid
        """), {"rid": run_id})
        await db.commit()
        return int(run_id)

    cost = np.ones((nS, nJ), dtype=float)  # default high cost
    # Map for breakdown retrieval when inserting
    pair_breakdown: Dict[Tuple[int,int], Dict[str,float]] = {}
    # Keep a quick lookup of internship row by id
    job_by_id: Dict[int, Dict[str,Any]] = {int(j["internship_id"]): j for j in internships}

    for si, s in enumerate(students):
        s_struct = skills_by_student.get(int(s["student_id"]), {})
        for ji, slot in enumerate(slots):
            int_id = int(slot["internship_id"])
            job = job_by_id[int_id]
            pref_rank = preferences.get((int(s["student_id"]), int_id))
            score, breakdown, reason = _score_pair(s, job, s_struct, weights_by_job.get(int_id, {}), pref_rank)
            # Ineligible => very high cost
            c = 1.0 - score if reason is None else 1.0
            cost[si, ji] = c
            if reason is None:
                pair_breakdown[(int(s["student_id"]), int_id)] = breakdown

    # 4) Hungarian assignment
    row_ind, col_ind = linear_sum_assignment(cost)

    # 5) Insert results (skip zero-score assignments)
    assigned = 0
    inserts: List[Dict[str,Any]] = []
    for r, c in zip(row_ind, col_ind):
        s = students[int(r)]
        slot = slots[int(c)]
        sid = int(s["student_id"])
        iid = int(slot["internship_id"])
        score = float(1.0 - cost[r, c])
        if score <= 0.0:
            continue  # ignore useless/ineligible assignment
        bd = pair_breakdown.get((sid, iid), {"exact":0, "sem":0, "pref":0, "loc":0})
        inserts.append({
            "run_id": int(run_id),
            "student_id": sid,
            "internship_id": iid,
            "allocated_slot": int(slot["slot_index"]),
            "final_score": round(score, 4),
            "component_json": json.dumps(bd),
            "explanation": f"exact={bd['exact']}, sem={bd['sem']}, pref={bd['pref']}, loc={bd['loc']}"
        })
        assigned += 1

    if inserts:
        await db.execute(text("""
            INSERT INTO match_result
              (run_id, student_id, internship_id, allocated_slot, final_score, component_json, explanation)
            VALUES
              (:run_id, :student_id, :internship_id, :allocated_slot, :final_score, CAST(:component_json AS JSON), :explanation)
        """), inserts)

    # 6) Metrics
    metrics = {
        "assigned": assigned,
        "students_total": len(students),
        "slots_total": len(slots),
        "fill_rate": round(assigned / max(1, len(slots)), 4),
        "coverage": round(assigned / max(1, len(students)), 4),
    }

    await db.execute(text("""
        UPDATE alloc_run
           SET status='SUCCESS',
               metrics_json=:metrics_json
         WHERE run_id=:rid
    """), {"metrics_json": json.dumps(metrics), "rid": run_id})
    await db.commit()

    return int(run_id)

# -----------------------------
# Optional: quick manual test
# -----------------------------
if __name__ == "__main__":
    import asyncio
    from sqlalchemy import text
    from .db import AsyncSessionLocal, engine  # <-- import engine so we can dispose it

    async def _smoke():
        try:
            async with AsyncSessionLocal() as db:
                rid = await run_allocation(db)
                print("Run ID:", rid)
                rows = (await db.execute(text("""
                    SELECT s.name AS student, i.title AS job, mr.final_score
                    FROM match_result mr
                    JOIN student s ON s.student_id = mr.student_id
                    JOIN internship i ON i.internship_id = mr.internship_id
                    WHERE mr.run_id = :rid
                    ORDER BY mr.final_score DESC
                    LIMIT 10
                """), {"rid": rid})).mappings().all()
                for r in rows:
                    print(f"{r['student']} -> {r['job']} [{r['final_score']}]")
        finally:
            # 🔒 make sure everything closes before the event loop ends
            await engine.dispose()

    asyncio.run(_smoke())