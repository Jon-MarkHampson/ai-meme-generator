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
        // Don't redirect automatically - let SessionContext handle it
        // This prevents the infinite reload loop
        console.log('[API] 401 detected, session expired - triggering logout event');
        
        // Dispatch custom event to notify SessionContext
        window.dispatchEvent(new CustomEvent('session-expired'));
      }
    }

    return Promise.reject(error);
  }
);

export default API;
