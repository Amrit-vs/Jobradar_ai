import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { App } from "./App";
import type { ParsedResume, Resume } from "./types/api";

test("shows the dashboard shell", () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => [] }));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><MemoryRouter><App /></MemoryRouter></QueryClientProvider>);

  expect(screen.getByText("JobRadar", { exact: false })).toBeInTheDocument();
  expect(screen.getByText("Loading jobs…")).toBeInTheDocument();
});

afterEach(() => vi.unstubAllGlobals());

test("renders API jobs with freshness and filters them", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => [{ id: 1, company: "Google", company_slug: "google", title: "AI Engineer", description: "Mock description", location: "Bengaluru, India", url: "https://example.invalid", posted_at: null, employment_type: "Full-time", experience_level: "New Grad", source: "MOCK", status: "NEW", freshness: "FRESH" }] }));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><MemoryRouter><App /></MemoryRouter></QueryClientProvider>);
  expect(await screen.findByText("AI Engineer")).toBeInTheDocument();
  expect(screen.getAllByText("FRESH").length).toBeGreaterThan(0);
  fireEvent.change(screen.getByLabelText("Filter jobs"), { target: { value: "backend" } });
  expect(screen.getByText(/No jobs yet/)).toBeInTheDocument();
});

test("renders API-backed companies", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => [{ id: 1, name: "NVIDIA", enabled: true, job_count: 5, last_collection_status: "success", last_collection_at: null }] }));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/companies"]}><App /></MemoryRouter></QueryClientProvider>);
  expect(await screen.findByText("NVIDIA")).toBeInTheDocument();
  expect(screen.getByText("5 jobs")).toBeInTheDocument();
});

test("renders job details and a manual apply link", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ id: 1, company: "Adobe", company_slug: "adobe", title: "Frontend Engineer", description: "Mock job description", location: "Noida, India", url: "https://example.invalid/apply", posted_at: null, employment_type: "Full-time", experience_level: "0–2 years", source: "MOCK", status: "NEW", freshness: "FRESH" }) }));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/jobs/1"]}><App /></MemoryRouter></QueryClientProvider>);
  expect(await screen.findByText("Mock job description")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Apply now" })).toHaveAttribute("href", "https://example.invalid/apply");
});

test("renders the resume upload area", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => [] }));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/resume-profile"]}><App /></MemoryRouter></QueryClientProvider>);
  expect(
  await screen.findByRole("heading", { name: "Resume & Profile" })
).toBeInTheDocument();
  expect(screen.getByLabelText("Upload resume")).toBeInTheDocument();
});

const profile: ParsedResume = { full_name: "Ada", email: null, phone: null, location: null, linkedin_url: null, github_url: null, skills: ["Python"], education: [], experience: [], projects: [], certifications: [], raw_text: "Ada" };

function resumeFixture(overrides: Partial<Resume> = {}): Resume {
  return { id: 1, filename: "resume.pdf", file_type: "pdf", file_size: 100, uploaded_at: "2026-10-15T00:00:00Z", updated_at: "2026-10-15T00:00:00Z", parsing_status: "completed", parsing_error: null, is_active: false, parsed_data: profile, ...overrides };
}

function renderResumes() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/resume-profile"]}><App /></MemoryRouter></QueryClientProvider>);
}

test("updates the selected editor after activation and preserves unsaved fields", async () => {
  let resume = resumeFixture();
  vi.stubGlobal("fetch", vi.fn().mockImplementation(async (url: string) => {
    if (url.endsWith("/activate")) resume = { ...resume, is_active: true };
    return { ok: true, json: async () => url.endsWith("/resumes") ? [resume] : resume };
  }));
  renderResumes();
  fireEvent.click(await screen.findByRole("button", { name: /resume.pdf · completed/ }));
  const name = await screen.findByLabelText("Name");
  fireEvent.change(name, { target: { value: "Unsaved edit" } });
  expect(screen.getByText(/Inactive resume/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Set as Active" }));
  expect(await screen.findByText(/^Active resume/)).toBeInTheDocument();
  expect(name).toHaveValue("Unsaved edit");
});

test("deletes a failed resume without parsed data", async () => {
  const failed = resumeFixture({ filename: "broken.pdf", parsing_status: "failed", parsing_error: "Could not read this PDF.", parsed_data: null });
  let removed = false;
  const fetchMock = vi.fn().mockImplementation(async (url: string, options?: RequestInit) => {
    if (options?.method === "DELETE") { removed = true; return { ok: true, status: 204 }; }
    return { ok: true, json: async () => url.endsWith("/resumes") ? (removed ? [] : [failed]) : failed };
  });
  vi.stubGlobal("fetch", fetchMock);
  renderResumes();
  fireEvent.click(await screen.findByRole("button", { name: /broken.pdf · failed/ }));
  expect(await screen.findByText("Could not read this PDF.")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Delete Resume" }));
  await waitFor(() => expect(screen.queryByRole("button", { name: /broken.pdf/ })).not.toBeInTheDocument());
  expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/resumes/1"), { method: "DELETE" });
});

