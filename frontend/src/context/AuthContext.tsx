/** Global authentication state with memory-only access token and cookie refresh. */
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { apiLogin, apiLogout, apiRefresh, setAccessToken, type UserProfile } from "../api/auth";

interface AuthState { user: UserProfile | null; isAuthenticated: boolean; isLoading: boolean; }
interface AuthContextValue extends AuthState { login: (email: string, password: string) => Promise<void>; logout: () => Promise<void>; }
const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ user: null, isAuthenticated: false, isLoading: true });

  useEffect(() => {
    let active = true;
    apiRefresh().then((data) => {
      if (!active) return;
      setAccessToken(data.access_token);
      setState({ user: data.user, isAuthenticated: true, isLoading: false });
    }).catch(() => {
      if (active) setState({ user: null, isAuthenticated: false, isLoading: false });
    });
    return () => { active = false; };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setState((s) => ({ ...s, isLoading: true }));
    try {
      const data = await apiLogin(email, password);
      setAccessToken(data.access_token);
      setState({ user: data.user, isAuthenticated: true, isLoading: false });
    } catch (err) {
      setState({ user: null, isAuthenticated: false, isLoading: false });
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    setState({ user: null, isAuthenticated: false, isLoading: false });
  }, []);

  const value = useMemo(() => ({ ...state, login, logout }), [state, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
