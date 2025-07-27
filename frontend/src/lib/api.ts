// frontend/src/lib/api.ts
import axios from "axios";
import { HOME_ROUTE } from "@/lib/authRoutes";

const API = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  withCredentials: true,
  timeout: 30000, // 30 seconds
});

// Response interceptor for 401 handling
API.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized - session expired
    if (error.response?.status === 401) {
      // Skip redirect for auth endpoints (login/signup requests)
      const isAuthEndpoint = error.config?.url?.includes("/auth/");

      if (!isAuthEndpoint && typeof window !== "undefined") {
        // Redirect to home - the backend already cleared the cookies
        window.location.href = HOME_ROUTE;
      }
    }

    return Promise.reject(error);
  }
);

export default API;
