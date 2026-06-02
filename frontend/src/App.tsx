import { Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";

import { AppShell } from "@/components/layout/AppShell";
import { AdminRoute } from "@/routes/AdminRoute";
import { HomeRoute } from "@/routes/HomeRoute";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { AnalyticsPage } from "@/features/analytics/AnalyticsPage";
import { DoctorsPage } from "@/features/doctors/DoctorsPage";
import { LeavesPage } from "@/features/leaves/LeavesPage";
import { RosterPage } from "@/features/roster/RosterPage";

export function App() {
  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route index element={<HomeRoute />} />
            <Route path="roster" element={<RosterPage />} />
            <Route element={<AdminRoute />}>
              <Route path="doctors" element={<DoctorsPage />} />
              <Route path="leaves" element={<LeavesPage />} />
              <Route path="analytics" element={<AnalyticsPage />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster richColors theme="dark" position="top-right" />
    </>
  );
}
