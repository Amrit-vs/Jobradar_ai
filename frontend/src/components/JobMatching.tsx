import { NavLink } from "react-router-dom";
import type { Job, MatchingContext } from "../types/api";

export function MatchingNotice({ context, isError }: { context?: MatchingContext; isError?: boolean }) {
  if (isError) return <p className="error">Could not load matching status. You can still browse jobs.</p>;
  if (!context?.status) return null;
  if (context.status === "ready") return <p className="matching-notice">Matching against {context.filename}. Scores use saved profile fields and do not determine eligibility.</p>;
  return <div className="matching-notice" role="status"><p>{context.explanation}</p><NavLink to="/resume-profile">Review and activate a resume</NavLink></div>;
}

export function JobMatching({ job, detailed = false }: { job: Job; detailed?: boolean }) {
  const match = job.matching;
  if (!match || (match.score === null && !detailed)) return <p className="match-unavailable">Match unavailable</p>;
  return <div className="job-matching">
    <strong className="match-score">{match.score === null ? "Match unavailable" : `Match: ${match.score}/100`}</strong>
    <p>Eligibility: <span className={`eligibility ${match.eligibility.status}`}>{match.eligibility.status}</span></p>
    <p><strong>Matched skills:</strong> {match.matched_skills.join(", ") || "None identified"}</p>
    <p><strong>Missing skills:</strong> {match.missing_skills.join(", ") || "None identified"}</p>
    {detailed && <>
      <h2>Why this score?</h2>
      <p>{match.explanation}</p>
      <dl className="match-components">
        <dt>Skill coverage</dt><dd>{match.components.skill_overlap === null ? "Unavailable" : `${match.components.skill_overlap}/100`} · weight {(match.weights.skill_overlap * 100).toFixed(1)}%</dd>
        <dt>Text similarity (TF-IDF cosine)</dt><dd>{match.components.text_similarity === null ? "Unavailable" : `${match.components.text_similarity}/100`} · weight {(match.weights.text_similarity * 100).toFixed(1)}%</dd>
      </dl>
      <h2>Eligibility checks</h2>
      <p>These checks cover recognized explicit requirements only. Unknown means more information or manual review is needed. Missing skills are job mentions, not inferred eligibility rules.</p>
      <ul className="eligibility-checks">{match.eligibility.checks.map((check) => <li key={check.criterion}>
        <strong>{check.criterion.replaceAll("_", " ")}: {check.status}</strong>
        {check.requirement && <p>Job requirement: {check.requirement}</p>}
        {check.candidate_value !== null && <p>Saved qualification: {check.candidate_value}</p>}
        <p>{check.reason}</p>
      </li>)}</ul>
    </>}
  </div>;
}
