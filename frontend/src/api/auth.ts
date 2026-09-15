/** Authentication API client. Access JWT stays in memory; refresh token is HttpOnly cookie. */
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

let _accessToken: string | null = null;

export function setAccessToken(token: string): void { _accessToken = token; }
export function clearAccessToken(): void { _accessToken = null; }
export function hasAccessToken(): boolean { return _accessToken !== null; }
export function getAccessToken(): string | null { return _accessToken; }

const apiClient = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  if (_accessToken) config.headers.Authorization = `Bearer ${_accessToken}`;
  return config;
});

export async function apiLogin(email: string, password: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/login", { email, password });
  return response.data;
}

export async function apiRegister(data: Record<string, unknown>): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/register", data);
  return response.data;
}

export async function apiRefresh(): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/refresh");
  return response.data;
}

export async function apiLogout(): Promise<void> {
  try { await apiClient.post("/auth/logout"); } finally { clearAccessToken(); }
}

export async function apiGetCurrentUser(): Promise<UserProfile> {
  const response = await apiClient.get<UserProfile>("/auth/me");
  return response.data;
}

export default apiClient;
