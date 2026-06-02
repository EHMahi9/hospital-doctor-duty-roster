# API Documentation

Base URL: `/api`

Authentication uses a Bearer JWT:

```http
Authorization: Bearer <access_token>
```

## Authentication

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| POST | `/auth/login` | Public | Login and receive JWT |
| POST | `/auth/register` | Public when enabled | Create staff roster-view account or claim an existing doctor profile |
| GET | `/auth/me` | Authenticated | Current user profile |
| POST | `/auth/users` | Super Admin, Admin | Create user account |

## Doctors

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| GET | `/doctors` | Authenticated | Search/filter doctors |
| POST | `/doctors` | Super Admin, Admin | Add doctor and optional login account |
| GET | `/doctors/{doctor_id}` | Authenticated | Doctor details |
| PATCH | `/doctors/{doctor_id}` | Super Admin, Admin | Edit doctor |
| DELETE | `/doctors/{doctor_id}` | Super Admin, Admin | Deactivate doctor |
| GET | `/doctors/departments` | Authenticated | Department list |
| POST | `/doctors/departments` | Super Admin, Admin | Create department |

## Leaves

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| GET | `/leaves` | Super Admin, Admin; own records for Doctor | List leaves by doctor/status/date |
| POST | `/leaves` | Super Admin, Admin, Doctor | Apply leave |
| PATCH | `/leaves/{leave_id}/decision` | Super Admin, Admin | Approve/reject leave |
| GET | `/leaves/conflicts` | Super Admin, Admin | Approved leave vs roster conflicts |

## Roster

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| GET | `/roster` | Authenticated | Monthly roster |
| POST | `/roster/generate` | Super Admin, Admin | Generate monthly roster |
| POST | `/roster/manual-override` | Super Admin, Admin | Manually assign/replace duty |
| GET | `/roster/conflicts` | Authenticated | Detect roster conflicts |
| GET | `/roster/summary` | Authenticated | Monthly summary statistics |
| GET | `/roster/export.xlsx` | Authenticated | Excel export |
| GET | `/roster/export.pdf` | Authenticated | PDF export |

## Analytics

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| GET | `/analytics/overview` | Super Admin, Admin | Dashboard cards and charts |
| GET | `/analytics/balance-ledger` | Super Admin, Admin | Fairness/workload ledger |

## Notifications and Audit

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| GET | `/notifications` | Authenticated | User notifications |
| POST | `/notifications/shift-reminders` | Super Admin, Admin | Queue duty reminders |
| GET | `/audit` | Super Admin, Admin | Audit log search |

## Example Generate Request

```json
{
  "month": 6,
  "year": 2026,
  "overwrite": true,
  "preserve_manual_overrides": true,
  "seed": 202606
}
```

## Example Manual Override

```json
{
  "doctor_id": 4,
  "duty_date": "2026-06-12",
  "duty_type": "Emergency Night",
  "notes": "Emergency coverage adjustment",
  "force": true
}
```
