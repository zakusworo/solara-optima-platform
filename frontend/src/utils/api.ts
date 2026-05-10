import axios from 'axios'

// Base URL: empty string in dev so Vite proxy handles /api/*.
// In production, set VITE_API_URL to the backend origin (e.g. https://api.example.com).
export const API_BASE_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

export const api = axios.create({
  baseURL: API_BASE_URL,
})

export const apiUrl = (path: string): string => {
  const normalized = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE_URL}${normalized}`
}
