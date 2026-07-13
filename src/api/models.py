from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum


class LightStatus(IntEnum):
    GREEN = 1
    YELLOW = 2
    RED = 3
    GREY = 4


LIGHT_LABELS = {
    LightStatus.GREEN: "Normal",
    LightStatus.YELLOW: "Alarma en inversor",
    LightStatus.RED: "ECU offline",
    LightStatus.GREY: "Sin datos",
}

SEVERITY_MAP = {
    LightStatus.GREEN: "info",
    LightStatus.YELLOW: "warning",
    LightStatus.RED: "critical",
    LightStatus.GREY: "critical",
}


@dataclass
class SystemInfo:
    sid: str
    account_name: str
    light: int | None = None
    ecu_list: list[str] = field(default_factory=list)
    capacity: str = ""
    system_type: int = 1
    timezone: str = "UTC"


@dataclass
class Alerta:
    sid: str
    account_name: str
    tipo: str
    severidad: str
    mensaje: str
    light_anterior: int | None = None
    light_nuevo: int | None = None
    email_enviado: bool = False
    created_at: datetime | None = None


@dataclass
class DailySummary:
    date: str
    account_name: str
    total_sistemas: int = 0
    green_count: int = 0
    yellow_count: int = 0
    red_count: int = 0
    grey_count: int = 0
    unknown_count: int = 0
    api_calls_used: int = 0
    alertas_generadas: int = 0
