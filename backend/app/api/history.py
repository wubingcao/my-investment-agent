from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select, desc

from app.config import get_settings
from app.db import session_scope
from app.models import AnalysisRun, Signal

router = APIRouter()


@router.get("/runs")
async def list_runs(limit: int = 30) -> list[dict]:
    async with session_scope() as db:
        stmt = select(AnalysisRun).order_by(desc(AnalysisRun.started_at)).limit(limit)
        rows = (await db.execute(stmt)).scalars().all()
    return [_run_out(r) for r in rows]


@router.get("/runs/{run_id}")
async def run_detail(run_id: int) -> dict:
    async with session_scope() as db:
        run = await db.get(AnalysisRun, run_id)
        if not run:
            raise HTTPException(404, "run not found")
        stmt = select(Signal).where(Signal.run_id == run_id)
        sigs = (await db.execute(stmt)).scalars().all()
    out = _run_out(run)
    out["signals"] = [
        {
            "id": s.id, "ticker": s.ticker, "action": s.action,
            "confidence": s.confidence, "target_pct": s.target_pct,
            "qc_passed": s.qc_passed, "thesis": s.thesis,
        }
        for s in sigs
    ]
    return out


@router.get("/runs/{run_id}/pine")
async def run_pine_script(run_id: int):
    cfg = get_settings()
    path = cfg.pine_path / f"run_{run_id}.pine"
    if not path.exists():
        raise HTTPException(404, "pine script not found for this run")
    content = path.read_text(encoding="utf-8")
    return Response(content=content, media_type="text/plain")


def _run_out(r: AnalysisRun) -> dict:
    return {
        "id": r.id,
        "started_at": r.started_at.isoformat(),
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "trigger": r.trigger,
        "tickers": r.tickers,
        "status": r.status,
        "error": r.error,
    }
