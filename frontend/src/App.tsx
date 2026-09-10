import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { NavLink, Route, Routes, useParams } from "react-router-dom";
import { api } from "./services/api";
import type { Job } from "./types/api";

const pages = ["Dashboard", "Jobs", "Companies", "Resume & Profile", "Preferences", "Alerts", "Settings"];

function PlaceholderPage({ title }: { title: string }) {
  return <section><h1>{title}</h1><p>This Phase 1 page is ready for its feature implementation.</p></section>;
}

function CollectionButton() { const client = useQueryClient(); const mutation = useMutation({ mutationFn: api.collect, onSuccess: () => { void client.invalidateQueries(); } }); return <div className="collection"><button onClick={() => mutation.mutate()} disabled={mutation.isPending}>{mutation.isPending ? "Collecting…" : "Run Job Collection"}</button>{mutation.data && <p>Completed: {mutation.data.jobs_fetched} fetched · {mutation.data.jobs_added} added · {mutation.data.duplicates} duplicates · {mutation.data.errors} errors</p>}{mutation.isError && <p className="error">Collection could not be completed.</p>}</div>; }
function JobCard({ job }: { job: Job }) { return <article className="card"><div><p className="eyebrow">{job.company} · {job.source}</p><h2>{job.title}</h2><p>{job.location ?? "Location not listed"} · {job.experience_level ?? "Level not listed"}</p></div><div className="status"><strong>{job.freshness}</strong><NavLink to={`/jobs/${job.id}`}>View job</NavLink></div></article>; }
function JobList() { const { data: jobs = [], isLoading, isError } = useQuery({ queryKey: ["jobs"], queryFn: api.jobs }); const [search, setSearch] = useState(""); const [company, setCompany] = useState(""); const [freshness, setFreshness] = useState(""); const displayed = jobs.filter((job) => `${job.company} ${job.title} ${job.location ?? ""} ${job.experience_level ?? ""}`.toLowerCase().includes(search.toLowerCase()) && (!company || job.company === company) && (!freshness || job.freshness === freshness)); if (isLoading) return <p>Loading jobs…</p>; if (isError) return <p className="error">Unable to load jobs. Run a collection after starting the API.</p>; return <section><div className="page-heading"><div><h1>Jobs</h1><p>Mock job data from the ingestion pipeline.</p></div><CollectionButton /></div><div className="filters"><input aria-label="Filter jobs" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Role, location, or experience" /><select aria-label="Filter company" value={company} onChange={(event) => setCompany(event.target.value)}><option value="">All companies</option>{[...new Set(jobs.map((job) => job.company))].map((name) => <option key={name}>{name}</option>)}</select><select aria-label="Filter freshness" value={freshness} onChange={(event) => setFreshness(event.target.value)}><option value="">All freshness</option>{["FRESH", "ACTIVE", "URGENT", "OLDER"].map((value) => <option key={value}>{value}</option>)}</select></div>{displayed.length === 0 ? <p>No jobs yet. Run Job Collection to load the five mock sources.</p> : <div className="job-list">{displayed.map((job) => <JobCard job={job} key={job.id} />)}</div>}</section>; }
function JobDetails() { const { jobId = "" } = useParams(); const { data: job, isLoading } = useQuery({ queryKey: ["job", jobId], queryFn: () => api.job(jobId) }); if (isLoading) return <p>Loading job…</p>; if (!job) return <p className="error">Job was not found.</p>; return <section><NavLink to="/jobs">← Back to jobs</NavLink><p className="eyebrow">{job.company} · {job.freshness} · {job.source}</p><h1>{job.title}</h1><p>{job.location} · {job.experience_level} · {job.employment_type}</p><p>Posted: {job.posted_at ? new Date(job.posted_at).toLocaleDateString() : "Unknown"}</p><p className="description">{job.description}</p><a className="apply" href={job.url} target="_blank" rel="noreferrer">Apply now</a></section>; }
function Companies() { const { data: companies = [], isLoading } = useQuery({ queryKey: ["companies"], queryFn: api.companies }); return <section><div className="page-heading"><div><h1>Companies</h1><p>Collection status is stored by the backend.</p></div><CollectionButton /></div>{isLoading ? <p>Loading companies…</p> : companies.length === 0 ? <p>No companies are registered yet. Run a mock collection to initialize them.</p> : <div className="company-table">{companies.map((company) => <article key={company.id}><strong>{company.name}</strong><span>{company.enabled ? "Enabled" : "Disabled"}</span><span>{company.last_collection_status ?? "Not collected"}</span><span>{company.job_count} jobs</span></article>)}</div>}</section>; }

export function App() {
  return (
    <div className="app-shell">
      <aside>
        <p className="brand">JobRadar <span>AI</span></p>
        <nav>{pages.map((page) => <NavLink key={page} to={page === "Dashboard" ? "/" : `/${page.toLowerCase().replaceAll(" & ", "-").replaceAll(" ", "-")}`}>{page}</NavLink>)}</nav>
      </aside>
      <main>
        <Routes>
          <Route path="/" element={<JobList />} />
          <Route path="/jobs" element={<JobList />} />
          <Route path="/jobs/:jobId" element={<JobDetails />} />
          <Route path="/companies" element={<Companies />} />
          <Route path="*" element={<PlaceholderPage title="JobRadar AI" />} />
        </Routes>
      </main>
    </div>
  );
}
