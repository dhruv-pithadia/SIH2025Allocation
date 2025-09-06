# app/models.py
from __future__ import annotations
from typing import Optional, List, Dict
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    String, Integer, BigInteger, Text, ForeignKey, DECIMAL, JSON, DateTime, Enum, UniqueConstraint, Boolean
)
from .db import Base

# -----------------------------
# Reference Tables
# -----------------------------

class Category(Base):
    __tablename__ = "category"

    category_code: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)

    # relationships
    students: Mapped[List["Student"]] = relationship(back_populates="category")


class DisabilityType(Base):
    __tablename__ = "disability_type"

    code: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)

    # relationships
    students: Mapped[List["Student"]] = relationship(back_populates="disability")


class Organization(Base):
    __tablename__ = "organization"

    org_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    org_name: Mapped[str] = mapped_column(String(200), nullable=False)
    org_email: Mapped[Optional[str]] = mapped_column(String(200))
    org_website: Mapped[Optional[str]] = mapped_column(String(300))
    created_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False)

    internships: Mapped[List["Internship"]] = relationship(back_populates="organization")


class SkillRef(Base):
    __tablename__ = "skill_ref"

    skill_code: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    nsqf_level: Mapped[Optional[int]] = mapped_column(Integer)

    student_links: Mapped[List["StudentSkill"]] = relationship(back_populates="skill")
    job_links: Mapped[List["JobSkillRequired"]] = relationship(back_populates="skill")


# -----------------------------
# Students
# -----------------------------

HighestQualificationEnum = Enum(
    "10", "12", "ITI", "Diploma", "UG", "PG",
    name="highest_qualification_enum"
)

EvidenceEnum = Enum(
    "RPL", "ITI", "CERT", "EXP", "NONE",
    name="evidence_enum"
)

ShiftEnum = Enum(
    "DAY", "NIGHT", "BOTH",
    name="shift_enum"
)

PhoneEnum = Enum(
    "SMARTPHONE", "FEATURE", "NONE",
    name="phone_enum"
)

class Student(Base):
    __tablename__ = "student"

    student_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ext_id: Mapped[Optional[str]] = mapped_column(String(64))

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(32))

    degree: Mapped[Optional[str]] = mapped_column(String(80))
    cgpa: Mapped[Optional[float]] = mapped_column(DECIMAL(4, 2))
    # MySQL YEAR mapped as Integer in ORM
    grad_year: Mapped[Optional[int]] = mapped_column(Integer)

    highest_qualification: Mapped[Optional[str]] = mapped_column(HighestQualificationEnum)
    tenth_percent: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    twelfth_percent: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))

    location_pref: Mapped[Optional[str]] = mapped_column(String(120))
    pincode: Mapped[Optional[str]] = mapped_column(String(6))
    willing_radius_km: Mapped[Optional[int]] = mapped_column(Integer, default=20)

    category_code: Mapped[str] = mapped_column(String(16), ForeignKey("category.category_code"), nullable=False)
    disability_code: Mapped[str] = mapped_column(String(16), ForeignKey("disability_type.code"), nullable=False)

    languages_json: Mapped[Optional[Dict]] = mapped_column(JSON)
    skills_text: Mapped[Optional[str]] = mapped_column(Text)
    resume_url: Mapped[Optional[str]] = mapped_column(String(500))
    resume_summary: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False)

    # relationships
    category: Mapped["Category"] = relationship(back_populates="students")
    disability: Mapped["DisabilityType"] = relationship(back_populates="students")

    skills: Mapped[List["StudentSkill"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    availability: Mapped[Optional["StudentAvailability"]] = relationship(back_populates="student", uselist=False, cascade="all, delete-orphan")
    preferences: Mapped[List["Preference"]] = relationship(back_populates="student")
    matches: Mapped[List["MatchResult"]] = relationship(back_populates="student")


class StudentSkill(Base):
    __tablename__ = "student_skill"
    __table_args__ = (
        UniqueConstraint("student_id", "skill_code", name="pk_student_skill"),
    )

    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("student.student_id"), primary_key=True)
    skill_code: Mapped[str] = mapped_column(String(32), ForeignKey("skill_ref.skill_code"), primary_key=True)

    proficiency: Mapped[Optional[int]] = mapped_column(Integer)
    evidence: Mapped[Optional[str]] = mapped_column(EvidenceEnum, default="NONE")
    evidence_score: Mapped[Optional[int]] = mapped_column(Integer)

    student: Mapped["Student"] = relationship(back_populates="skills")
    skill: Mapped["SkillRef"] = relationship(back_populates="student_links")


class StudentAvailability(Base):
    __tablename__ = "student_availability"

    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("student.student_id"), primary_key=True)
    can_shift: Mapped[Optional[str]] = mapped_column(ShiftEnum, default="DAY")
    days_json: Mapped[Optional[Dict]] = mapped_column(JSON)
    phone_access: Mapped[Optional[str]] = mapped_column(PhoneEnum, default="FEATURE")

    student: Mapped["Student"] = relationship(back_populates="availability")


# -----------------------------
# Internships / Job Skills
# -----------------------------

class Internship(Base):
    __tablename__ = "internship"

    internship_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    org_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("organization.org_id"))
    org_name: Mapped[Optional[str]] = mapped_column(String(200))

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    req_skills_text: Mapped[Optional[str]] = mapped_column(Text)
    min_cgpa: Mapped[float] = mapped_column(DECIMAL(4, 2), nullable=False, default=0.00)

    location: Mapped[Optional[str]] = mapped_column(String(120))
    pincode: Mapped[Optional[str]] = mapped_column(String(6))
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    job_role_code: Mapped[Optional[str]] = mapped_column(String(32))
    nsqf_required_level: Mapped[Optional[int]] = mapped_column(Integer)

    min_age: Mapped[Optional[int]] = mapped_column(Integer)
    genders_allowed: Mapped[Optional[Dict]] = mapped_column(JSON)
    languages_required_json: Mapped[Optional[Dict]] = mapped_column(JSON)
    is_shift_night: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # TINYINT(1)

    wage_min: Mapped[Optional[int]] = mapped_column(Integer)
    wage_max: Mapped[Optional[int]] = mapped_column(Integer)

    category_quota_json: Mapped[Optional[Dict]] = mapped_column(JSON)

    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # TINYINT(1)
    created_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False)

    # relationships
    organization: Mapped[Optional["Organization"]] = relationship(back_populates="internships")
    required_skills: Mapped[List["JobSkillRequired"]] = relationship(back_populates="internship", cascade="all, delete-orphan")
    preferences: Mapped[List["Preference"]] = relationship(back_populates="internship")
    matches: Mapped[List["MatchResult"]] = relationship(back_populates="internship")


class JobSkillRequired(Base):
    __tablename__ = "job_skill_required"
    __table_args__ = (
        UniqueConstraint("internship_id", "skill_code", name="pk_job_skill_required"),
    )

    internship_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("internship.internship_id"), primary_key=True)
    skill_code: Mapped[str] = mapped_column(String(32), ForeignKey("skill_ref.skill_code"), primary_key=True)
    weight: Mapped[float] = mapped_column(DECIMAL(4, 2), nullable=False, default=1.00)

    internship: Mapped["Internship"] = relationship(back_populates="required_skills")
    skill: Mapped["SkillRef"] = relationship(back_populates="job_links")


# -----------------------------
# Preferences
# -----------------------------

class Preference(Base):
    __tablename__ = "preference"
    __table_args__ = (
        UniqueConstraint("student_id", "internship_id", name="ux_pref_unique"),
    )

    preference_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("student.student_id"), nullable=False)
    internship_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("internship.internship_id"), nullable=False)
    ranked: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False)

    student: Mapped["Student"] = relationship(back_populates="preferences")
    internship: Mapped["Internship"] = relationship(back_populates="preferences")


# -----------------------------
# Allocation Runs / Matches / Audit
# -----------------------------

RunStatusEnum = Enum(
    "QUEUED", "RUNNING", "SUCCESS", "FAILED",
    name="run_status_enum"
)

AuditLevelEnum = Enum(
    "INFO", "WARN", "ERROR",
    name="audit_level_enum"
)

class AllocRun(Base):
    __tablename__ = "alloc_run"

    run_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(RunStatusEnum, nullable=False, default="SUCCESS")
    params_json: Mapped[Optional[Dict]] = mapped_column(JSON)
    metrics_json: Mapped[Optional[Dict]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False)

    matches: Mapped[List["MatchResult"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    audits: Mapped[List["AuditLog"]] = relationship(back_populates="run")


class MatchResult(Base):
    __tablename__ = "match_result"
    __table_args__ = (
        UniqueConstraint("run_id", "student_id", name="ux_run_student"),
    )

    match_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("alloc_run.run_id"), nullable=False)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("student.student_id"), nullable=False)
    internship_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("internship.internship_id"), nullable=False)

    allocated_slot: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    final_score: Mapped[float] = mapped_column(DECIMAL(6, 4), nullable=False)
    component_json: Mapped[Optional[Dict]] = mapped_column(JSON)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False)

    run: Mapped["AllocRun"] = relationship(back_populates="matches")
    student: Mapped["Student"] = relationship(back_populates="matches")
    internship: Mapped["Internship"] = relationship(back_populates="matches")


class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("alloc_run.run_id"))
    level: Mapped[str] = mapped_column(AuditLevelEnum, nullable=False, default="INFO")
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    payload_json: Mapped[Optional[Dict]] = mapped_column(JSON)
    created_at: Mapped["DateTime"] = mapped_column(DateTime, nullable=False)

    run: Mapped[Optional["AllocRun"]] = relationship(back_populates="audits")