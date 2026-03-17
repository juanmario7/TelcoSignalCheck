from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

from .database import init_db, save_report, get_all_reports, get_stats
from .geocoding import geocode

app = FastAPI(title="TelcoSignalCheck")

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.on_event("startup")
def startup():
    init_db()


# ── Formulario del usuario ────────────────────────────────────────────────────

@app.get("/form", response_class=HTMLResponse)
def form(phone: str = Query(..., description="Número del usuario")):
    with open(os.path.join(FRONTEND_DIR, "form.html"), encoding="utf-8") as f:
        html = f.read().replace("{{PHONE}}", phone)
    return HTMLResponse(html)


class ReportPayload(BaseModel):
    phone: str
    location_method: str          # "gps" | "address"
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    description: str | None = None


@app.post("/api/report")
def submit_report(payload: ReportPayload):
    lat, lng, address = payload.lat, payload.lng, payload.address

    if payload.location_method == "address":
        if not payload.address:
            raise HTTPException(400, "Se requiere dirección")
        result = geocode(payload.address)
        if not result:
            raise HTTPException(422, "No se pudo geocodificar la dirección. Intenta ser más específico.")
        lat, lng, address = result["lat"], result["lng"], result["display_name"]

    elif payload.location_method == "gps":
        if lat is None or lng is None:
            raise HTTPException(400, "Se requieren coordenadas GPS")

    else:
        raise HTTPException(400, "location_method inválido")

    save_report(
        phone=payload.phone,
        address=address,
        lat=lat,
        lng=lng,
        location_method=payload.location_method,
        description=payload.description,
    )
    return {"ok": True, "lat": lat, "lng": lng}


# ── Dashboard API ─────────────────────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open(os.path.join(FRONTEND_DIR, "dashboard.html"), encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/api/reports")
def reports():
    return JSONResponse(get_all_reports())


@app.get("/api/stats")
def stats():
    return JSONResponse(get_stats())
