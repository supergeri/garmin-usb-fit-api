from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import io
import os
import tempfile
import json

from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.workout_message import WorkoutMessage
from fit_tool.profile.messages.workout_step_message import WorkoutStepMessage
from fit_tool.profile.profile_type import (
    Sport,
    Intensity,
    WorkoutStepDuration,
    WorkoutStepTarget,
    Manufacturer,
    FileType,
)

from .schemas import GenerateFitRequest

app = FastAPI(
    title="Garmin USB FIT API",
    description="Generates FIT files for USB transfer to Garmin watches",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def build_simple_workout_fit_bytes(req: "GenerateFitRequest") -> bytes:
    """
    Build a simple, valid FIT workout using fit_tool.
    Later we will map full canonical workout JSON → actual multiple steps.
    For now, this creates a single OPEN step that Garmin accepts.
    """
    title = (req.title or "AmakaFlow Workout").strip() or "AmakaFlow Workout"

    # ---- File ID Message ----
    file_id = FileIdMessage()
    file_id.type = FileType.WORKOUT
    file_id.manufacturer = Manufacturer.DEVELOPMENT.value
    file_id.product = 0
    file_id.time_created = round(datetime.now().timestamp() * 1000)
    file_id.serial_number = 0x12345678

    # ---- One Workout Step ----
    step = WorkoutStepMessage()
    step.workout_step_name = title[:50]
    step.intensity = Intensity.ACTIVE
    step.duration_type = WorkoutStepDuration.OPEN
    step.durationValue = 0
    step.target_type = WorkoutStepTarget.OPEN
    step.target_value = 0

    # ---- Workout Message ----
    workout_msg = WorkoutMessage()
    workout_msg.workoutName = title[:50]
    workout_msg.sport = Sport.GENERIC
    workout_msg.num_valid_steps = 1

    # ---- Build FIT file ----
    builder = FitFileBuilder(auto_define=True, min_string_size=50)
    builder.add(file_id)
    builder.add(workout_msg)
    builder.add(step)

    fit_file = builder.build()

    # ---- Write FIT file to temp file → return bytes ----
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".fit") as tmp:
            tmp_path = tmp.name

        fit_file.to_file(tmp_path)

        with open(tmp_path, "rb") as f:
            return f.read()

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/generate-fit")
async def generate_fit(req: GenerateFitRequest):
    """
    Generate a Garmin-compatible FIT workout file.
    Currently builds a simple one-step workout using fit_tool.
    """
    try:
        fit_bytes = build_simple_workout_fit_bytes(req)
    except Exception as exc:
        print("Error generating FIT file:", exc)
        raise HTTPException(status_code=500, detail="Failed to generate FIT file")

    filename_title = (req.title or "workout").strip() or "workout"
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in filename_title)
    download_name = f"{safe_name}.fit"

    return StreamingResponse(
        io.BytesIO(fit_bytes),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"'
        },
    )


@app.get("/")
async def root():
    return JSONResponse(
        {
            "service": "garmin-usb-fit-api",
            "version": "0.1.0",
            "endpoints": ["/health", "/generate-fit"],
        }
    )

