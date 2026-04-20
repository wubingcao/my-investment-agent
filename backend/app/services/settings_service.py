from __future__ import annotations

from sqlalchemy import select

from app.db import session_scope
from app.models import Setting
from app.schemas import RiskSettings

RISK_KEY = "risk"


async def get_risk_settings() -> RiskSettings:
    async with session_scope() as db:
        row = await db.get(Setting, RISK_KEY)
        if row:
            return RiskSettings(**row.value)
    return RiskSettings()


async def set_risk_settings(settings: RiskSettings) -> RiskSettings:
    async with session_scope() as db:
        row = await db.get(Setting, RISK_KEY)
        payload = settings.model_dump()
        if row:
            row.value = payload
        else:
            db.add(Setting(key=RISK_KEY, value=payload))
    return settings
