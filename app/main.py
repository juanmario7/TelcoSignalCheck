from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os, csv, io
from dotenv import load_dotenv

load_dotenv()

from .database import init_db, save_report, get_all_reports, get_stats
from .geocoding import geocode

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

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
        html = f.read().replace("{{PHONE}}", phone).replace("{{GOOGLE_MAPS_API_KEY}}", GOOGLE_MAPS_API_KEY)
    return HTMLResponse(html)


class ReportPayload(BaseModel):
    phone: str
    problem_type: str
    frequency: str
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
        if lat is None or lng is None:
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
        problem_type=payload.problem_type,
        frequency=payload.frequency,
        address=address,
        lat=lat,
        lng=lng,
        location_method=payload.location_method,
        description=payload.description,
    )
    return {"ok": True, "lat": lat, "lng": lng}


@app.post("/api/no-problem")
def no_problem(payload: dict):
    """Registra usuarios que respondieron que no tienen problemas."""
    return {"ok": True}


# ── Dashboard API ─────────────────────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open(os.path.join(FRONTEND_DIR, "dashboard.html"), encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/api/reports")
def reports(date_from: str = Query(None), date_to: str = Query(None)):
    return JSONResponse(get_all_reports(date_from, date_to))


@app.get("/api/stats")
def stats(date_from: str = Query(None), date_to: str = Query(None)):
    return JSONResponse(get_stats(date_from, date_to))


@app.get("/api/reports/export")
def export_reports(date_from: str = Query(None), date_to: str = Query(None)):
    rows = get_all_reports(date_from, date_to)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "phone", "problem_type", "frequency", "address", "lat", "lng", "location_method", "description", "created_at"])
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    filename = "reportes_senal"
    if date_from:
        filename += f"_{date_from}"
    if date_to:
        filename += f"_a_{date_to}"
    filename += ".csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
