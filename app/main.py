from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Pocket Mechanic API", version="0.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

Category = Literal["automotive", "motorcycle", "appliance", "home", "equipment", "diy"]


class DiagnosisRequest(BaseModel):
    category: Category
    symptom: str = Field(min_length=5, max_length=2000)
    answers: dict[str, Any] = Field(default_factory=dict)
    profile_id: str | None = None


class Cause(BaseModel):
    title: str
    confidence: float = Field(ge=0, le=1)
    why: str
    checks: list[str]
    repair: list[str]
    safety: Literal["low", "medium", "high", "stop"]


class DiagnosisResponse(BaseModel):
    id: str
    created_at: str
    category: Category
    symptom: str
    summary: str
    safety_message: str
    causes: list[Cause]


class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: Category
    make: str | None = None
    model: str | None = None
    year: int | None = Field(default=None, ge=1900, le=2100)
    engine: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=2000)


PROFILES: dict[str, dict[str, Any]] = {}
DIAGNOSES: dict[str, DiagnosisResponse] = {}

RULES = [
    {
        "category": "automotive",
        "needles": ["speedometer", "odometer", "cruise"],
        "cause": Cause(
            title="Vehicle speed signal loss",
            confidence=0.93,
            why="The speedometer, odometer, and cruise control share the vehicle-speed signal. A combined failure points toward the sensor, wiring, connector, or signal path.",
            checks=[
                "Scan live data for vehicle speed while the vehicle is moved safely.",
                "Inspect the vehicle-speed sensor and connector for damage or corrosion.",
                "Test sensor power, ground, and signal using the correct wiring diagram.",
                "Inspect related fuses and grounds before replacing the instrument cluster.",
            ],
            repair=[
                "Repair damaged wiring or connector terminals.",
                "Replace the sensor only after confirming circuit and live-data failure.",
                "Re-test the speedometer, odometer, cruise control, and shifting.",
            ],
            safety="medium",
        ),
    },
    {
        "category": "automotive",
        "needles": ["belt", "shred"],
        "cause": Cause(
            title="Pulley misalignment or bearing failure",
            confidence=0.88,
            why="A belt shredding along one edge commonly tracks off-center because of pulley misalignment, tensioner wear, bracket damage, or bearing play.",
            checks=[
                "Remove the belt and spin every pulley by hand.",
                "Check tensioner-arm alignment and smooth movement.",
                "Use a straightedge across pulley faces.",
                "Inspect the crank pulley and accessory brackets for wobble.",
            ],
            repair=[
                "Replace the failed pulley, tensioner, bearing, or damaged bracket.",
                "Install the correct belt and verify routing.",
                "Run briefly while observing belt tracking from a safe position.",
            ],
            safety="high",
        ),
    },
    {
        "category": "appliance",
        "needles": ["dryer", "hc"],
        "cause": Cause(
            title="Dryer temperature-sensing fault",
            confidence=0.87,
            why="An HC-style dryer error often involves the thermistor circuit, restricted airflow, a grounded heater, or abnormal temperature interpretation.",
            checks=[
                "Disconnect power before opening the dryer.",
                "Measure thermistor resistance at room temperature.",
                "Check thermistor wiring for opens, shorts, and loose terminals.",
                "Test the heating element for continuity to the metal housing.",
                "Clean the entire exhaust path and verify airflow.",
            ],
            repair=[
                "Replace a failed thermistor or damaged harness.",
                "Replace a grounded heating element.",
                "Restore airflow before operating the dryer.",
            ],
            safety="high",
        ),
    },
    {
        "category": "equipment",
        "needles": ["no start"],
        "cause": Cause(
            title="Fuel, spark, or compression fault",
            confidence=0.78,
            why="Small-engine no-start problems are isolated by checking fresh fuel delivery, ignition spark, and compression in that order.",
            checks=[
                "Verify fresh fuel and the correct fuel mixture.",
                "Inspect and test the spark plug.",
                "Check air-filter and choke operation.",
                "Confirm fuel reaches the carburetor.",
                "Perform a compression test if fuel and spark are present.",
            ],
            repair=[
                "Replace a fouled plug and stale fuel.",
                "Clean or rebuild the carburetor if fuel delivery is restricted.",
                "Repair ignition or internal compression faults based on test results.",
            ],
            safety="medium",
        ),
    },
    {
        "category": "home",
        "needles": ["sparking", "outlet"],
        "cause": Cause(
            title="Electrical arcing hazard",
            confidence=0.95,
            why="Visible sparking, heat, burning odor, or discoloration can indicate a loose or damaged electrical connection and create fire or shock risk.",
            checks=[
                "Turn off the circuit at the breaker if safe.",
                "Do not touch exposed conductors.",
                "Check for heat, smoke, or active fire from a safe distance.",
                "Have a qualified electrician inspect the circuit and device.",
            ],
            repair=["Do not energize the circuit until damaged wiring or equipment is repaired and tested."],
            safety="stop",
        ),
    },
]

FALLBACK_CAUSES = {
    "automotive": "Systematic vehicle diagnosis needed",
    "motorcycle": "Systematic motorcycle diagnosis needed",
    "appliance": "Systematic appliance diagnosis needed",
    "home": "Systematic home-system diagnosis needed",
    "equipment": "Systematic equipment diagnosis needed",
    "diy": "Project assessment needed",
}

OBD_CODES = {
    "P0300": {"title": "Random/multiple-cylinder misfire", "system": "Powertrain", "first_checks": ["Read freeze-frame data", "Inspect plugs and coils", "Check for vacuum leaks", "Verify fuel pressure"]},
    "P0171": {"title": "System too lean — Bank 1", "system": "Fuel control", "first_checks": ["Inspect intake leaks", "Check MAF readings", "Verify fuel pressure", "Inspect exhaust leaks before the upstream sensor"]},
    "P0420": {"title": "Catalyst efficiency below threshold — Bank 1", "system": "Emissions", "first_checks": ["Repair active misfires first", "Check exhaust leaks", "Compare upstream/downstream O2 activity", "Confirm catalyst temperature and operation"]},
    "P0456": {"title": "EVAP system very small leak", "system": "Evaporative emissions", "first_checks": ["Inspect fuel cap and seal", "Inspect EVAP hoses", "Test purge and vent valves", "Smoke-test the system"]},
    "U0100": {"title": "Lost communication with ECM/PCM", "system": "Network", "first_checks": ["Check battery voltage", "Inspect ECM power and grounds", "Check CAN wiring resistance", "Inspect connectors for water or corrosion"]},
}


def diagnose(req: DiagnosisRequest) -> DiagnosisResponse:
    text = f"{req.symptom} {' '.join(map(str, req.answers.values()))}".lower()
    matches: list[Cause] = []
    for rule in RULES:
        if rule["category"] == req.category and all(word in text for word in rule["needles"]):
            matches.append(rule["cause"])

    if not matches:
        matches = [Cause(
            title=FALLBACK_CAUSES[req.category],
            confidence=0.52,
            why="The symptom does not match a verified local rule yet, so Pocket Mechanic is collecting evidence instead of guessing.",
            checks=[
                "Record the exact model, year, engine, and identification number.",
                "Describe when the problem started and what changed beforehand.",
                "Capture fault codes, sounds, smells, leaks, temperatures, and warning lights.",
                "Check power, grounds, connectors, fluids, and visible damage.",
                "Stop for fire, fuel leakage, exposed electricity, unstable lifting, or rotating-equipment danger.",
            ],
            repair=["Complete the checks, then enter the new evidence for a narrower diagnosis."],
            safety="medium",
        )]

    top_safety = matches[0].safety
    safety_message = {
        "low": "Normal precautions apply.",
        "medium": "Use appropriate PPE and disable power before disassembly.",
        "high": "Do not operate until the fault is inspected. Disconnect power or disable the machine before service.",
        "stop": "STOP WORK. Leave the area safe and contact a qualified professional or emergency services when appropriate.",
    }[top_safety]

    return DiagnosisResponse(
        id=str(uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        category=req.category,
        symptom=req.symptom,
        summary=f"Pocket Mechanic found {len(matches)} likely diagnostic path{'s' if len(matches) != 1 else ''}.",
        safety_message=safety_message,
        causes=matches,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.4.0"}


@app.post("/api/diagnoses", response_model=DiagnosisResponse, status_code=201)
def create_diagnosis(req: DiagnosisRequest) -> DiagnosisResponse:
    result = diagnose(req)
    DIAGNOSES[result.id] = result
    return result


@app.get("/api/diagnoses")
def list_diagnoses() -> list[DiagnosisResponse]:
    return list(reversed(list(DIAGNOSES.values())))


@app.get("/api/diagnoses/{diagnosis_id}", response_model=DiagnosisResponse)
def get_diagnosis(diagnosis_id: str) -> DiagnosisResponse:
    result = DIAGNOSES.get(diagnosis_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return result


@app.post("/api/profiles", status_code=201)
def create_profile(profile: ProfileCreate) -> dict[str, Any]:
    profile_id = str(uuid4())
    data = profile.dict() if hasattr(profile, "dict") else profile.model_dump()
    record = {"id": profile_id, **data, "created_at": datetime.now(timezone.utc).isoformat()}
    PROFILES[profile_id] = record
    return record


@app.get("/api/profiles")
def list_profiles() -> list[dict[str, Any]]:
    return list(PROFILES.values())


@app.get("/api/obd/{code}")
def obd_lookup(code: str) -> dict[str, Any]:
    normalized = code.strip().upper()
    result = OBD_CODES.get(normalized)
    if result is None:
        raise HTTPException(status_code=404, detail="Code is not in the offline starter library")
    return {"code": normalized, **result}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
