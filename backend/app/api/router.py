from fastapi import APIRouter

from app.api.routes import analytics, audit, auth, doctors, leaves, notifications, roster

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["Doctor Management"])
api_router.include_router(leaves.router, prefix="/leaves", tags=["Leave Management"])
api_router.include_router(roster.router, prefix="/roster", tags=["Roster"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
