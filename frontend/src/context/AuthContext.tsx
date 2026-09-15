/**
 * Authentication context.
 *
 * Provides authenticated user state to the entire React tree.
 * The access token lives in memory only — never in localStorage.
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import {
  apiLogin,
  clearAccessToken,
  setAccessToken,
  type UserProfile,
} from "../api/auth";

interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: false,
  });

  const logout = useCallback(() => {
    clearAccessToken();
    setState({ user: null, isAuthenticated: false, isLoading: false });
  }, []);

  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      setState((s) => ({ ...s, isLoading: true }));
      try {
        const data = await apiLogin(email, password);
        // Store token in memory — never in localStorage
        setAccessToken(data.access_token);
        setState({
          user: data.user,
          isAuthenticated: true,
          isLoading: false,
        });
      } catch (err) {
        setState({ user: null, isAuthenticated: false, isLoading: false });
        throw err; // Re-throw for the login form to handle
      }
    },
    []
  );

  const value = useMemo(
    () => ({ ...state, login, logout }),
    [state, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return ctx;
}
