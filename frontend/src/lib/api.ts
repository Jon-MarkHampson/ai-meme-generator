import axios from "axios";
import Cookies from "js-cookie";

// Create an Axios instance with dynamic base URL and credentials
const API = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  withCredentials: true, // send cookies if any
});

// Automatically attach JWT to every request if present
API.interceptors.request.use((config) => {
  const token = Cookies.get("token");
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default API;
