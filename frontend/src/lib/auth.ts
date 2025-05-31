import API from './api'

export interface User {
  id: number
  username: string
  email: string
}

export async function signup(username: string, email: string, password: string) {
  const resp = await API.post<User>('/auth/signup', { username, email, password })
  return resp.data
}

export async function login(username: string, password: string) {
  const body = new URLSearchParams({
    grant_type: 'password',
    username,
    password,
  }).toString()

  const resp = await API.post<{ access_token: string; token_type: string }>(
    '/auth/login',
    body,
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
  )
  return resp.data
}

export async function fetchProfile() {
  return API.get<User>('/users/me')
}