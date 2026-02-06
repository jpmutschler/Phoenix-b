"""
Diagnostics API routes.

Provides endpoints for PRBS testing, eye diagrams, and other diagnostic operations.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from phoenix.api import app as app_module
from phoenix.protocol.enums import PRBSPattern, MaxDataRate

router = APIRouter()


class PRBSStartRequest(BaseModel):
    """Request to start PRBS test."""

    pattern: str = Field(default="PRBS31", description="PRBS pattern")
    data_rate: str = Field(default="GEN5_32G", description="Data rate")
    lanes: List[int] = Field(default_factory=lambda: list(range(16)), description="Lanes to test")
    sample_count: int = Field(default=0x100000, description="Sample count")


class PRBSStatusResponse(BaseModel):
    """PRBS test status response."""

    running: bool
    pattern: str
    data_rate: str
    lanes: List[int]


class PRBSResultResponse(BaseModel):
    """PRBS test results."""

    lane: int
    bit_count: int
    error_count: int
    bit_error_rate: str
    sync_acquired: bool
    complete: bool


class EyeDiagramRequest(BaseModel):
    """Request for eye diagram capture."""

    lane: int = Field(ge=0, le=15, description="Lane number")
    data_rate: str = Field(default="GEN5_32G", description="Data rate")


class EyeDiagramResponse(BaseModel):
    """Eye diagram capture result."""

    lane: int
    data_rate: str
    left_margin_mui: int
    right_margin_mui: int
    upper_margin_mv: int
    lower_margin_mv: int
    horizontal_opening_mui: int
    vertical_opening_mv: int
    valid: bool


# Note: Full PRBS implementation would require additional device commands
# This provides the API structure that can be extended

@router.post("/{handle}/prbs/start")
async def start_prbs(handle: int, request: PRBSStartRequest) -> dict:
    """Start PRBS generator and checker.

    Note: Full implementation requires additional device command support.
    """
    try:
        device = app_module.get_device(handle)

        # Validate pattern
        try:
            pattern = PRBSPattern[request.pattern]
        except KeyError:
            raise HTTPException(
                status_code=400, detail=f"Invalid PRBS pattern: {request.pattern}"
            )

        # Validate data rate
        try:
            rate = MaxDataRate[request.data_rate]
        except KeyError:
            raise HTTPException(
                status_code=400, detail=f"Invalid data rate: {request.data_rate}"
            )

        # Validate lanes
        for lane in request.lanes:
            if lane < 0 or lane > 15:
                raise HTTPException(
                    status_code=400, detail=f"Invalid lane number: {lane}"
                )

        # TODO: Implement actual PRBS start command
        # This would write to the PRBS control registers

        return {
            "status": "started",
            "pattern": pattern.name,
            "data_rate": rate.name,
            "lanes": request.lanes,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{handle}/prbs/status", response_model=PRBSStatusResponse)
async def get_prbs_status(handle: int) -> PRBSStatusResponse:
    """Get PRBS test status."""
    try:
        device = app_module.get_device(handle)

        # TODO: Read actual PRBS status registers

        return PRBSStatusResponse(
            running=False,
            pattern="PRBS31",
            data_rate="GEN5_32G",
            lanes=[],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{handle}/prbs/stop")
async def stop_prbs(handle: int) -> dict:
    """Stop PRBS test."""
    try:
        device = app_module.get_device(handle)

        # TODO: Implement actual PRBS stop command

        return {"status": "stopped"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{handle}/prbs/results", response_model=List[PRBSResultResponse])
async def get_prbs_results(handle: int) -> List[PRBSResultResponse]:
    """Get PRBS test results for all tested lanes."""
    try:
        device = app_module.get_device(handle)

        # TODO: Read actual PRBS results

        return []

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{handle}/eye-diagram", response_model=EyeDiagramResponse)
async def capture_eye_diagram(handle: int, request: EyeDiagramRequest) -> EyeDiagramResponse:
    """Capture eye diagram for a lane.

    Note: Full implementation requires additional device command support.
    """
    try:
        device = app_module.get_device(handle)

        # Validate data rate
        try:
            rate = MaxDataRate[request.data_rate]
        except KeyError:
            raise HTTPException(
                status_code=400, detail=f"Invalid data rate: {request.data_rate}"
            )

        # TODO: Implement actual eye diagram capture

        return EyeDiagramResponse(
            lane=request.lane,
            data_rate=rate.name,
            left_margin_mui=0,
            right_margin_mui=0,
            upper_margin_mv=0,
            lower_margin_mv=0,
            horizontal_opening_mui=0,
            vertical_opening_mv=0,
            valid=False,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{handle}/prbs/patterns")
async def list_prbs_patterns() -> dict:
    """List available PRBS patterns."""
    return {
        "patterns": [
            {"name": pattern.name, "value": pattern.value}
            for pattern in PRBSPattern
        ]
    }
