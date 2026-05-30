import { api } from "@/api/client";
import type {
  BalanceLedger,
  DashboardOverview,
  Department,
  Doctor,
  DutyAssignment,
  DutyType,
  LeaveRequest,
  LeaveStatus,
  LoginResponse,
  MonthlySummary,
  RosterConflict
} from "@/types/api";

export const authApi = {
  login: async (email: string, password: string) => {
    const { data } = await api.post<LoginResponse>("/auth/login", { email, password });
    return data;
  },
  me: async () => {
    const { data } = await api.get<LoginResponse["user"]>("/auth/me");
    return data;
  }
};

export const doctorApi = {
  list: async (params?: { search?: string; department_id?: number; is_active?: boolean }) => {
    const { data } = await api.get<Doctor[]>("/doctors", { params });
    return data;
  },
  create: async (payload: Partial<Doctor> & { initial_password?: string; create_user_account?: boolean }) => {
    const { data } = await api.post<Doctor>("/doctors", payload);
    return data;
  },
  update: async (id: number, payload: Partial<Doctor>) => {
    const { data } = await api.patch<Doctor>(`/doctors/${id}`, payload);
    return data;
  },
  remove: async (id: number) => {
    const { data } = await api.delete<{ message: string }>(`/doctors/${id}`);
    return data;
  },
  departments: async () => {
    const { data } = await api.get<Department[]>("/doctors/departments");
    return data;
  }
};

export const leaveApi = {
  list: async (params?: { doctor_id?: number; status?: LeaveStatus; from_date?: string; to_date?: string }) => {
    const { data } = await api.get<LeaveRequest[]>("/leaves", { params });
    return data;
  },
  apply: async (payload: Pick<LeaveRequest, "doctor_id" | "leave_date" | "leave_type" | "reason">) => {
    const { data } = await api.post<LeaveRequest>("/leaves", payload);
    return data;
  },
  decide: async (id: number, status: Exclude<LeaveStatus, "pending">, review_note?: string, force = false) => {
    const { data } = await api.patch<LeaveRequest>(`/leaves/${id}/decision`, { status, review_note }, { params: { force } });
    return data;
  }
};

export const rosterApi = {
  list: async (month: number, year: number, params?: { department_id?: number; doctor_id?: number }) => {
    const { data } = await api.get<DutyAssignment[]>("/roster", { params: { month, year, ...params } });
    return data;
  },
  generate: async (payload: { month: number; year: number; overwrite: boolean; preserve_manual_overrides: boolean; seed?: number }) => {
    const { data } = await api.post<{ assignments_created: number; conflicts: RosterConflict[] }>("/roster/generate", payload);
    return data;
  },
  manualOverride: async (payload: { doctor_id: number; duty_date: string; duty_type: DutyType; notes?: string; force?: boolean }) => {
    const { data } = await api.post<DutyAssignment>("/roster/manual-override", payload);
    return data;
  },
  conflicts: async (month: number, year: number) => {
    const { data } = await api.get<RosterConflict[]>("/roster/conflicts", { params: { month, year } });
    return data;
  },
  summary: async (month: number, year: number) => {
    const { data } = await api.get<MonthlySummary>("/roster/summary", { params: { month, year } });
    return data;
  },
  exportFile: async (month: number, year: number, type: "xlsx" | "pdf") => {
    const { data } = await api.get<Blob>(`/roster/export.${type}`, {
      params: { month, year },
      responseType: "blob"
    });
    return data;
  }
};

export const analyticsApi = {
  overview: async (month: number, year: number) => {
    const { data } = await api.get<DashboardOverview>("/analytics/overview", { params: { month, year } });
    return data;
  },
  balanceLedger: async (month: number, year: number) => {
    const { data } = await api.get<BalanceLedger[]>("/analytics/balance-ledger", { params: { month, year } });
    return data;
  }
};
