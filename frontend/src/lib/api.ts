// lib/api.ts
import axios from "axios";
import axiosRetry from "axios-retry";
import { clearAuthCookies, isPublicRoute } from "@/lib/authRoutes";
import authEvents from "@/lib/authEvents";
import { isAuthApiRoute } from "@/lib/authRoutes";

const API = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  withCredentials: true,
  timeout: 10000, // 10 second timeout
});

// Automatically retry failed network requests with exponential backoff
axiosRetry(API, {
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: axiosRetry.isNetworkError, // retry on network errors
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
  async (error: any) => {
    // Determine if this is an auth endpoint via shared helper
    const url = error?.config?.url || "";
    const isAuthEndpoint = isAuthApiRoute(url);

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !isHandling401 && !isAuthEndpoint) {
      isHandling401 = true;
      try {
        authEvents.emit("logout");
        clearAuthCookies();
        if (
          typeof window !== "undefined" &&
          !isPublicRoute(window.location.pathname)
        ) {
          window.location.replace("/?session=expired");
        }
      } catch (cleanupError) {
        console.error("Error during session cleanup:", cleanupError);
      } finally {
        setTimeout(() => {
          isHandling401 = false;
        }, 1000);
      }
    }

    // Optionally handle other statuses
    if (error.response?.status === 403) {
      console.error("Insufficient permissions");
    }
    if (error.code === "ECONNABORTED" || error.message?.includes("timeout")) {
      console.error("Request timeout or network error");
    }

    return Promise.reject(error);
  }
);

export default API;
