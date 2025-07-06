// lib/api.ts
import axios from "axios";

const API = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  withCredentials: true, // browser will include HttpOnly access_token cookie
});

// Redirect to login on 401 Unauthorized
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error.response?.status === 401 &&
      window.location.pathname !== "/login"
    ) {
      // Clear any client state if needed, then redirect
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default API;
