from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from statistics import mean
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.balance import BalanceLedger
from app.models.doctor import Doctor
from app.models.duty import DutyAssignment
from app.models.enums import DutyType, LeaveStatus, ShiftType
from app.models.leave import LeaveRequest


def month_bounds(month: int, year: int) -> tuple[date, date]:
    last_day = monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def duty_weight(assignment: DutyAssignment) -> float:
    if assignment.shift == ShiftType.NIGHT:
        return 1.4
    if assignment.duty_type in {DutyType.EMERGENCY_MORNING, DutyType.EMERGENCY_EVENING}:
        return 1.2
    return 1.0


def is_emergency(duty_type: DutyType) -> bool:
    return duty_type in {
        DutyType.EMERGENCY_MORNING,
        DutyType.EMERGENCY_EVENING,
        DutyType.EMERGENCY_NIGHT,
    }


def is_indoor(duty_type: DutyType) -> bool:
    return duty_type in {DutyType.INDOOR_MORNING, DutyType.INDOOR_NIGHT}


def calculate_monthly_summary(db: Session, month: int, year: int) -> dict[str, Any]:
    start, end = month_bounds(month, year)
    assignments = (
        db.query(DutyAssignment)
        .join(Doctor)
        .filter(DutyAssignment.duty_date >= start, DutyAssignment.duty_date <= end)
        .all()
    )

    by_doctor: dict[int, dict[str, Any]] = {}
    for assignment in assignments:
        doctor = assignment.doctor
        row = by_doctor.setdefault(
            doctor.id,
            {
                "doctor_id": doctor.id,
                "doctor_name": doctor.name,
                "department": doctor.department.name if doctor.department else None,
                "emergency": 0,
                "indoor": 0,
                "outdoor": 0,
                "night": 0,
                "total": 0,
                "weighted_workload": 0.0,
                "max_monthly_duty": doctor.max_monthly_duty,
            },
        )
        row["total"] += 1
        row["weighted_workload"] += duty_weight(assignment)
        if is_emergency(assignment.duty_type):
            row["emergency"] += 1
        elif is_indoor(assignment.duty_type):
            row["indoor"] += 1
        else:
            row["outdoor"] += 1
        if assignment.shift == ShiftType.NIGHT:
            row["night"] += 1

    workloads = [item["weighted_workload"] for item in by_doctor.values()]
    average_workload = mean(workloads) if workloads else 0
    for item in by_doctor.values():
        variance = abs(item["weighted_workload"] - average_workload)
        item["fairness_score"] = round(max(0, 100 - (variance * 12)), 2)
        item["overtime_hours"] = max(0, item["total"] - item["max_monthly_duty"]) * 8

    return {
        "month": month,
        "year": year,
        "total_duties": len(assignments),
        "emergency_duties": sum(1 for item in assignments if is_emergency(item.duty_type)),
        "indoor_duties": sum(1 for item in assignments if is_indoor(item.duty_type)),
        "outdoor_duties": sum(1 for item in assignments if item.duty_type == DutyType.OUTDOOR),
        "night_duties": sum(1 for item in assignments if item.shift == ShiftType.NIGHT),
        "overtime_hours": float(sum(row.get("overtime_hours", 0) for row in by_doctor.values())),
        "by_doctor": sorted(by_doctor.values(), key=lambda row: row["doctor_name"]),
    }


def refresh_balance_ledgers(db: Session, month: int, year: int) -> list[BalanceLedger]:
    summary = calculate_monthly_summary(db, month, year)
    ledgers: list[BalanceLedger] = []

    for row in summary["by_doctor"]:
        ledger = (
            db.query(BalanceLedger)
            .filter(
                BalanceLedger.doctor_id == row["doctor_id"],
                BalanceLedger.month == month,
                BalanceLedger.year == year,
            )
            .one_or_none()
        )
        if not ledger:
            ledger = BalanceLedger(doctor_id=row["doctor_id"], month=month, year=year)
            db.add(ledger)

        extra_duties = max(0, row["total"] - row["max_monthly_duty"])
        missed_duties = max(0, row["max_monthly_duty"] - row["total"])
        ledger.emergency_count = row["emergency"]
        ledger.indoor_count = row["indoor"]
        ledger.outdoor_count = row["outdoor"]
        ledger.night_count = row["night"]
        ledger.total_duties = row["total"]
        ledger.extra_duties = extra_duties
        ledger.missed_duties = missed_duties
        ledger.overtime_hours = float(row["overtime_hours"])
        ledger.fairness_score = float(row["fairness_score"])
        ledger.workload_score = float(row["weighted_workload"])
        ledgers.append(ledger)

    db.flush()
    return ledgers


def dashboard_overview(db: Session, month: int, year: int) -> dict[str, Any]:
    start, end = month_bounds(month, year)
    summary = calculate_monthly_summary(db, month, year)
    today = date.today()
    upcoming_limit = today + timedelta(days=14)

    upcoming_leaves = (
        db.query(func.count(LeaveRequest.id))
        .filter(
            LeaveRequest.status == LeaveStatus.APPROVED,
            LeaveRequest.leave_date >= today,
            LeaveRequest.leave_date <= upcoming_limit,
        )
        .scalar()
        or 0
    )

    leave_status_rows = (
        db.query(LeaveRequest.status, func.count(LeaveRequest.id))
        .filter(LeaveRequest.leave_date >= start, LeaveRequest.leave_date <= end)
        .group_by(LeaveRequest.status)
        .all()
    )

    return {
        "total_doctors": db.query(func.count(Doctor.id)).filter(Doctor.is_active.is_(True)).scalar() or 0,
        "total_duties": summary["total_duties"],
        "emergency_duty_count": summary["emergency_duties"],
        "indoor_duty_count": summary["indoor_duties"],
        "outdoor_duty_count": summary["outdoor_duties"],
        "upcoming_leaves": upcoming_leaves,
        "workload_analytics": summary["by_doctor"],
        "duty_mix": [
            {"name": "Emergency", "value": summary["emergency_duties"]},
            {"name": "Indoor", "value": summary["indoor_duties"]},
            {"name": "Outdoor", "value": summary["outdoor_duties"]},
            {"name": "Night", "value": summary["night_duties"]},
        ],
        "leave_status": [{"status": status.value, "count": count} for status, count in leave_status_rows],
    }
