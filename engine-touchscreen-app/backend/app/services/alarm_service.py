from app.config import ALARM_RULES
from app.schemas import AlarmResponse
from app.services.live_service import get_latest_all


def _severity_for_rule(value: float | None, rule: dict) -> tuple[str | None, str | None]:
    if value is None:
        return None, None

    critical_above = rule.get("critical_above")
    warning_above = rule.get("warning_above")
    critical_below = rule.get("critical_below")
    warning_below = rule.get("warning_below")

    if critical_above is not None and value >= critical_above:
        return "critical", f">= {critical_above}"
    if warning_above is not None and value >= warning_above:
        return "warning", f">= {warning_above}"
    if critical_below is not None and value <= critical_below:
        return "critical", f"<= {critical_below}"
    if warning_below is not None and value <= warning_below:
        return "warning", f"<= {warning_below}"

    return None, None


def get_active_alarms(db) -> list[AlarmResponse]:
    latest = get_latest_all(db)
    alarms: list[AlarmResponse] = []

    for item in latest:
        label = item.label or ""
        for key, rule in ALARM_RULES.items():
            if key.lower() not in label.lower():
                continue
            severity, limit_text = _severity_for_rule(item.value, rule)
            if severity is None:
                continue
            alarms.append(
                AlarmResponse(
                    addr=item.addr,
                    label=item.label,
                    dg_name=item.dg_name,
                    severity=severity,
                    value=item.value,
                    unit=item.unit,
                    timestamp=item.timestamp,
                    message=f"{label} is {severity} ({item.value} {item.unit}), limit {limit_text}",
                )
            )

    alarms.sort(key=lambda a: (a.severity != "critical", a.timestamp), reverse=True)
    return alarms
