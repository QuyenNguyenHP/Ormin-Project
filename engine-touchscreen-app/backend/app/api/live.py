from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import LiveEngineData
from app.schemas import LiveValueResponse
from app.services.live_service import get_latest_all, get_latest_by_addr, get_latest_by_group

router = APIRouter(prefix="/api/live", tags=["live"])


@router.get("/all", response_model=list[LiveValueResponse])
def live_all(db: Session = Depends(get_db)):
    return get_latest_all(db)


@router.get("/timestamp")
def live_latest_timestamp(db: Session = Depends(get_db)):
    latest_ts = db.execute(select(func.max(LiveEngineData.timestamp))).scalar_one_or_none()
    return {"timestamp": latest_ts}


@router.get("/lable_value")
def live_lable_value(db: Session = Depends(get_db)):
    rows = get_latest_all(db)
    return [{"label": r.label, "value": r.value} for r in rows]


@router.get("/analog_lable_value")
def live_analog_lable_value(db: Session = Depends(get_db)):
    rows = get_latest_all(db)
    return [
        {"label": r.label, "value": r.value}
        for r in rows
        if (r.unit or "").strip().lower() != "on/off"
    ]


@router.get("/{addr}", response_model=LiveValueResponse)
def live_by_addr(addr: str, db: Session = Depends(get_db)):
    item = get_latest_by_addr(db, addr)
    if item is None:
        raise HTTPException(status_code=404, detail="Address not found")
    return item


@router.get("/group/{group_name}", response_model=list[LiveValueResponse])
def live_by_group(group_name: str, db: Session = Depends(get_db)):
    return get_latest_by_group(db, group_name)
