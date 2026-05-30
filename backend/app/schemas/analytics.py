from typing import Any

from pydantic import BaseModel


class DashboardOverview(BaseModel):
    total_doctors: int
    total_duties: int
    emergency_duty_count: int
    indoor_duty_count: int
    outdoor_duty_count: int
    upcoming_leaves: int
    workload_analytics: list[dict[str, Any]]
    duty_mix: list[dict[str, Any]]
    leave_status: list[dict[str, Any]]


class BalanceLedgerRead(BaseModel):
    doctor_id: int
    doctor_name: str
    month: int
    year: int
    emergency_count: int
    indoor_count: int
    outdoor_count: int
    night_count: int
    total_duties: int
    extra_duties: int
    missed_duties: int
    overtime_hours: float
    fairness_score: float
    workload_score: float
