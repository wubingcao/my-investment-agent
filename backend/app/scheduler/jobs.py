"""APScheduler setup for daily scans + phase-2 learning jobs."""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.config import get_settings
from app.db import session_scope
from app.models import Watchlist

log = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def daily_watchlist_scan():
    from app.services.analysis_service import run_analysis
    async with session_scope() as db:
        rows = (await db.execute(select(Watchlist))).scalars().all()
    tickers = [r.ticker for r in rows]
    if not tickers:
        log.info("Daily scan skipped: watchlist empty")
        return
    log.info("Daily scan running on %d tickers", len(tickers))
    try:
        await run_analysis(tickers, "swing", trigger="scheduled")
    except Exception:
        log.exception("Daily scan failed")


async def weekly_learning_job():
    # Phase 2 — placeholder hook
    try:
        from app.learning.learning_curator import run_weekly_learnings
        await run_weekly_learnings()
    except Exception:
        log.exception("Weekly learning job failed (expected during Phase 1)")


async def monthly_skill_job():
    try:
        from app.learning.skill_synthesizer import run_monthly_skills
        await run_monthly_skills()
    except Exception:
        log.exception("Monthly skill job failed (expected during Phase 1)")


async def daily_performance_eval():
    try:
        from app.learning.performance_evaluator import run_daily_evaluation
        await run_daily_evaluation()
    except Exception:
        log.exception("Daily performance eval failed (expected during Phase 1)")


def _cron_trigger(expression: str) -> CronTrigger:
    # APScheduler CronTrigger expects kwargs; accept standard 5-field cron "m h dom mon dow"
    parts = expression.split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron: {expression}")
    minute, hour, dom, mon, dow = parts
    return CronTrigger(minute=minute, hour=hour, day=dom, month=mon, day_of_week=dow.lower())


def start_scheduler():
    global _scheduler
    cfg = get_settings()
    if _scheduler and _scheduler.running:
        return
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(daily_watchlist_scan, _cron_trigger(cfg.daily_scan_cron), id="daily_scan", replace_existing=True)
    _scheduler.add_job(daily_performance_eval, _cron_trigger("0 17 * * MON-FRI"), id="daily_perf_eval", replace_existing=True)
    _scheduler.add_job(weekly_learning_job, _cron_trigger(cfg.weekly_learning_cron), id="weekly_learning", replace_existing=True)
    _scheduler.add_job(monthly_skill_job, _cron_trigger(cfg.monthly_skills_cron), id="monthly_skills", replace_existing=True)
    _scheduler.start()
    log.info("Scheduler started with daily/weekly/monthly jobs")


def shutdown_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
