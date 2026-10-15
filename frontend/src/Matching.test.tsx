import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { App } from "./App";
import type { Job, MatchingContext } from "./types/api";

afterEach(() => vi.unstubAllGlobals());

const context: MatchingContext = { status: "ready", resume_id: 1, filename: "reviewed.pdf", explanation: "Using saved profile." };
const job: Job = {
  id: 1, company: "Google", company_slug: "google", title: "Python Engineer", description: "Python SQL. Minimum experience: 2 years", location: "India", url: "https://example.invalid/job", posted_at: null, employment_type: "Full-time", experience_level: "2–5 years", source: "MOCK", status: "NEW", freshness: "FRESH", match_score: 75,
  matching: { status: "scored", resume_id: 1, score: 75, matched_skills: ["Python"], missing_skills: ["SQL"], components: { skill_overlap: 50, text_similarity: 80 }, weights: { skill_overlap: 0.6, text_similarity: 0.4 }, eligibility: { status: "unknown", checks: [{ criterion: "experience", status: "unknown", requirement: "2 years", candidate_value: null, reason: "Total years is not explicitly saved." }] }, explanation: "Skill coverage and TF-IDF cosine similarity; eligibility is separate.", method: "pairwise-tfidf-v1" }
};

function renderPage(path = "/jobs") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}><App /></MemoryRouter></QueryClientProvider>);
}

function mockApi(currentContext = context) {
  const fetchMock = vi.fn().mockImplementation(async (url: string) => {
    const parsed = new URL(url);
    if (parsed.pathname.endsWith("/matching/context")) return { ok: true, json: async () => currentContext };
    if (parsed.pathname.endsWith("/companies")) return { ok: true, json: async () => [{ id: 1, name: "Google" }] };
    if (parsed.pathname.endsWith("/jobs/1")) return { ok: true, json: async () => job };
    const jobs = Number(parsed.searchParams.get("min_match_score")) > 75 ? [] : [job];
    return { ok: true, json: async () => jobs };
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

test("job cards show score, matched skills, missing skills, and unknown eligibility", async () => {
  mockApi();
  renderPage();
  expect(await screen.findByText("Match: 75/100")).toBeInTheDocument();
  expect(screen.getByText("Matched skills:").parentElement).toHaveTextContent("Python");
  expect(screen.getByText("SQL", { exact: true })).toBeInTheDocument();
  expect(screen.getByText("unknown", { exact: true })).toBeInTheDocument();
});

test("best-match sorting and minimum score reach the backend and explain empty results", async () => {
  const fetchMock = mockApi();
  renderPage();
  await screen.findByText("Match: 75/100");
  const minimum = screen.getByLabelText("Minimum match score");
  await waitFor(() => expect(minimum).toBeEnabled());
  fireEvent.change(screen.getByLabelText("Sort jobs"), { target: { value: "match_score" } });
  fireEvent.change(minimum, { target: { value: "90" } });
  expect(await screen.findByText(/No jobs match these filters/)).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("sort_by=match_score&min_match_score=90"), undefined);
  // Company options remain available even when the score filter removes all jobs.
  expect(screen.getByRole("option", { name: "Google" })).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Minimum match score"), { target: { value: "" } });
  expect(await screen.findByText("Match: 75/100")).toBeInTheDocument();
});

test("no active resume offers review guidance without hiding jobs", async () => {
  mockApi({ status: "no_active_resume", resume_id: null, filename: null, explanation: "Review and activate a resume to see scores." });
  renderPage();
  expect(await screen.findByRole("link", { name: "Review and activate a resume" })).toHaveAttribute("href", "/resume-profile");
  expect(screen.getByText("Python Engineer")).toBeInTheDocument();
  expect(screen.getByLabelText("Minimum match score")).toBeDisabled();
  expect(screen.getByRole("option", { name: "Best match" })).toBeDisabled();
});

test("job details explain weights, component scores, and eligibility evidence", async () => {
  mockApi();
  renderPage("/jobs/1");
  expect(await screen.findByText("Why this score?")).toBeInTheDocument();
  expect(screen.getByText(/50\/100 · weight 60.0%/)).toBeInTheDocument();
  expect(screen.getByText(/80\/100 · weight 40.0%/)).toBeInTheDocument();
  expect(screen.getByText("Total years is not explicitly saved.")).toBeInTheDocument();
  expect(screen.getByText("Job requirement: 2 years")).toBeInTheDocument();
});
