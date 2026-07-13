import os
import time
import logging
import sys
from datetime import datetime
from pathlib import Path

import schedule

from src.config import load_config
from src.storage.db import Database
from src.monitor.checker import run_check
from src.notify.email_sender import EmailSender
from src.api.models import LightStatus

LOG_DIR = Path("/app/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "monitor.log"),
    ],
)
logger = logging.getLogger(__name__)


def run_monitor_job():
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("INICIO DE VERIFICACION - %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        config = load_config()
        db = Database(config.db)
        db.connect()

        alertas = run_check(config.accounts, db)

        if alertas:
            sender = EmailSender(config.smtp)
            for alerta in alertas:
                try:
                    sender.send_alert(alerta)
                    if alerta.id is not None:
                        db.mark_email_sent(alerta.id)
                    logger.info("Alerta enviada por email: %s", alerta.sid)
                except Exception as e:
                    logger.error("Error enviando email para %s: %s", alerta.sid, e)

        api_usage = []
        for account in config.accounts:
            used = db.get_calls_this_month(account.name)
            remaining = max(0, 1000 - used)
            api_usage.append({
                "name": account.name,
                "used": used,
                "remaining": remaining,
            })

        accounts_summary = _build_accounts_summary(alertas, config)

        if accounts_summary:
            try:
                sender = EmailSender(config.smtp)
                sender.send_daily_report(accounts_summary, api_usage)
                logger.info("Reporte diario enviado por email")
            except Exception as e:
                logger.error("Error enviando reporte diario: %s", e)

        db.cleanup_old_alertas(config.alert_retention_days)
        db.cleanup_old_api_calls(config.alert_retention_days)

        elapsed = time.time() - start_time
        logger.info("Verificacion completada en %.1f segundos", elapsed)
        logger.info("Uso API: %s", api_usage)
        logger.info("=" * 60)

        db.close()

    except Exception as e:
        logger.error("Error en verificacion: %s", e, exc_info=True)


def _build_accounts_summary(alertas, config) -> list[dict]:
    summaries = []
    today = datetime.now().strftime("%Y-%m-%d")

    for account in config.accounts:
        account_alertas = [
            {
                "sid": a.sid,
                "severidad": a.severidad,
                "mensaje": a.mensaje,
                "light_color": _light_color(a.light_nuevo),
            }
            for a in alertas
            if a.account_name == account.name
        ]

        summaries.append({
            "name": account.name,
            "total": len(account.systems),
            "green": 0,
            "yellow": 0,
            "red": 0,
            "grey": 0,
            "alertas": account_alertas,
            "api_calls": 0,
        })

    return summaries


def _light_color(light: int | None) -> str:
    if light is None:
        return "unknown"
    try:
        return LightStatus(light).name.lower()
    except ValueError:
        return "unknown"


def main():
    config = load_config()

    logger.info("APsystems Alert Monitor iniciado")
    logger.info("Cuentas configuradas: %d", len(config.accounts))
    for account in config.accounts:
        logger.info("  - %s: %d sistemas", account.name, len(account.systems))
    logger.info("Intervalo de verificacion: cada %d horas", config.check_interval_hours)

    logger.info("Ejecutando verificacion inicial...")
    run_monitor_job()

    schedule.every(config.check_interval_hours).hours.do(run_monitor_job)

    logger.info("Scheduler activo. Proxima verificacion en %d horas.", config.check_interval_hours)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
