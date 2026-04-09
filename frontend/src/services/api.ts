import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export const api = axios.create({
  baseURL: `${BASE_URL}/api`,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);
