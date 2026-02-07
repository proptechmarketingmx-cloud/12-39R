"""Aplicacion FastAPI."""
from __future__ import annotations

from fastapi import FastAPI

from app.routers.properties import router as properties_router

app = FastAPI(title="CRM Inmobiliario API", version="0.1.0")


@app.get("/health")
def health():
	return {"status": "ok"}


app.include_router(properties_router)
