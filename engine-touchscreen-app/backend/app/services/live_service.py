from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import LiveEngineData
from app.schemas import LiveValueResponse


def get_latest_all(db: Session) -> list[LiveValueResponse]:
    latest_ts = (
        select(LiveEngineData.addr, func.max(LiveEngineData.timestamp).label("max_ts"))
        .group_by(LiveEngineData.addr)
        .subquery()
    )

    stmt = (
        select(LiveEngineData)
        .join(
            latest_ts,
            (LiveEngineData.addr == latest_ts.c.addr)
            & (LiveEngineData.timestamp == latest_ts.c.max_ts),
        )
        .order_by(LiveEngineData.addr)
    )

    rows = db.execute(stmt).scalars().all()
    return [
        LiveValueResponse(
            addr=r.addr,
            label=r.label,
            value=r.val,
            unit=r.unit,
            timestamp=r.timestamp,
        )
        for r in rows
    ]


def get_latest_by_addr(db: Session, addr: str) -> LiveValueResponse | None:
    stmt = (
        select(LiveEngineData)
        .where(LiveEngineData.addr == addr)
        .order_by(LiveEngineData.timestamp.desc())
        .limit(1)
    )
    row = db.execute(stmt).scalar_one_or_none()
    if row is None:
        return None
    return LiveValueResponse(
        addr=row.addr,
        label=row.label,
        value=row.val,
        unit=row.unit,
        timestamp=row.timestamp,
    )


def get_latest_by_group(db: Session, group_name: str) -> list[LiveValueResponse]:
    all_rows = get_latest_all(db)
    keyword = group_name.strip().lower()
    return [r for r in all_rows if (r.label or "").lower().find(keyword) >= 0]
