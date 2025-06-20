// lib/api.ts
import axios from "axios";

const API = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  withCredentials: true, // browser will include your HttpOnly access_token cookie
});

export default API;
