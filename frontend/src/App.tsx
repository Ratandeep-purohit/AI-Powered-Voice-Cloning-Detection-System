import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { AppShell } from "./components/AppShell";
import { ProductDashboardPage } from "./pages/ProductDashboardPage";

export default function App() {
  return <AuthProvider><BrowserRouter><Routes>
    <Route path="/" element={<LandingPage/>}/>
    <Route path="/login" element={<LoginPage/>}/>
    <Route path="/register" element={<RegisterPage/>}/>
    <Route element={<ProtectedRoute><AppShell/></ProtectedRoute>}>
      <Route path="/dashboard" element={<ProductDashboardPage mode="overview"/>}/>
      <Route path="/dashboard/analysis" element={<ProductDashboardPage mode="analysis"/>}/>
      <Route path="/dashboard/audio" element={<ProductDashboardPage mode="audio"/>}/>
      <Route path="/dashboard/alerts" element={<ProductDashboardPage mode="alerts"/>}/>
      <Route path="/dashboard/reports" element={<ProductDashboardPage mode="reports"/>}/>
      <Route path="/dashboard/organization" element={<ProductDashboardPage mode="organization"/>}/>
      <Route path="/dashboard/settings" element={<ProductDashboardPage mode="settings"/>}/>
    </Route>
    <Route path="*" element={<Navigate to="/" replace/>}/>
  </Routes></BrowserRouter></AuthProvider>;
}
