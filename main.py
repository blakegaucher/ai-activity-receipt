"""Bounded read-only Vercel pilot for AI Activity Receipt.

This adapter intentionally exposes only non-sensitive project metadata.
It does not execute AI agents, accept receipt uploads, mutate records,
or claim production/commercial validation.
"""
from fastapi import FastAPI

app = FastAPI(
    title="AI Activity Receipt — Read-only Pilot",
    description="Pre-commercial research demonstration. Synthetic/technical evidence only.",
    version="0.1.0",
)

@app.get("/")
def home():
    return {
        "project": "AI Activity Receipt",
        "mode": "read-only deployment pilot",
        "status": "pre-commercial research and development",
        "evidence_boundary": "synthetic/technical evidence; no claim of proven productivity, safety, legal compliance, standards conformance, or commercial advantage",
        "mutations_enabled": False,
        "external_ai_calls_enabled": False,
    }

@app.get("/health")
def health():
    return {"status": "ok", "mode": "read-only"}
