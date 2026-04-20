from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.schemas import AnalyzeRequest
from app.services.analysis_service import run_analysis

router = APIRouter()


@router.post("")
async def analyze(req: AnalyzeRequest, background: BackgroundTasks) -> dict:
    if not req.tickers:
        raise HTTPException(400, "tickers list is empty")
    # For MVP, run synchronously but capped
    run_id = await run_analysis(req.tickers, req.time_horizon, trigger="on_demand")
    return {"run_id": run_id, "status": "done"}


@router.post("/async")
async def analyze_async(req: AnalyzeRequest, background: BackgroundTasks) -> dict:
    """Kick off analysis in the background; client polls /api/history/runs/{id}."""
    if not req.tickers:
        raise HTTPException(400, "tickers list is empty")

    async def _wrap():
        try:
            await run_analysis(req.tickers, req.time_horizon, trigger="on_demand")
        except Exception:
            pass

    background.add_task(_wrap)
    return {"status": "queued"}
