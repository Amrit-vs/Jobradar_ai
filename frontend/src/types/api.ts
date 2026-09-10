export type Job = { id: number; company: string; company_slug: string; title: string; description: string; location: string | null; url: string; posted_at: string | null; employment_type: string | null; experience_level: string | null; source: string; status: string; freshness: string };
export type Company = { id: number; name: string; enabled: boolean; job_count: number; last_collection_status: string | null; last_collection_at: string | null };
export type CollectionStats = { companies_processed: number; jobs_fetched: number; jobs_added: number; jobs_updated: number; duplicates: number; errors: number };

