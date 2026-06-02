import { Navigate } from "react-router-dom";

import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { isAdminRole } from "@/lib/roles";
import { useAuthStore } from "@/store/authStore";

export function HomeRoute() {
  const user = useAuthStore((state) => state.user);

  return isAdminRole(user?.role) ? <DashboardPage /> : <Navigate to="/roster" replace />;
}
