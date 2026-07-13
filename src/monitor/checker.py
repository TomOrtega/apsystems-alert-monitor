import logging
from datetime import datetime

from src.api.models import SystemInfo, Alerta, DailySummary
from src.monitor.batch import fetch_all_systems
from src.monitor.rules import detect_alert, count_by_light
from src.storage.db import Database
from src.config import AccountConfig

logger = logging.getLogger(__name__)


def run_check(
    accounts: list[AccountConfig],
    db: Database,
) -> list[Alerta]:
    all_alertas = []
    today = datetime.now().strftime("%Y-%m-%d")

    for account in accounts:
        logger.info("=== Verificando cuenta: %s ===", account.name)

        api_calls_before = db.get_calls_this_month(account.name)

        systems, calls_used = fetch_all_systems(account)

        for system in systems:
            db.upsert_system(system)

        alertas_generadas = 0
        for system in systems:
            light_anterior = db.get_system_light(system.sid)
            if light_anterior == system.light:
                continue

            alerta = detect_alert(system, light_anterior)
            if alerta:
                alerta_id = db.insert_alerta(alerta)
                alerta.id = alerta_id
                all_alertas.append(alerta)
                alertas_generadas += 1
                logger.warning(
                    "ALERTA: %s [%s] %s",
                    alerta.severidad.upper(),
                    alerta.tipo,
                    alerta.mensaje,
                )

        counts = count_by_light(systems)
        summary = DailySummary(
            date=today,
            account_name=account.name,
            total_sistemas=len(systems),
            green_count=counts["green"],
            yellow_count=counts["yellow"],
            red_count=counts["red"],
            grey_count=counts["grey"],
            unknown_count=counts["unknown"],
            api_calls_used=calls_used,
            alertas_generadas=alertas_generadas,
        )
        db.upsert_daily_summary(summary)

        api_calls_after = db.get_calls_this_month(account.name)
        logger.info(
            "Cuenta %s: %d sistemas, %d verdes, %d amarillos, %d rojos, %d grises, "
            "%d alertas, llamadas API este mes: %d/%d",
            account.name,
            len(systems),
            counts["green"],
            counts["yellow"],
            counts["red"],
            counts["grey"],
            alertas_generadas,
            api_calls_after,
            api_calls_after + (1000 - api_calls_after),
        )

    logger.info(
        "=== Verificacion completada: %d alertas totales ===",
        len(all_alertas),
    )
    return all_alertas
