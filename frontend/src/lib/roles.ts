import type { UserRole } from "@/types/api";

export function isAdminRole(role: UserRole | undefined) {
  return role === "super_admin" || role === "admin";
}
