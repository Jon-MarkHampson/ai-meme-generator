// lib/api.ts
import axios from "axios";
import { logoutSilently } from "@/context/AuthContext"; // helper you export

const API = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  withCredentials: true,
});

API.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      logoutSilently(); // clear React state, but DON’T change location
    }
    return Promise.reject(err);
  }
);

export default API;
