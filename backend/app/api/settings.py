from fastapi import APIRouter

from app.schemas import RiskSettings
from app.services.settings_service import get_risk_settings, set_risk_settings

router = APIRouter()


@router.get("/risk")
async def get_risk() -> RiskSettings:
    return await get_risk_settings()


@router.put("/risk")
async def put_risk(settings: RiskSettings) -> RiskSettings:
    return await set_risk_settings(settings)
