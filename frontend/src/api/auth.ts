/**
 * API client — auth endpoints only.
 *
 * SECURITY:
 * - Access tokens are stored in memory (module-level variable), NOT in
 *   localStorage or sessionStorage. This prevents XSS-based token theft.
 * - The token is cleared on logout or tab close (memory-only).
 * - Credentials are NEVER logged by this module.
 *
 * NOTE: The spec does not define a refresh-token mechanism with sufficient
 * detail to implement safely, so only login / me / logout (clear) are provided.
 */

import axios from "axios";

const API_BASE = "/api/v1";

export interface UserProfile {
  id: string;
  organization_id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}

export interface ApiError {
  detail?: string;
  error?: string;
  message?: string;
}

// ── In-memory token store ─────────────────────────────────────────────────
let _accessToken: string | null = null;

export function setAccessToken(token: string): void {
  _accessToken = token;
}

export function clearAccessToken(): void {
  _accessToken = null;
}

export function hasAccessToken(): boolean {
  return _accessToken !== null;
}

// ── Axios instance ────────────────────────────────────────────────────────
const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Attach the access token to every request (from memory, never from storage)
apiClient.interceptors.request.use((config) => {
  if (_accessToken) {
    config.headers["Authorization"] = `Bearer ${_accessToken}`;
  }
  return config;
});

// ── Auth API calls ────────────────────────────────────────────────────────

export async function apiLogin(
  email: string,
  password: string
): Promise<TokenResponse> {
  // Credentials are sent over HTTPS (enforced in deployment)
  const response = await apiClient.post<TokenResponse>("/auth/login", {
    email,
    password,
  });
  return response.data;
}

export async function apiRegister(data: Record<string, any>): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/register", data);
  return response.data;
}

export async function apiGetCurrentUser(): Promise<UserProfile> {
  const response = await apiClient.get<UserProfile>("/auth/me");
  return response.data;
}

export default apiClient;
