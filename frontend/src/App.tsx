import { Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";

import { AppShell } from "@/components/layout/AppShell";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { LoginPage } from "@/features/auth/LoginPage";
import { AnalyticsPage } from "@/features/analytics/AnalyticsPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { DoctorsPage } from "@/features/doctors/DoctorsPage";
import { LeavesPage } from "@/features/leaves/LeavesPage";
import { RosterPage } from "@/features/roster/RosterPage";

export function App() {
  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route index element={<DashboardPage />} />
            <Route path="doctors" element={<DoctorsPage />} />
            <Route path="leaves" element={<LeavesPage />} />
            <Route path="roster" element={<RosterPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster richColors theme="dark" position="top-right" />
    </>
  );
}
