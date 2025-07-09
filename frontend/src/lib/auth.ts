// frontend/src/lib/auth.ts
import API from "./api";

/** Matches FastAPI’s UserRead model exactly */
export interface User {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
}

export interface SignupResponse {
  user: User;
  access_token: string;
  token_type: string;
}

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
): Promise<{ access_token: string; token_type: string }> {
  const resp = await API.post<{ access_token: string; token_type: string }>(
    "/auth/login",
    new URLSearchParams({ username: email, password }).toString(),
    { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
  );
  return resp.data;
}

export async function fetchProfile(): Promise<User> {
  const resp = await API.get<User>("/users/me");
  return resp.data;
}

export async function apiRefreshSession(): Promise<void> {
  await API.post("/auth/refresh");
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
  // axios.delete needs the data field cast to any to satisfy TS
  await API.delete<void>("/users/me", { data: { password } } as any);
}

/**
 * Attempts to fetch the current user's profile to verify session.
 * Returns the User if logged in, or null if unauthorized or error.
 */
export async function getSession(): Promise<User | null> {
  try {
    return await fetchProfile();
  } catch (error) {
    return null;
  }
}
