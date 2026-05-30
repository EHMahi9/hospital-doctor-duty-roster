export type UserRole = "super_admin" | "admin" | "doctor" | "staff";
export type PreferredShift = "morning" | "evening" | "night" | "flexible";
export type LeaveStatus = "pending" | "approved" | "rejected";
export type LeaveType = "casual" | "sick" | "earned" | "training" | "other";
export type DutyType =
  | "Emergency Morning"
  | "Emergency Evening"
  | "Emergency Night"
  | "Indoor Morning"
  | "Indoor Night"
  | "Outdoor";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  expires_in_minutes: number;
  user: User;
}

export interface Department {
  id: number;
  name: string;
  code: string;
  is_active: boolean;
}

export interface Doctor {
  id: number;
  name: string;
  email: string;
  phone: string;
  department_id: number;
  department: Department;
  designation: string;
  max_monthly_duty: number;
  preferred_shift: PreferredShift;
  weekly_off_day: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LeaveRequest {
  id: number;
  doctor_id: number;
  leave_date: string;
  leave_type: LeaveType;
  reason: string;
  status: LeaveStatus;
  reviewed_by_id?: number | null;
  reviewed_at?: string | null;
  created_at: string;
  doctor: Doctor;
}

export interface DutyAssignment {
  id: number;
  doctor_id: number;
  duty_date: string;
  duty_type: DutyType;
  shift: "morning" | "evening" | "night" | "outdoor";
  is_manual_override: boolean;
  source: string;
  notes?: string | null;
  created_at: string;
  doctor: Doctor;
}

export interface RosterConflict {
  code: string;
  severity: "low" | "medium" | "high";
  message: string;
  duty_date?: string | null;
  duty_type?: DutyType | null;
  doctor_id?: number | null;
  doctor_name?: string | null;
  assignment_id?: number | null;
}

export interface DashboardOverview {
  total_doctors: number;
  total_duties: number;
  emergency_duty_count: number;
  indoor_duty_count: number;
  outdoor_duty_count: number;
  upcoming_leaves: number;
  workload_analytics: Array<Record<string, number | string | null>>;
  duty_mix: Array<{ name: string; value: number }>;
  leave_status: Array<{ status: LeaveStatus; count: number }>;
}

export interface MonthlySummary {
  month: number;
  year: number;
  total_duties: number;
  emergency_duties: number;
  indoor_duties: number;
  outdoor_duties: number;
  night_duties: number;
  overtime_hours: number;
  by_doctor: Array<Record<string, number | string | null>>;
}

export interface BalanceLedger {
  doctor_id: number;
  doctor_name: string;
  month: number;
  year: number;
  emergency_count: number;
  indoor_count: number;
  outdoor_count: number;
  night_count: number;
  total_duties: number;
  extra_duties: number;
  missed_duties: number;
  overtime_hours: number;
  fairness_score: number;
  workload_score: number;
}
