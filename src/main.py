import os
import time
import logging
import sys
import threading
from datetime import datetime
from pathlib import Path

import schedule
import uvicorn

from src.config import load_config
from src.storage.db import Database
from src.monitor.checker import run_check
from src.monitor.collector import collect_and_write
from src.notify.email_sender import EmailSender
from src.notify.telegram_sender import TelegramSender
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
            if config.smtp.enabled and config.smtp.user:
                try:
                    sender = EmailSender(config.smtp)
                    for alerta in alertas:
                        try:
                            sender.send_alert(alerta)
                            if alerta.id is not None:
                                db.mark_email_sent(alerta.id)
                            logger.info("Alerta enviada por email: %s", alerta.sid)
                        except Exception as e:
                            logger.error("Error enviando email para %s: %s", alerta.sid, e)
                except Exception as e:
                    logger.error("Error inicializando email sender: %s", e)
            else:
                logger.info("Email deshabilitado, saltando envio")

            if config.telegram.enabled and config.telegram.bot_token:
                try:
                    tg = TelegramSender(config.telegram.bot_token, config.telegram.chat_id)
                    for alerta in alertas:
                        tg.send_alert(alerta)
                    logger.info("Alertas enviadas por Telegram: %d", len(alertas))
                except Exception as e:
                    logger.error("Error enviando Telegram: %s", e)
            else:
                logger.info("Telegram deshabilitado, saltando envio")

        api_usage = []
        for account in config.accounts:
            used = db.get_calls_this_month(account.name)
            remaining = max(0, 1000 - used)
            api_usage.append({"name": account.name, "used": used, "remaining": remaining})

        accounts_summary = _build_accounts_summary(alertas, config)

        if accounts_summary:
            if config.smtp.enabled and config.smtp.user:
                try:
                    sender = EmailSender(config.smtp)
                    sender.send_daily_report(accounts_summary, api_usage)
                    logger.info("Reporte diario enviado por email")
                except Exception as e:
                    logger.error("Error enviando reporte diario: %s", e)

            if config.telegram.enabled and config.telegram.bot_token:
                try:
                    tg = TelegramSender(config.telegram.bot_token, config.telegram.chat_id)
                    tg.send_daily_report(accounts_summary, api_usage)
                    logger.info("Reporte diario enviado por Telegram")
                except Exception as e:
                    logger.error("Error enviando reporte Telegram: %s", e)

        db.cleanup_old_alertas(config.alert_retention_days)
        db.cleanup_old_api_calls(config.alert_retention_days)

        collect_stats = collect_and_write(config.accounts, config.influx, db)

        elapsed = time.time() - start_time
        logger.info("Verificacion completada en %.1f segundos", elapsed)
        logger.info("Uso API: %s", api_usage)
        logger.info("InfluxDB recoleccion: %d sistemas, %d llamadas, %d errores",
                     collect_stats["systems_collected"], collect_stats["calls_used"], collect_stats["errors"])
        logger.info("=" * 60)

        db.close()

    except Exception as e:
        logger.error("Error en verificacion: %s", e, exc_info=True)


def _build_accounts_summary(alertas, config) -> list[dict]:
    summaries = []
    for account in config.accounts:
        account_alertas = [
            {"sid": a.sid, "severidad": a.severidad, "mensaje": a.mensaje, "light_color": _light_color(a.light_nuevo)}
            for a in alertas
            if a.account_name == account.name
        ]
        summaries.append({
            "name": account.name,
            "total": len(account.systems),
            "green": 0, "yellow": 0, "red": 0, "grey": 0,
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


def start_api_server():
    config = load_config()
    db = config.db
    os.environ["DB_HOST"] = db.host
    os.environ["DB_PORT"] = str(db.port)
    os.environ["DB_USER"] = db.user
    os.environ["DB_PASSWORD"] = db.password
    os.environ["DB_NAME"] = db.name

    uvicorn.run("src.api_server:app", host="0.0.0.0", port=8000, log_level="info")


def main():
    config = load_config()

    logger.info("APsystems Alert Monitor iniciado")
    logger.info("Cuentas configuradas: %d", len(config.accounts))
    for account in config.accounts:
        logger.info("  - %s: %d sistemas", account.name, len(account.systems))
    logger.info("Intervalo de verificacion: cada %d horas", config.check_interval_hours)
    logger.info("Email habilitado: %s", config.smtp.enabled)
    logger.info("Telegram habilitado: %s", config.telegram.enabled)

    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    logger.info("API server iniciado en puerto 8000")

    logger.info("Ejecutando verificacion inicial...")
    run_monitor_job()

    schedule.every(config.check_interval_hours).hours.do(run_monitor_job)

    logger.info("Scheduler activo. Proxima verificacion en %d horas.", config.check_interval_hours)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
