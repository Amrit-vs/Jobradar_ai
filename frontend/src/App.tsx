import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { NavLink, Route, Routes, useParams } from "react-router-dom";
import { api } from "./services/api";
import { JobMatching, MatchingNotice } from "./components/JobMatching";
import type { Job, ParsedResume, Resume } from "./types/api";

const pages = ["Dashboard", "Jobs", "Companies", "Resume & Profile", "Preferences", "Alerts", "Settings"];

function PlaceholderPage({ title }: { title: string }) {
  return <section><h1>{title}</h1><p>This Phase 1 page is ready for its feature implementation.</p></section>;
}

function CollectionButton() { const client = useQueryClient(); const mutation = useMutation({ mutationFn: api.collect, onSuccess: () => { void client.invalidateQueries(); } }); return <div className="collection"><button onClick={() => mutation.mutate()} disabled={mutation.isPending}>{mutation.isPending ? "Collecting…" : "Run Job Collection"}</button>{mutation.data && <p>Completed: {mutation.data.jobs_fetched} fetched · {mutation.data.jobs_added} added · {mutation.data.duplicates} duplicates · {mutation.data.errors} errors</p>}{mutation.isError && <p className="error">Collection could not be completed.</p>}</div>; }
function JobCard({ job }: { job: Job }) {
  return <article className="card"><div>
    <p className="eyebrow">{job.company} · {job.source}</p><h2>{job.title}</h2>
    <p>{job.location ?? "Location not listed"} · {job.experience_level ?? "Level not listed"}</p>
    <JobMatching job={job} />
  </div><div className="status"><strong>{job.freshness}</strong><NavLink to={`/jobs/${job.id}`}>View job</NavLink></div></article>;
}
function JobList() {
  const context = useQuery({ queryKey: ["matching-context"], queryFn: api.matchingContext });
  const canMatch = context.data?.status === "ready";
  const [sort, setSort] = useState<"posted_at" | "match_score">("posted_at");
  const [minimum, setMinimum] = useState("");
  const validMinimum = minimum === "" || (Number.isFinite(Number(minimum)) && Number(minimum) >= 0 && Number(minimum) <= 100);
  const filters = { sort_by: canMatch ? sort : "posted_at" as const, min_match_score: canMatch && minimum !== "" && validMinimum ? Number(minimum) : undefined };
  const { data: jobs = [], isLoading, isError } = useQuery({ queryKey: ["jobs", filters, context.data?.resume_id], queryFn: () => api.jobs(filters), placeholderData: (previous) => previous });
  const [search, setSearch] = useState("");
  const [company, setCompany] = useState("");
  const [freshness, setFreshness] = useState("");
  const companies = useQuery({ queryKey: ["companies"], queryFn: api.companies });
  const companyNames = [...new Set([...(companies.data ?? []).map((item) => item.name), ...jobs.map((job) => job.company)].filter(Boolean))].sort();
  const displayed = jobs.filter((job) => `${job.company} ${job.title} ${job.location ?? ""} ${job.experience_level ?? ""}`.toLowerCase().includes(search.toLowerCase()) && (!company || job.company === company) && (!freshness || job.freshness === freshness));
  const filtered = !!(search || company || freshness || filters.min_match_score !== undefined);
  if (isLoading) return <p>Loading jobs…</p>;
  if (isError) return <p className="error">Unable to load jobs. Run a collection after starting the API.</p>;
  return <section>
    <div className="page-heading"><div><h1>Jobs</h1><p>Mock jobs ranked against your saved, active resume.</p></div><CollectionButton /></div>
    <MatchingNotice context={context.data} isError={context.isError} />
    <div className="filters">
      <input aria-label="Filter jobs" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Role, location, or experience" />
      <select aria-label="Filter company" value={company} onChange={(event) => setCompany(event.target.value)}><option value="">All companies</option>{companyNames.map((name) => <option key={name}>{name}</option>)}</select>
      <select aria-label="Filter freshness" value={freshness} onChange={(event) => setFreshness(event.target.value)}><option value="">All freshness</option>{["FRESH", "ACTIVE", "URGENT", "OLDER"].map((value) => <option key={value}>{value}</option>)}</select>
      <label>Sort jobs<select aria-label="Sort jobs" value={canMatch ? sort : "posted_at"} onChange={(event) => setSort(event.target.value as "posted_at" | "match_score")}><option value="posted_at">Newest first</option><option value="match_score" disabled={!canMatch}>Best match</option></select></label>
      <label>Minimum match score<input aria-label="Minimum match score" type="number" min="0" max="100" step="1" placeholder="Any score" disabled={!canMatch} value={canMatch ? minimum : ""} onChange={(event) => setMinimum(event.target.value)} /></label>
    </div>
    {!validMinimum && canMatch && <p className="error">Minimum score must be between 0 and 100.</p>}
    {displayed.length === 0 ? <p>{filtered ? "No jobs match these filters. Try lowering the minimum score or clearing filters." : "No jobs yet. Run Job Collection to load the five mock sources."}</p> : <div className="job-list">{displayed.map((job) => <JobCard job={job} key={job.id} />)}</div>}
  </section>;
}
function JobDetails() {
  const { jobId = "" } = useParams();
  const { data: job, isLoading } = useQuery({ queryKey: ["job", jobId], queryFn: () => api.job(jobId) });
  const context = useQuery({ queryKey: ["matching-context"], queryFn: api.matchingContext });
  if (isLoading) return <p>Loading job…</p>;
  if (!job) return <p className="error">Job was not found.</p>;
  return <section><NavLink to="/jobs">← Back to jobs</NavLink><p className="eyebrow">{job.company} · {job.freshness} · {job.source}</p>
    <h1>{job.title}</h1><p>{job.location} · {job.experience_level} · {job.employment_type}</p>
    <p>Posted: {job.posted_at ? new Date(job.posted_at).toLocaleDateString() : "Unknown"}</p>
    <MatchingNotice context={context.data} isError={context.isError} />
    <JobMatching job={job} detailed />
    <p className="description">{job.description}</p><a className="apply" href={job.url} target="_blank" rel="noreferrer">Apply now</a>
  </section>;
}
function Companies() { const { data: companies = [], isLoading } = useQuery({ queryKey: ["companies"], queryFn: api.companies }); return <section><div className="page-heading"><div><h1>Companies</h1><p>Collection status is stored by the backend.</p></div><CollectionButton /></div>{isLoading ? <p>Loading companies…</p> : companies.length === 0 ? <p>No companies are registered yet. Run a mock collection to initialize them.</p> : <div className="company-table">{companies.map((company) => <article key={company.id}><strong>{company.name}</strong><span>{company.enabled ? "Enabled" : "Disabled"}</span><span>{company.last_collection_status ?? "Not collected"}</span><span>{company.job_count} jobs</span></article>)}</div>}</section>; }
function ResumePage() {
  const client = useQueryClient();
  const { data: resumes = [], isLoading } = useQuery({ queryKey: ["resumes"], queryFn: api.resumes });
  const [selected, setSelected] = useState<Resume | null>(null);
  const [error, setError] = useState("");
  const refresh = () => {
    void client.invalidateQueries({ queryKey: ["resumes"] });
    void client.invalidateQueries({ queryKey: ["matching-context"] });
    void client.invalidateQueries({ queryKey: ["jobs"] });
    void client.invalidateQueries({ queryKey: ["job"] });
  };
  const upload = useMutation({
    mutationFn: api.uploadResume,
    onSuccess: (resume) => { setSelected(resume); refresh(); },
    onError: () => { setError("Upload or parsing failed. Please use a valid text-based PDF or DOCX."); refresh(); }
  });
  const save = useMutation({
    mutationFn: ({ id, data }: { id: number; data: ParsedResume }) => api.updateResumeProfile(id, data),
    onSuccess: (resume) => { setSelected((current) => current?.id === resume.id ? resume : current); refresh(); },
    onError: () => setError("Could not save profile changes. Please try again.")
  });
  const activate = useMutation({
    mutationFn: api.activateResume,
    onSuccess: (resume) => {
      setSelected((current) => current ? { ...current, is_active: current.id === resume.id } : null);
      refresh();
    },
    onError: () => setError("Could not activate this resume. Please try again.")
  });
  const remove = useMutation({
    mutationFn: api.deleteResume,
    onSuccess: (_, id) => { setSelected((current) => current?.id === id ? null : current); refresh(); },
    onError: () => setError("Could not delete this resume. Please try again.")
  });
  const choose = async (resume: Resume) => {
    setError("");
    try { setSelected(await api.resume(resume.id)); }
    catch { setError("Could not load this resume."); }
  };
  const parsed = selected?.parsed_data;
  return <section>
    <h1>Resume &amp; Profile</h1>
    <p>Upload a text-based PDF or DOCX resume. The server validates the configured size limit. Parsing is rule-based. Review and save corrections before setting a resume as active for matching.</p>
    <label className="upload">
      <input aria-label="Upload resume" type="file" accept=".pdf,.docx" disabled={upload.isPending} onChange={(event) => {
        const file = event.target.files?.[0];
        if (file) { setError(""); upload.mutate(file); }
        event.target.value = "";
      }} />
      {upload.isPending ? "Analyzing your resume…" : "Upload your resume"}
    </label>
    {error && <p className="error">{error}</p>}
    {isLoading ? <p>Loading resumes…</p> : <div className="resume-list">{resumes.map((resume) =>
      <button className="resume-item" key={resume.id} onClick={() => void choose(resume)}>
        {resume.filename} · {resume.parsing_status} {resume.is_active ? "· Active" : ""}
      </button>
    )}</div>}
    {selected && (parsed ? <ResumeEditor key={selected.id} resume={selected} data={parsed}
      onSave={(data) => save.mutate({ id: selected.id, data })}
      onActivate={() => activate.mutate(selected.id)}
      onDelete={() => remove.mutate(selected.id)} /> :
      <div className="resume-editor">
        <h2>{selected.filename}</h2>
        <p className="error">{selected.parsing_error ?? "Parsed data is not available for this resume."}</p>
        <button className="danger" disabled={remove.isPending} onClick={() => remove.mutate(selected.id)}>Delete Resume</button>
      </div>)}
  </section>;
}
function ResumeEditor({ resume, data, onSave, onActivate, onDelete }: { resume: Resume; data: ParsedResume; onSave: (data: ParsedResume) => void; onActivate: () => void; onDelete: () => void }) { const [draft, setDraft] = useState(data); const field = (key: keyof ParsedResume, label: string) => <label>{label}<input value={(draft[key] as string | null) ?? ""} onChange={(event) => setDraft({ ...draft, [key]: event.target.value })} /></label>; return <div className="resume-editor"><h2>{resume.filename}</h2><p>{resume.is_active ? "Active resume" : "Inactive resume"} · parsed {resume.parsing_status}</p><div className="profile-grid">{field("full_name", "Name")}{field("email", "Email")}{field("phone", "Phone")}{field("location", "Location")}{field("linkedin_url", "LinkedIn")}{field("github_url", "GitHub")}</div><label>Total years of experience (only if known)<input aria-label="Total years of experience" type="number" min="0" max="100" step="0.1" value={draft.years_of_experience ?? ""} onChange={(event) => setDraft({ ...draft, years_of_experience: event.target.value === "" ? null : Number(event.target.value) })} /></label><label>Skills (comma separated)<textarea value={draft.skills.join(", ")} onChange={(event) => setDraft({ ...draft, skills: event.target.value.split(",").map((s) => s.trim()).filter(Boolean) })} /></label><section className="structured"><h3>Education</h3>{draft.education.map((item, index) => <div className="entry" key={index}><input aria-label="Education institution" value={item.institution ?? ""} placeholder="Institution" onChange={(event) => setDraft({ ...draft, education: draft.education.map((entry, i) => i === index ? { ...entry, institution: event.target.value } : entry) })} /><input value={item.degree ?? ""} placeholder="Degree" onChange={(event) => setDraft({ ...draft, education: draft.education.map((entry, i) => i === index ? { ...entry, degree: event.target.value } : entry) })} /><input value={item.graduation_year ?? ""} placeholder="Graduation year" onChange={(event) => setDraft({ ...draft, education: draft.education.map((entry, i) => i === index ? { ...entry, graduation_year: event.target.value } : entry) })} /><label>Academic percentage (optional)<input aria-label="Academic percentage" type="number" min="0" max="100" step="0.1" value={item.percentage ?? ""} placeholder="Unknown" onChange={(event) => setDraft({ ...draft, education: draft.education.map((entry, i) => i === index ? { ...entry, percentage: event.target.value === "" ? null : Number(event.target.value) } : entry) })} /></label><button className="secondary" onClick={() => setDraft({ ...draft, education: draft.education.filter((_, i) => i !== index) })}>Remove</button></div>)}<button className="secondary" onClick={() => setDraft({ ...draft, education: [...draft.education, { institution: null, degree: null, field_of_study: null, start_date: null, end_date: null, graduation_year: null, cgpa: null }] })}>Add Education</button></section><section className="structured"><h3>Experience &amp; Internships</h3>{draft.experience.map((item, index) => <div className="entry" key={index}><input aria-label="Experience role" value={item.role ?? ""} placeholder="Role" onChange={(event) => setDraft({ ...draft, experience: draft.experience.map((entry, i) => i === index ? { ...entry, role: event.target.value } : entry) })} /><input value={item.company ?? ""} placeholder="Organization" onChange={(event) => setDraft({ ...draft, experience: draft.experience.map((entry, i) => i === index ? { ...entry, company: event.target.value } : entry) })} /><textarea value={item.description ?? ""} placeholder="Description" onChange={(event) => setDraft({ ...draft, experience: draft.experience.map((entry, i) => i === index ? { ...entry, description: event.target.value } : entry) })} /><button className="secondary" onClick={() => setDraft({ ...draft, experience: draft.experience.filter((_, i) => i !== index) })}>Remove</button></div>)}<button className="secondary" onClick={() => setDraft({ ...draft, experience: [...draft.experience, { company: null, role: null, start_date: null, end_date: null, description: null }] })}>Add Experience</button></section><section className="structured"><h3>Projects</h3>{draft.projects.map((item, index) => <div className="entry" key={index}><input aria-label="Project name" value={item.name ?? ""} placeholder="Project title" onChange={(event) => setDraft({ ...draft, projects: draft.projects.map((entry, i) => i === index ? { ...entry, name: event.target.value } : entry) })} /><input value={item.technologies.join(", ")} placeholder="Technologies" onChange={(event) => setDraft({ ...draft, projects: draft.projects.map((entry, i) => i === index ? { ...entry, technologies: event.target.value.split(",").map((value) => value.trim()).filter(Boolean) } : entry) })} /><textarea value={item.description ?? ""} placeholder="Description" onChange={(event) => setDraft({ ...draft, projects: draft.projects.map((entry, i) => i === index ? { ...entry, description: event.target.value } : entry) })} /><button className="secondary" onClick={() => setDraft({ ...draft, projects: draft.projects.filter((_, i) => i !== index) })}>Remove</button></div>)}<button className="secondary" onClick={() => setDraft({ ...draft, projects: [...draft.projects, { name: null, organization: null, start_date: null, end_date: null, description: null, technologies: [] }] })}>Add Project</button></section><section className="structured"><h3>Certifications</h3><textarea aria-label="Certifications" value={draft.certifications.join("\n")} onChange={(event) => setDraft({ ...draft, certifications: event.target.value.split("\n").map((value) => value.trim()).filter(Boolean) })} /></section><div className="actions"><button onClick={() => onSave(draft)}>Save Changes</button><button onClick={onActivate}>Set as Active</button><button className="danger" onClick={onDelete}>Delete Resume</button></div></div>; }

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
          <Route path="/resume-profile" element={<ResumePage />} />
          <Route path="*" element={<PlaceholderPage title="JobRadar AI" />} />
        </Routes>
      </main>
    </div>
  );
}
