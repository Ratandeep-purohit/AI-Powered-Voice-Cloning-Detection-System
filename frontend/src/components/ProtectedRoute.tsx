/**
 * Protected route wrapper.
 * Redirects unauthenticated users to /login.
 */
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div style={{ display: "grid", placeItems: "center", height: "100vh" }}>
        <p>Loading…</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Preserve the intended destination for redirect after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
