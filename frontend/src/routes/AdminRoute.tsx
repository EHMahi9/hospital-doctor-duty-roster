import { Navigate, Outlet } from "react-router-dom";

import { isAdminRole } from "@/lib/roles";
import { useAuthStore } from "@/store/authStore";

export function AdminRoute() {
  const user = useAuthStore((state) => state.user);

  return isAdminRole(user?.role) ? <Outlet /> : <Navigate to="/roster" replace />;
}
