from pydantic import BaseModel
from typing import Any, Dict, Optional


class GenerateFitRequest(BaseModel):
    workout_id: Optional[str] = None
    title: Optional[str] = None
    # Canonical workout JSON (whatever mapper-api produces)
    workout: Dict[str, Any]
    # Optional: device info if needed later
    device_profile: Optional[Dict[str, Any]] = None

