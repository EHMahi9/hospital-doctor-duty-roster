from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.balance import BalanceLedger
from app.models.user import User
from app.schemas.analytics import BalanceLedgerRead, DashboardOverview
from app.services.analytics_service import dashboard_overview, refresh_balance_ledgers

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
def overview(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2020, le=2100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    today = date.today()
    return dashboard_overview(db, month or today.month, year or today.year)


@router.get("/balance-ledger", response_model=list[BalanceLedgerRead])
def balance_ledger(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2020, le=2100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    today = date.today()
    month = month or today.month
    year = year or today.year
    refresh_balance_ledgers(db, month, year)
    db.commit()
    rows = db.query(BalanceLedger).filter(BalanceLedger.month == month, BalanceLedger.year == year).all()
    return [
        {
            "doctor_id": row.doctor_id,
            "doctor_name": row.doctor.name,
            "month": row.month,
            "year": row.year,
            "emergency_count": row.emergency_count,
            "indoor_count": row.indoor_count,
            "outdoor_count": row.outdoor_count,
            "night_count": row.night_count,
            "total_duties": row.total_duties,
            "extra_duties": row.extra_duties,
            "missed_duties": row.missed_duties,
            "overtime_hours": row.overtime_hours,
            "fairness_score": row.fairness_score,
            "workload_score": row.workload_score,
        }
        for row in rows
    ]
