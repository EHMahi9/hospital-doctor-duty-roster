from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from heapq import heappop, heappush
from random import Random
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.models.doctor import Doctor
from app.models.duty import DutyAssignment, RosterRun
from app.models.enums import DutyType, LeaveStatus, PreferredShift, ShiftType
from app.models.leave import LeaveRequest
from app.models.user import User
from app.services.analytics_service import calculate_monthly_summary, month_bounds, refresh_balance_ledgers
from app.services.audit_service import write_audit_log

WEEKDAY_INDEX = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


@dataclass(frozen=True)
class DutyDefinition:
    duty_type: DutyType
    shift: ShiftType
    workload_weight: float


DUTY_DEFINITIONS: tuple[DutyDefinition, ...] = (
    DutyDefinition(DutyType.EMERGENCY_MORNING, ShiftType.MORNING, 1.2),
    DutyDefinition(DutyType.EMERGENCY_EVENING, ShiftType.EVENING, 1.2),
    DutyDefinition(DutyType.EMERGENCY_NIGHT, ShiftType.NIGHT, 1.6),
    DutyDefinition(DutyType.INDOOR_MORNING, ShiftType.MORNING, 1.0),
    DutyDefinition(DutyType.INDOOR_NIGHT, ShiftType.NIGHT, 1.4),
    DutyDefinition(DutyType.OUTDOOR, ShiftType.OUTDOOR, 0.9),
)


class RosterScheduler:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_monthly_roster(
        self,
        *,
        month: int,
        year: int,
        actor: User | None,
        overwrite: bool = False,
        preserve_manual_overrides: bool = True,
        seed: int | None = None,
    ) -> dict[str, Any]:
        start, end = month_bounds(month, year)
        random = Random(seed)

        if overwrite:
            delete_query = self.db.query(DutyAssignment).filter(
                DutyAssignment.duty_date >= start,
                DutyAssignment.duty_date <= end,
            )
            if preserve_manual_overrides:
                delete_query = delete_query.filter(DutyAssignment.is_manual_override.is_(False))
            delete_query.delete(synchronize_session=False)
            self.db.flush()

        doctors = (
            self.db.query(Doctor)
            .options(joinedload(Doctor.department))
            .filter(Doctor.is_active.is_(True))
            .order_by(Doctor.name.asc())
            .all()
        )
        if not doctors:
            raise ValueError("No active doctors are available for roster generation.")

        existing_assignments = self._load_assignments(start, end)
        assignments_by_doctor_day = self._assignments_by_doctor_day(existing_assignments)
        assignments_by_slot = {(item.duty_date, item.duty_type): item for item in existing_assignments}
        approved_leaves = self._approved_leave_dates(start, end)
        monthly_counts = defaultdict(int)
        type_counts = defaultdict(lambda: defaultdict(int))
        night_counts = defaultdict(int)
        workload_scores = defaultdict(float)

        for assignment in existing_assignments:
            monthly_counts[assignment.doctor_id] += 1
            type_counts[assignment.doctor_id][assignment.duty_type] += 1
            workload_scores[assignment.doctor_id] += self._definition_for(assignment.duty_type).workload_weight
            if assignment.shift == ShiftType.NIGHT:
                night_counts[assignment.doctor_id] += 1

        run = RosterRun(month=month, year=year, generated_by_id=actor.id if actor else None, seed=seed, status="running")
        self.db.add(run)
        self.db.flush()

        created_count = 0
        conflicts: list[dict[str, Any]] = []
        current = start
        while current <= end:
            for definition in DUTY_DEFINITIONS:
                if (current, definition.duty_type) in assignments_by_slot:
                    continue

                heap: list[tuple[float, int, Doctor]] = []
                for doctor in doctors:
                    reasons = self._candidate_blockers(
                        doctor=doctor,
                        duty_date=current,
                        definition=definition,
                        approved_leaves=approved_leaves,
                        assignments_by_doctor_day=assignments_by_doctor_day,
                        monthly_count=monthly_counts[doctor.id],
                    )
                    if reasons:
                        continue

                    score = self._candidate_score(
                        doctor=doctor,
                        definition=definition,
                        monthly_count=monthly_counts[doctor.id],
                        type_count=type_counts[doctor.id][definition.duty_type],
                        night_count=night_counts[doctor.id],
                        workload_score=workload_scores[doctor.id],
                        random=random,
                    )
                    heappush(heap, (score, doctor.id, doctor))

                if not heap:
                    conflicts.append(
                        {
                            "code": "UNFILLED_SLOT",
                            "severity": "high",
                            "message": f"No eligible doctor found for {definition.duty_type.value} on {current.isoformat()}.",
                            "duty_date": current,
                            "duty_type": definition.duty_type,
                        }
                    )
                    continue

                _, _, selected = heappop(heap)
                assignment = DutyAssignment(
                    doctor_id=selected.id,
                    duty_date=current,
                    duty_type=definition.duty_type,
                    shift=definition.shift,
                    roster_run_id=run.id,
                    created_by_id=actor.id if actor else None,
                    is_manual_override=False,
                    source="auto",
                )
                self.db.add(assignment)
                self.db.flush()
                created_count += 1
                assignments_by_slot[(current, definition.duty_type)] = assignment
                assignments_by_doctor_day[(selected.id, current)].append(assignment)
                monthly_counts[selected.id] += 1
                type_counts[selected.id][definition.duty_type] += 1
                workload_scores[selected.id] += definition.workload_weight
                if definition.shift == ShiftType.NIGHT:
                    night_counts[selected.id] += 1

            current += timedelta(days=1)

        refresh_balance_ledgers(self.db, month, year)
        summary = calculate_monthly_summary(self.db, month, year)
        run.status = "completed_with_conflicts" if conflicts else "completed"
        run.summary_json = {
            "assignments_created": created_count,
            "conflict_count": len(conflicts),
            "total_duties": summary["total_duties"],
        }
        write_audit_log(
            self.db,
            actor=actor,
            action="roster.generate",
            entity_type="RosterRun",
            entity_id=run.id,
            metadata={"month": month, "year": year, "assignments_created": created_count, "conflicts": len(conflicts)},
        )
        self.db.commit()
        self.db.refresh(run)
        return {"run": run, "assignments_created": created_count, "conflicts": conflicts}

    def manual_override(
        self,
        *,
        doctor_id: int,
        duty_date: date,
        duty_type: DutyType,
        notes: str | None,
        force: bool,
        actor: User,
    ) -> tuple[DutyAssignment | None, list[dict[str, Any]]]:
        doctor = self.db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.is_active.is_(True)).one_or_none()
        if not doctor:
            return None, [
                {
                    "code": "DOCTOR_NOT_FOUND",
                    "severity": "high",
                    "message": "Doctor is inactive or does not exist.",
                    "duty_date": duty_date,
                    "duty_type": duty_type,
                    "doctor_id": doctor_id,
                }
            ]

        definition = self._definition_for(duty_type)
        month_start, month_end = month_bounds(duty_date.month, duty_date.year)
        assignments = self._load_assignments(month_start, month_end)
        approved_leaves = self._approved_leave_dates(month_start, month_end)
        assignments_by_doctor_day = self._assignments_by_doctor_day(assignments)
        monthly_count = sum(1 for item in assignments if item.doctor_id == doctor_id)
        conflicts = self._candidate_blockers(
            doctor=doctor,
            duty_date=duty_date,
            definition=definition,
            approved_leaves=approved_leaves,
            assignments_by_doctor_day=assignments_by_doctor_day,
            monthly_count=monthly_count,
        )

        existing_slot = next(
            (item for item in assignments if item.duty_date == duty_date and item.duty_type == duty_type),
            None,
        )
        if existing_slot and existing_slot.doctor_id != doctor_id:
            conflicts.append(
                {
                    "code": "SLOT_ALREADY_FILLED",
                    "severity": "medium",
                    "message": f"{existing_slot.doctor.name} is already assigned to this duty slot.",
                    "duty_date": duty_date,
                    "duty_type": duty_type,
                    "doctor_id": existing_slot.doctor_id,
                    "doctor_name": existing_slot.doctor.name,
                    "assignment_id": existing_slot.id,
                }
            )

        if conflicts and not force:
            return None, conflicts

        delete_ids = set()
        for item in assignments:
            if item.duty_date == duty_date and (item.duty_type == duty_type or item.doctor_id == doctor_id):
                delete_ids.add(item.id)
        if delete_ids:
            self.db.query(DutyAssignment).filter(DutyAssignment.id.in_(delete_ids)).delete(synchronize_session=False)
            self.db.flush()

        assignment = DutyAssignment(
            doctor_id=doctor_id,
            duty_date=duty_date,
            duty_type=duty_type,
            shift=definition.shift,
            is_manual_override=True,
            source="manual",
            notes=notes,
            created_by_id=actor.id,
        )
        self.db.add(assignment)
        self.db.flush()
        refresh_balance_ledgers(self.db, duty_date.month, duty_date.year)
        write_audit_log(
            self.db,
            actor=actor,
            action="roster.manual_override",
            entity_type="DutyAssignment",
            entity_id=assignment.id,
            metadata={"force": force, "conflicts": len(conflicts)},
        )
        self.db.commit()
        self.db.refresh(assignment)
        return assignment, conflicts

    def detect_conflicts(self, *, month: int, year: int) -> list[dict[str, Any]]:
        start, end = month_bounds(month, year)
        doctors = {doctor.id: doctor for doctor in self.db.query(Doctor).all()}
        assignments = self._load_assignments(start, end)
        assignments_by_slot = defaultdict(list)
        assignments_by_doctor_day = defaultdict(list)
        conflicts: list[dict[str, Any]] = []

        for assignment in assignments:
            assignments_by_slot[(assignment.duty_date, assignment.duty_type)].append(assignment)
            assignments_by_doctor_day[(assignment.doctor_id, assignment.duty_date)].append(assignment)

        current = start
        while current <= end:
            for definition in DUTY_DEFINITIONS:
                if not assignments_by_slot[(current, definition.duty_type)]:
                    conflicts.append(
                        {
                            "code": "UNFILLED_SLOT",
                            "severity": "high",
                            "message": f"No doctor assigned for {definition.duty_type.value}.",
                            "duty_date": current,
                            "duty_type": definition.duty_type,
                        }
                    )
            current += timedelta(days=1)

        approved_leaves = self._approved_leave_dates(start, end)
        for (doctor_id, duty_date), day_assignments in list(assignments_by_doctor_day.items()):
            doctor = doctors.get(doctor_id)
            if not doctor:
                continue
            if len(day_assignments) > 1:
                conflicts.append(
                    {
                        "code": "DOUBLE_DUTY",
                        "severity": "high",
                        "message": f"{doctor.name} has more than one duty on {duty_date.isoformat()}.",
                        "duty_date": duty_date,
                        "doctor_id": doctor_id,
                        "doctor_name": doctor.name,
                    }
                )
            if (doctor_id, duty_date) in approved_leaves:
                conflicts.append(self._conflict("ON_LEAVE", doctor, duty_date, day_assignments[0]))
            if self._is_weekly_off(doctor, duty_date):
                conflicts.append(self._conflict("WEEKLY_OFF", doctor, duty_date, day_assignments[0]))
            if any(item.shift == ShiftType.NIGHT for item in day_assignments):
                prev_day = duty_date - timedelta(days=1)
                next_day = duty_date + timedelta(days=1)
                if any(item.shift == ShiftType.NIGHT for item in assignments_by_doctor_day.get((doctor_id, prev_day), [])):
                    conflicts.append(self._conflict("CONSECUTIVE_NIGHT", doctor, duty_date, day_assignments[0]))
                if any(item.shift == ShiftType.NIGHT for item in assignments_by_doctor_day.get((doctor_id, next_day), [])):
                    conflicts.append(self._conflict("CONSECUTIVE_NIGHT", doctor, duty_date, day_assignments[0]))

        counts = defaultdict(int)
        for assignment in assignments:
            counts[assignment.doctor_id] += 1
        for doctor_id, total in counts.items():
            doctor = doctors.get(doctor_id)
            if doctor and total > doctor.max_monthly_duty:
                conflicts.append(
                    {
                        "code": "OVERLOADED",
                        "severity": "medium",
                        "message": f"{doctor.name} has {total} duties, above the configured monthly maximum of {doctor.max_monthly_duty}.",
                        "doctor_id": doctor.id,
                        "doctor_name": doctor.name,
                    }
                )
        return conflicts

    def _candidate_blockers(
        self,
        *,
        doctor: Doctor,
        duty_date: date,
        definition: DutyDefinition,
        approved_leaves: set[tuple[int, date]],
        assignments_by_doctor_day: dict[tuple[int, date], list[DutyAssignment]],
        monthly_count: int,
    ) -> list[dict[str, Any]]:
        blockers: list[dict[str, Any]] = []
        existing_today = assignments_by_doctor_day.get((doctor.id, duty_date), [])
        if existing_today:
            blockers.append(self._conflict("DOUBLE_DUTY", doctor, duty_date, existing_today[0], definition.duty_type))
        if (doctor.id, duty_date) in approved_leaves:
            blockers.append(self._conflict("ON_LEAVE", doctor, duty_date, None, definition.duty_type))
        if self._is_weekly_off(doctor, duty_date):
            blockers.append(self._conflict("WEEKLY_OFF", doctor, duty_date, None, definition.duty_type))
        if monthly_count >= doctor.max_monthly_duty:
            blockers.append(
                {
                    "code": "OVERLOADED",
                    "severity": "medium",
                    "message": f"{doctor.name} already reached max monthly duty ({doctor.max_monthly_duty}).",
                    "duty_date": duty_date,
                    "duty_type": definition.duty_type,
                    "doctor_id": doctor.id,
                    "doctor_name": doctor.name,
                }
            )
        if definition.shift == ShiftType.NIGHT and self._has_adjacent_night(
            doctor.id,
            duty_date,
            assignments_by_doctor_day,
        ):
            blockers.append(self._conflict("CONSECUTIVE_NIGHT", doctor, duty_date, None, definition.duty_type))
        return blockers

    def _candidate_score(
        self,
        *,
        doctor: Doctor,
        definition: DutyDefinition,
        monthly_count: int,
        type_count: int,
        night_count: int,
        workload_score: float,
        random: Random,
    ) -> float:
        preferred_penalty = 0.0
        if doctor.preferred_shift != PreferredShift.FLEXIBLE and doctor.preferred_shift.value != definition.shift.value:
            preferred_penalty = 1.5
        night_penalty = night_count * 2.5 if definition.shift == ShiftType.NIGHT else night_count * 0.4
        load_ratio = monthly_count / max(doctor.max_monthly_duty, 1)
        return (
            monthly_count * 10
            + type_count * 3
            + workload_score * 2
            + load_ratio * 8
            + night_penalty
            + preferred_penalty
            + random.random() * 0.1
        )

    def _load_assignments(self, start: date, end: date) -> list[DutyAssignment]:
        return (
            self.db.query(DutyAssignment)
            .options(joinedload(DutyAssignment.doctor).joinedload(Doctor.department))
            .filter(DutyAssignment.duty_date >= start, DutyAssignment.duty_date <= end)
            .all()
        )

    def _approved_leave_dates(self, start: date, end: date) -> set[tuple[int, date]]:
        rows = (
            self.db.query(LeaveRequest.doctor_id, LeaveRequest.leave_date)
            .filter(
                LeaveRequest.status == LeaveStatus.APPROVED,
                LeaveRequest.leave_date >= start,
                LeaveRequest.leave_date <= end,
            )
            .all()
        )
        return {(doctor_id, leave_date) for doctor_id, leave_date in rows}

    @staticmethod
    def _assignments_by_doctor_day(assignments: list[DutyAssignment]) -> dict[tuple[int, date], list[DutyAssignment]]:
        grouped: dict[tuple[int, date], list[DutyAssignment]] = defaultdict(list)
        for assignment in assignments:
            grouped[(assignment.doctor_id, assignment.duty_date)].append(assignment)
        return grouped

    @staticmethod
    def _definition_for(duty_type: DutyType) -> DutyDefinition:
        for definition in DUTY_DEFINITIONS:
            if definition.duty_type == duty_type:
                return definition
        raise ValueError(f"Unsupported duty type: {duty_type}")

    @staticmethod
    def _is_weekly_off(doctor: Doctor, duty_date: date) -> bool:
        return WEEKDAY_INDEX.get(doctor.weekly_off_day, -1) == duty_date.weekday()

    @staticmethod
    def _has_adjacent_night(
        doctor_id: int,
        duty_date: date,
        assignments_by_doctor_day: dict[tuple[int, date], list[DutyAssignment]],
    ) -> bool:
        prev_day = duty_date - timedelta(days=1)
        next_day = duty_date + timedelta(days=1)
        return any(item.shift == ShiftType.NIGHT for item in assignments_by_doctor_day.get((doctor_id, prev_day), [])) or any(
            item.shift == ShiftType.NIGHT for item in assignments_by_doctor_day.get((doctor_id, next_day), [])
        )

    @staticmethod
    def _conflict(
        code: str,
        doctor: Doctor,
        duty_date: date,
        assignment: DutyAssignment | None,
        duty_type: DutyType | None = None,
    ) -> dict[str, Any]:
        messages = {
            "DOUBLE_DUTY": f"{doctor.name} already has a duty on {duty_date.isoformat()}.",
            "ON_LEAVE": f"{doctor.name} is on approved leave on {duty_date.isoformat()}.",
            "WEEKLY_OFF": f"{doctor.name} has weekly off on {duty_date.isoformat()}.",
            "CONSECUTIVE_NIGHT": f"{doctor.name} would receive consecutive night shifts.",
        }
        return {
            "code": code,
            "severity": "high" if code in {"DOUBLE_DUTY", "ON_LEAVE"} else "medium",
            "message": messages.get(code, "Roster conflict detected."),
            "duty_date": duty_date,
            "duty_type": duty_type or (assignment.duty_type if assignment else None),
            "doctor_id": doctor.id,
            "doctor_name": doctor.name,
            "assignment_id": assignment.id if assignment else None,
        }
