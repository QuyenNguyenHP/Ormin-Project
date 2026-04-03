from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import AlarmResponse
from app.services.alarm_service import get_active_alarms

router = APIRouter(prefix="/api/alarms", tags=["alarms"])


@router.get("/active", response_model=list[AlarmResponse])
def active_alarms(db: Session = Depends(get_db)):
    return get_active_alarms(db)


@router.get("/history", response_model=list[AlarmResponse])
def alarm_history(db: Session = Depends(get_db)):
    # Placeholder: currently returns same as active alarms.
    return get_active_alarms(db)
