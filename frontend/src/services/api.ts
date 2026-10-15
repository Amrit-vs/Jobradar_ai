import type { CollectionStats, Company, Job, ParsedResume, Resume } from "../types/api";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options);

  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }

  // DELETE endpoints can return HTTP 204 with no body.
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = { jobs: () => request<Job[]>("/jobs"), job: (id: string) => request<Job>(`/jobs/${id}`), companies: () => request<Company[]>("/companies"), collect: () => request<CollectionStats>("/admin/collect", { method: "POST" }), resumes: () => request<Resume[]>("/resumes"), resume: (id: number) => request<Resume>(`/resumes/${id}`), uploadResume: (file: File) => { const form = new FormData(); form.append("file", file); return request<Resume>("/resumes/upload", { method: "POST", body: form }); }, updateResumeProfile: (id: number, data: ParsedResume) => request<Resume>(`/resumes/${id}/profile`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }), activateResume: (id: number) => request<Resume>(`/resumes/${id}/activate`, { method: "POST" }), deleteResume: (id: number) => request<void>(`/resumes/${id}`, { method: "DELETE" }) };
