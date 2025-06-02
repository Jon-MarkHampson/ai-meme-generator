import API from './api'
import Cookies from 'js-cookie'

/**
 * Matches FastAPI UserRead model exactly:
 */
export interface User {
  id: number
  username: string
  email: string
}

/**
 * Shape of the response from POST /auth/signup:
 * {
 *   user: { id, username, email },
 *   access_token: string,
 *   token_type: string
 * }
 */
interface SignupResponse {
  user: User
  access_token: string
  token_type: string
}

/**
 * Call the backend to create a new user and receive a token.
 * Now /auth/signup returns both the created User and a JWT.
 */
export async function apiSignup(
  username: string,
  email: string,
  password: string
): Promise<SignupResponse> {
  const resp = await API.post<SignupResponse>('/auth/signup', {
    username,
    email,
    password,
  })
  return resp.data
}

/**
 * Call the backend to obtain a JWT.
 * POST /auth/login responds with { access_token, token_type }.
 */
export async function apiLogin(
  username: string,
  password: string
): Promise<{ access_token: string; token_type: string }> {
  const resp = await API.post<{ access_token: string; token_type: string }>(
    '/auth/login',
    new URLSearchParams({ username, password }).toString(),
    {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }
  )
  return resp.data
}

/**
 * Fetch the current user’s profile from /users/me.
 * Thanks to the interceptor, API will auto-attach the cookie JWT.
 */
export async function fetchProfile(): Promise<{ data: User }> {
  return API.get<User>('/users/me')
}

/**
 * Update the current user’s profile.
 * Accepts partial updates, so you can send only the fields you want to change.
 * Sends a PATCH to /users/me with whichever fields changed.
 * Backend returns the updated user object.
 */
export async function apiUpdateProfile(payload: {
  username?: string
  email?: string
  password?: string
}): Promise<{ data: User }> {
  return API.patch<User>('/users/me', payload)
}

/**
 * Delete the current user, verifying by password.
 * We expect no response body (204 No Content), so we give `<void>`.
 */
export async function apiDeleteAccount(password: string): Promise<void> {
  // Bypass TS checking by casting the config object to "any"
  await API.delete<void>('/users/me', { data: { password } } as any)
}