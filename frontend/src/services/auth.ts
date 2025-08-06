import API from "./api";
import { User, SignupResponse } from "@/types/auth";

export async function apiSignup(
  first_name: string,
  last_name: string,
  email: string,
  password: string
): Promise<SignupResponse> {
  const resp = await API.post<SignupResponse>("/auth/signup", {
    first_name,
    last_name,
    email,
    password,
  });
  return resp.data;
}

export async function apiLogin(
  email: string,
  password: string
): Promise<{ token_type: string }> {
  const form = new URLSearchParams({ username: email, password });
  const resp = await API.post<{ token_type: string }>("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  // Note: The actual access_token is set as an HTTP-only cookie by the backend
  return resp.data;
}

export async function fetchProfile(): Promise<User> {
  const resp = await API.get<User>("/users/me");
  return resp.data;
}

export async function apiRefreshSession(): Promise<void> {
  try {
    await API.post("/auth/refresh");
  } catch (error) {
    // Re-throw the error so SessionContext can handle it,
    // but don't add extra logging here to avoid noise
    throw error;
  }
}

export async function apiUpdateProfile(
  payload: Partial<{
    current_password: string;
    first_name: string;
    last_name: string;
    email: string;
    password: string;
  }>
): Promise<User> {
  const resp = await API.patch<User>("/users/me", payload);
  return resp.data;
}

export async function apiLogout(): Promise<void> {
  await API.post("/auth/logout");
}

export async function apiDeleteAccount(password: string): Promise<void> {
  // FastAPI DELETE /users/me, body: { password }
  await API.request({
    method: "DELETE",
    url: "/users/me",
    data: { password },
  });
}

/**
 * Attempts to fetch the current user's profile to verify session.
 * Returns the User if logged in, or null if unauthorized or error.
 * This function expects potential 401s and handles them gracefully.
 */
export async function getSession(): Promise<User | null> {
  try {
    return await fetchProfile();
  } catch (error: unknown) {
    const apiError = error as { response?: { status?: number } };
    // 401 is expected when not logged in - don't treat as an error
    if (apiError.response?.status === 401) {
      return null;
    }
    // For other errors, log and return null
    console.warn("Unexpected error fetching session:", error);
    return null;
  }
}

/**
 * Get session status including time remaining.
 * Returns session info or null if unauthorized.
 * This function expects 401s when not logged in and handles them gracefully.
 */
export async function getSessionStatus(): Promise<{
  time_remaining: number;
  expires_at: number;
} | null> {
  try {
    const resp = await API.get<{
      authenticated: boolean;
      time_remaining: number;
      expires_at: number;
    }>("/auth/session-status");
    return resp.data;
  } catch (error: unknown) {
    const apiError = error as { response?: { status?: number } };
    // 401 is expected when not logged in - don't treat as an error
    if (apiError.response?.status === 401) {
      return null;
    }
    // For other errors, log and return null
    console.warn("Unexpected error fetching session status:", error);
    return null;
  }
}
