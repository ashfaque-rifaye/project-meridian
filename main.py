"""Vercel entrypoint for the Meridian FastAPI application."""

from apps.api.main import app

__all__ = ["app"]
