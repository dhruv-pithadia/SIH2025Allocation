from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import json

from app.db import get_db

router = APIRouter(prefix="/internships", tags=["internships"])


# ---------- Pydantic models (kept local to this router for now) ----------
class SkillWeight(BaseModel):
    skill_code: str
    weight: float = Field(1.0, ge=0.0, le=10.0)


class InternshipCreate(BaseModel):
    # Either provide org_id OR org_name (we'll create org if needed)
    org_id: Optional[int] = None
    org_name: Optional[str] = None

    title: str
    description: Optional[str] = None
    req_skills_text: Optional[str] = None

    min_cgpa: float = 0.0

    location: Optional[str] = None
    pincode: Optional[str] = Field(None, min_length=3, max_length=6)

    capacity: int = Field(1, ge=1)

    job_role_code: Optional[str] = None
    nsqf_required_level: Optional[int] = Field(None, ge=1, le=10)

    min_age: Optional[int] = Field(None, ge=14, le=80)

    genders_allowed: Optional[List[str]] = None            # e.g., ["ANY"] / ["M","F"]
    languages_required: Optional[List[str]] = None         # e.g., ["en","hi"]

    is_shift_night: bool = False

    wage_min: Optional[int] = Field(None, ge=0)
    wage_max: Optional[int] = Field(None, ge=0)

    category_quota: Optional[Dict[str, int]] = None        # e.g., {"SC":1,"ST":1}

    is_active: bool = True

    job_skills: Optional[List[SkillWeight]] = None         # structured skills list

    @validator("wage_max")
    def check_wage_range(cls, v, values):
        wmin = values.get("wage_min")
        if v is not None and wmin is not None and v < wmin:
            raise ValueError("wage_max cannot be less than wage_min")
        return v

    @validator("org_name", always=True)
    def at_least_one_org_field(cls, v, values):
        if not v and not values.get("org_id"):
            raise ValueError("Provide either org_id or org_name")
        return v


# ---------- Helpers ----------
async def _ensure_org(db: AsyncSession, org_id: Optional[int], org_name: Optional[str]) -> int:
    """Return a valid org_id. If org_name provided and not present, create it."""
    if org_id:
        exists = (await db.execute(text("SELECT org_id FROM organization WHERE org_id=:oid"), {"oid": org_id})).scalar()
        if not exists:
            raise HTTPException(400, f"Organization id {org_id} not found")
        return int(org_id)

    # create or get by org_name
    row = (await db.execute(text("SELECT org_id FROM organization WHERE org_name=:n LIMIT 1"), {"n": org_name})).scalar()
    if row:
        return int(row)

    res = await db.execute(
        text("INSERT INTO organization (org_name) VALUES (:n)"),
        {"n": org_name}
    )
    await db.commit()
    new_id = res.lastrowid or (await db.execute(text("SELECT LAST_INSERT_ID()"))).scalar()
    return int(new_id)


# ---------- Routes ----------
@router.post("", summary="Create a new internship (with optional structured skills)")
async def create_internship(payload: InternshipCreate, db: AsyncSession = Depends(get_db)):
    try:
        # 1) resolve organization
        oid = await _ensure_org(db, payload.org_id, payload.org_name)

        # 2) insert internship
        params = {
            "org_id": oid,
            "org_name": payload.org_name,
            "title": payload.title,
            "description": payload.description,
            "req_skills_text": payload.req_skills_text,
            "min_cgpa": float(payload.min_cgpa or 0.0),
            "location": payload.location,
            "pincode": payload.pincode,
            "capacity": int(payload.capacity),
            "job_role_code": payload.job_role_code,
            "nsqf_required_level": payload.nsqf_required_level,
            "min_age": payload.min_age,
            "genders_allowed": json.dumps(payload.genders_allowed) if payload.genders_allowed else None,
            "languages_required_json": json.dumps(payload.languages_required) if payload.languages_required else None,
            "is_shift_night": 1 if payload.is_shift_night else 0,
            "wage_min": payload.wage_min,
            "wage_max": payload.wage_max,
            "category_quota_json": json.dumps(payload.category_quota) if payload.category_quota else None,
            "is_active": 1 if payload.is_active else 0,
        }

        res = await db.execute(text("""
            INSERT INTO internship
              (org_id, org_name, title, description, req_skills_text,
               min_cgpa, location, pincode, capacity,
               job_role_code, nsqf_required_level, min_age,
               genders_allowed, languages_required_json,
               is_shift_night, wage_min, wage_max,
               category_quota_json, is_active)
            VALUES
              (:org_id, :org_name, :title, :description, :req_skills_text,
               :min_cgpa, :location, :pincode, :capacity,
               :job_role_code, :nsqf_required_level, :min_age,
               CAST(:genders_allowed AS JSON), CAST(:languages_required_json AS JSON),
               :is_shift_night, :wage_min, :wage_max,
               CAST(:category_quota_json AS JSON), :is_active)
        """), params)
        iid = res.lastrowid or (await db.execute(text("SELECT LAST_INSERT_ID()"))).scalar()

        # 3) insert structured job skills (if any)
        if payload.job_skills:
            rows = [{"internship_id": iid, "skill_code": s.skill_code, "weight": float(s.weight)} for s in payload.job_skills]
            await db.execute(text("""
                INSERT INTO job_skill_required (internship_id, skill_code, weight)
                VALUES (:internship_id, :skill_code, :weight)
            """), rows)

        await db.commit()

        return {"status": "success", "internship_id": int(iid)}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"Failed to create internship: {e}")


@router.get("", summary="List internships (basic)")
async def list_internships(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text("""
        SELECT i.internship_id, COALESCE(i.org_name, o.org_name) AS org_name,
               i.title, i.location, i.pincode, i.capacity, i.is_active,
               i.min_cgpa
        FROM internship i
        LEFT JOIN organization o ON o.org_id = i.org_id
        ORDER BY i.internship_id DESC
        LIMIT 200
    """))).mappings().all()
    return {"items": rows}