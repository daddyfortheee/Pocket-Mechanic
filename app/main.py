from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import re
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from app.diagnosis_engine import build_diagnostic_causes, fallback_cause
from app.project_planner import build_project_plan
from app.vision_engine import analyze_uploaded_images, VisionUnavailableError
from app.vehicle_catalog import router as vehicle_catalog_router

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads" / "media"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_IMAGE_SIZE = 15 * 1024 * 1024
MAX_VIDEO_SIZE = 75 * 1024 * 1024
UPLOADED_MEDIA: dict[str, dict[str, Any]] = {}

MAX_IMAGES = 6
MAX_VIDEOS = 1

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
}

app = FastAPI(title="Pocket Guru API", version="0.6.0")
app.include_router(vehicle_catalog_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

Category = Literal["automotive", "motorcycle", "appliance", "home", "equipment", "diy"]


def safe_filename(filename: str | None) -> str:
    original = filename or "upload"
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", original).strip("._")
    return clean[:120] or "upload"


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "version": app.version, "photo_analysis_configured": bool(os.getenv("OPENAI_API_KEY"))}


@app.post("/api/uploads")
async def upload_media(files: list[UploadFile] = File(...)) -> dict[str, Any]:
    if not files:
        raise HTTPException(status_code=400, detail="No files were selected.")

    if len(files) > MAX_IMAGES + MAX_VIDEOS:
        raise HTTPException(
            status_code=400,
            detail=f"Upload up to {MAX_IMAGES} pictures and {MAX_VIDEOS} video.",
        )

    image_count = 0
    video_count = 0
    uploaded: list[dict[str, Any]] = []

    for upload in files:
        content_type = (upload.content_type or "").lower()

        if content_type in ALLOWED_IMAGE_TYPES:
            image_count += 1
            file_kind = "image"
            size_limit = MAX_IMAGE_SIZE

            if image_count > MAX_IMAGES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Only {MAX_IMAGES} pictures may be uploaded.",
                )

        elif content_type in ALLOWED_VIDEO_TYPES:
            video_count += 1
            file_kind = "video"
            size_limit = MAX_VIDEO_SIZE

            if video_count > MAX_VIDEOS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Only {MAX_VIDEOS} video may be uploaded.",
                )

        else:
            raise HTTPException(
                status_code=415,
                detail=f"{upload.filename or 'The selected file'} is not a supported picture or video.",
            )

        contents = await upload.read(size_limit + 1)
        await upload.close()

        if len(contents) > size_limit:
            limit_mb = size_limit // (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"{upload.filename or 'The selected file'} exceeds the {limit_mb} MB limit.",
            )

        media_id = str(uuid4())
        cleaned_name = safe_filename(upload.filename)
        extension = Path(cleaned_name).suffix.lower()
        stored_name = f"{media_id}{extension}"
        stored_path = UPLOAD_DIR / stored_name
        stored_path.write_bytes(contents)

        uploaded.append(
            {
                "id": media_id,
                "kind": file_kind,
                "filename": cleaned_name,
                "content_type": content_type,
                "size_bytes": len(contents),
                "stored_name": stored_name,
            }
        )

    for record in uploaded:
        UPLOADED_MEDIA[record["id"]] = record

    return {
        "count": len(uploaded),
        "files": uploaded,
        "message": "Media uploaded successfully.",
    }


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
    visual_analysis: dict[str, Any] | None = None


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
    media = req.answers.get("media", [])
    media_count = len(media) if isinstance(media, list) else 0


    if req.category == "diy":
        plan = build_project_plan(
            description=req.symptom,
            answers=req.answers,
            media_count=media_count,
        )

        project_result = Cause(
            title=plan["title"],
            confidence=plan["confidence"],
            why=plan["why"],
            checks=plan["checks"],
            repair=plan["repair"],
            safety="medium",
        )

        return DiagnosisResponse(
            id=str(uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            category=req.category,
            symptom=req.symptom,
            summary=plan["summary"],
            safety_message=plan["safety_message"],
            causes=[project_result],
        )

    cause_data = build_diagnostic_causes(
        category=req.category,
        symptom=req.symptom,
        answers=req.answers,
    )

    if not cause_data:
        cause_data = [
            fallback_cause(
                category=req.category,
                media_count=media_count,
                answers=req.answers,
            )
        ]

    matches = [Cause(**item) for item in cause_data]

    safety_order = {
        "low": 0,
        "medium": 1,
        "high": 2,
        "stop": 3,
    }

    highest_safety = max(
        (cause.safety for cause in matches),
        key=lambda level: safety_order[level],
    )

    safety_message = {
        "low": "Normal precautions apply.",
        "medium": "Use appropriate PPE and disable power before disassembly.",
        "high": (
            "Do not operate until the fault is inspected. "
            "Disconnect power or disable the machine before service."
        ),
        "stop": (
            "STOP WORK. Leave the area safe and contact a qualified "
            "professional or emergency services when appropriate."
        ),
    }[highest_safety]

    if media_count == 1:
        media_summary = " One attachment was included."
    elif media_count > 1:
        media_summary = f" {media_count} attachments were included."
    else:
        media_summary = ""

    path_word = "path" if len(matches) == 1 else "paths"

    return DiagnosisResponse(
        id=str(uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        category=req.category,
        symptom=req.symptom,
        summary=(
            f"Pocket Guru found {len(matches)} likely diagnostic "
            f"{path_word}.{media_summary}"
        ),
        safety_message=safety_message,
        causes=matches,
    )


@app.post("/api/diagnoses", response_model=DiagnosisResponse, status_code=201)
def create_diagnosis(req: DiagnosisRequest) -> DiagnosisResponse:
    result = diagnose(req)
    media = req.answers.get("media", [])
    if isinstance(media, list) and media:
        # Resolve server-issued records; never trust client-supplied file paths or MIME types.
        records = [UPLOADED_MEDIA[item.get("id")] for item in media
                   if isinstance(item, dict) and isinstance(item.get("id"), str)
                   and item.get("id") in UPLOADED_MEDIA]
        try:
            result.visual_analysis = analyze_uploaded_images(records, req.category, req.symptom)
            if len(records) != len(media):
                result.visual_analysis["attachment_warning"] = "Some attachments expired or were not found. Upload them again."
        except VisionUnavailableError:
            result.visual_analysis = {"available": False, "reason": "Photo analysis is not configured on the server. Symptom diagnosis still works.", "analyzed_files": []}
        except (RuntimeError, ValueError, OSError, TypeError):
            result.visual_analysis = {"available": False, "reason": "Photo analysis could not finish. Try again or upload a clearer photo. Symptom diagnosis still works.", "analyzed_files": []}
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
