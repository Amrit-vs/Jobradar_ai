import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, vi } from "vitest";
import { App } from "./App";

test("shows the dashboard shell", () => {
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
  expect(screen.getByText("FRESH")).toBeInTheDocument();
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
