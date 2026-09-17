import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { AppShell } from "./components/AppShell";
import {
  AlertDetailPage,
  AlertsPage,
  AnalysisDetailPage,
  AnalysisPage,
  AudioPage,
  OrganizationPage,
  ReportsPage,
  SecurityOverviewPage,
  SettingsPage,
} from "./pages/SecurityWorkspace";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
            <Route path="/dashboard" element={<SecurityOverviewPage />} />
            <Route path="/dashboard/analysis" element={<AnalysisPage />} />
            <Route path="/dashboard/analysis/:analysisId" element={<AnalysisDetailPage />} />
            <Route path="/dashboard/audio" element={<AudioPage />} />
            <Route path="/dashboard/alerts" element={<AlertsPage />} />
            <Route path="/dashboard/alerts/:alertId" element={<AlertDetailPage />} />
            <Route path="/dashboard/reports" element={<ReportsPage />} />
            <Route path="/dashboard/organization" element={<OrganizationPage />} />
            <Route path="/dashboard/settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
