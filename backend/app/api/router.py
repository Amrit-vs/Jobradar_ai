from fastapi import APIRouter

from app.api.routes import collection, companies, health, jobs, matching, resume

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(companies.router)
api_router.include_router(jobs.router)
api_router.include_router(collection.router)
api_router.include_router(resume.router)
api_router.include_router(matching.router)
