import type { CollectionStats, Company, Job } from "../types/api";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";
async function request<T>(path: string, options?: RequestInit): Promise<T> { const response = await fetch(`${API_BASE}${path}`, options); if (!response.ok) throw new Error(`Request failed (${response.status})`); return response.json() as Promise<T>; }
export const api = { jobs: () => request<Job[]>("/jobs"), job: (id: string) => request<Job>(`/jobs/${id}`), companies: () => request<Company[]>("/companies"), collect: () => request<CollectionStats>("/admin/collect", { method: "POST" }) };

