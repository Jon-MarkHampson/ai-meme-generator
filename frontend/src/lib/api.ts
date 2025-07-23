// lib/api.ts
import axios from "axios";
import { logoutSilently } from "@/context/AuthContext";
import { clearAuthCookies, isPublicRoute } from "@/lib/authUtils";

const API = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  withCredentials: true,
  timeout: 10000, // 10 second timeout
});

// Track if we're already handling a 401 to prevent multiple redirects
let isHandling401 = false;

// Request interceptor to add auth headers if needed
API.interceptors.request.use(
  (config) => {
    // Add any additional headers if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling session expiry
API.interceptors.response.use(
  (response) => response,
  async (error: {
    response?: { status?: number };
    code?: string;
    message?: string;
  }) => {
    // Handle 401 Unauthorized (session expired)
    if (error.response?.status === 401 && !isHandling401) {
      isHandling401 = true;

      try {
        // Clear user state using the shared function
        logoutSilently();

        // Clear any auth cookies client-side
        clearAuthCookies();

        // Only redirect if we're not already on a public route and we're in browser
        if (
          typeof window !== "undefined" &&
          !isPublicRoute(window.location.pathname)
        ) {
          // Use replace to avoid back button issues and ensure immediate redirect
          window.location.replace("/?session=expired");
        }
      } catch (cleanupError) {
        console.error("Error during session cleanup:", cleanupError);
      } finally {
        // Reset the flag after a brief delay
        setTimeout(() => {
          isHandling401 = false;
        }, 1000);
      }
    }

    // Handle network errors
    if (error.code === "ECONNABORTED" || error.message?.includes("timeout")) {
      console.error("Request timeout or network error");
      // You might want to show a toast notification here
    }

    // Handle 403 Forbidden (insufficient permissions)
    if (error.response?.status === 403) {
      console.error("Insufficient permissions");
      // You might want to show a toast notification here
    }

    return Promise.reject(error);
  }
);

export default API;
