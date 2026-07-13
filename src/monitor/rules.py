import logging

from src.api.models import (
    LightStatus,
    LIGHT_LABELS,
    SEVERITY_MAP,
    SystemInfo,
    Alerta,
)

logger = logging.getLogger(__name__)


def classify_light(light: int | None) -> tuple[str, str]:
    if light is None:
        return "unknown", "info"
    try:
        status = LightStatus(light)
        return LIGHT_LABELS[status], SEVERITY_MAP[status]
    except ValueError:
        return f"desconocido ({light})", "info"


def detect_alert(
    system: SystemInfo, light_anterior: int | None
) -> Alerta | None:
    light_nuevo = system.light

    if light_nuevo == light_anterior:
        return None

    if light_nuevo is None and light_anterior is None:
        return None

    label, severidad = classify_light(light_nuevo)
    label_anterior, _ = classify_light(light_anterior)

    if light_nuevo == LightStatus.GREEN:
        if light_anterior is not None and light_anterior != LightStatus.GREEN:
            return Alerta(
                sid=system.sid,
                account_name=system.account_name,
                tipo="recovery",
                severidad="info",
                mensaje=(
                    f"Sistema {system.sid} recuperado: "
                    f"{label_anterior} -> {label}"
                ),
                light_anterior=light_anterior,
                light_nuevo=light_nuevo,
            )
        return None

    if light_anterior is None or light_anterior == LightStatus.GREEN:
        return Alerta(
            sid=system.sid,
            account_name=system.account_name,
            tipo="light_change",
            severidad=severidad,
            mensaje=(
                f"Sistema {system.sid} ({system.account_name}): "
                f"Cambio de estado a {label}"
            ),
            light_anterior=light_anterior,
            light_nuevo=light_nuevo,
        )

    if light_nuevo != light_anterior:
        return Alerta(
            sid=system.sid,
            account_name=system.account_name,
            tipo="light_change",
            severidad=severidad,
            mensaje=(
                f"Sistema {system.sid} ({system.account_name}): "
                f"Estado cambio de {label_anterior} a {label}"
            ),
            light_anterior=light_anterior,
            light_nuevo=light_nuevo,
        )

    return None


def count_by_light(systems: list[SystemInfo]) -> dict[str, int]:
    counts = {"green": 0, "yellow": 0, "red": 0, "grey": 0, "unknown": 0}
    for s in systems:
        if s.light is None:
            counts["unknown"] += 1
        elif s.light == LightStatus.GREEN:
            counts["green"] += 1
        elif s.light == LightStatus.YELLOW:
            counts["yellow"] += 1
        elif s.light == LightStatus.RED:
            counts["red"] += 1
        elif s.light == LightStatus.GREY:
            counts["grey"] += 1
        else:
            counts["unknown"] += 1
    return counts
