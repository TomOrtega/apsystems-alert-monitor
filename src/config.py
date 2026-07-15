import os
import logging
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class AccountConfig:
    name: str
    app_id: str
    app_secret: str
    base_url: str
    systems: list[str] = field(default_factory=list)


@dataclass
class SmtpConfig:
    host: str
    port: int
    user: str
    password: str
    from_addr: str
    alert_to: str
    enabled: bool = True


@dataclass
class TelegramConfig:
    bot_token: str
    chat_id: str
    enabled: bool = False


@dataclass
class DbConfig:
    host: str
    port: int
    user: str
    password: str
    name: str

    @property
    def dsn(self) -> str:
        return (
            f"host={self.host} port={self.port} "
            f"dbname={self.name} user={self.user} password={self.password}"
        )


@dataclass
class AppConfig:
    accounts: list[AccountConfig]
    smtp: SmtpConfig
    telegram: TelegramConfig
    db: DbConfig
    check_interval_hours: int
    alert_retention_days: int


def _load_accounts_from_env() -> list[AccountConfig]:
    accounts = []
    idx = 1
    while True:
        app_id = os.getenv(f"ACCOUNT{idx}_APP_ID")
        if not app_id:
            break
        name = os.getenv(f"ACCOUNT{idx}_NAME", f"Account{idx}")
        app_secret = os.getenv(f"ACCOUNT{idx}_APP_SECRET", "")
        base_url = os.getenv(
            f"ACCOUNT{idx}_BASE_URL",
            "https://api.apsystemsema.com:9282",
        )
        systems_raw = os.getenv(f"ACCOUNT{idx}_SYSTEMS", "")
        systems = [s.strip() for s in systems_raw.split(",") if s.strip()]
        accounts.append(AccountConfig(name=name, app_id=app_id, app_secret=app_secret, base_url=base_url, systems=systems))
        logger.info("Cuenta cargada (env): %s (%d sistemas)", name, len(systems))
        idx += 1
    return accounts


def _load_config_from_db():
    try:
        from src.storage.db import Database
        db = Database(DbConfig(
            host=os.getenv("DB_HOST", "postgres"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER", "apsystems"),
            password=os.getenv("DB_PASSWORD", "changeme"),
            name=os.getenv("DB_NAME", "apsystems_monitor"),
        ))
        db.connect()
        conn = db._get_conn()

        with conn.cursor() as cur:
            cur.execute("SELECT key, value FROM config WHERE section = 'accounts' ORDER BY id")
            raw = {r[0]: r[1] for r in cur.fetchall()}

        accounts = []
        idx = 1
        while True:
            prefix = f"account{idx}"
            app_id = raw.get(f"{prefix}_app_id", "")
            if not app_id:
                break
            accounts.append(AccountConfig(
                name=raw.get(f"{prefix}_name", f"Account{idx}"),
                app_id=app_id,
                app_secret=raw.get(f"{prefix}_app_secret", ""),
                base_url=raw.get(f"{prefix}_base_url", "https://api.apsystemsema.com:9282"),
                systems=[s.strip() for s in raw.get(f"{prefix}_systems", "").split(",") if s.strip()],
            ))
            idx += 1

        with conn.cursor() as cur:
            cur.execute("SELECT key, value FROM config WHERE section = 'smtp'")
            smtp_raw = {r[0]: r[1] for r in cur.fetchall()}

        smtp = SmtpConfig(
            host=smtp_raw.get("host", os.getenv("SMTP_HOST", "smtp.office365.com")),
            port=int(smtp_raw.get("port", os.getenv("SMTP_PORT", "587"))),
            user=smtp_raw.get("user", os.getenv("SMTP_USER", "")),
            password=smtp_raw.get("password", os.getenv("SMTP_PASSWORD", "")),
            from_addr=smtp_raw.get("from_addr", os.getenv("SMTP_FROM", "")),
            alert_to=smtp_raw.get("alert_to", os.getenv("ALERT_TO", "")),
            enabled=smtp_raw.get("enabled", "true").lower() == "true",
        )

        with conn.cursor() as cur:
            cur.execute("SELECT key, value FROM config WHERE section = 'telegram'")
            tg_raw = {r[0]: r[1] for r in cur.fetchall()}

        telegram = TelegramConfig(
            bot_token=tg_raw.get("bot_token", ""),
            chat_id=tg_raw.get("chat_id", ""),
            enabled=tg_raw.get("enabled", "false").lower() == "true",
        )

        with conn.cursor() as cur:
            cur.execute("SELECT key, value FROM config WHERE section = 'scheduler'")
            sched_raw = {r[0]: r[1] for r in cur.fetchall()}

        db.close()

        return AppConfig(
            accounts=accounts,
            smtp=smtp,
            telegram=telegram,
            db=DbConfig(
                host=os.getenv("DB_HOST", "postgres"),
                port=int(os.getenv("DB_PORT", "5432")),
                user=os.getenv("DB_USER", "apsystems"),
                password=os.getenv("DB_PASSWORD", "changeme"),
                name=os.getenv("DB_NAME", "apsystems_monitor"),
            ),
            check_interval_hours=int(sched_raw.get("check_interval_hours", "24")),
            alert_retention_days=int(sched_raw.get("alert_retention_days", "90")),
        )
    except Exception as e:
        logger.warning("No se pudo cargar config de DB, usando .env: %s", e)
        return None


def load_config() -> AppConfig:
    db_config = _load_config_from_db()
    if db_config and db_config.accounts:
        logger.info("Configuracion cargada desde PostgreSQL: %d cuentas", len(db_config.accounts))
        return db_config

    logger.info("Fallback: cargando configuracion desde .env")
    accounts = _load_accounts_from_env()
    smtp = SmtpConfig(
        host=os.getenv("SMTP_HOST", "smtp.office365.com"),
        port=int(os.getenv("SMTP_PORT", "587")),
        user=os.getenv("SMTP_USER", ""),
        password=os.getenv("SMTP_PASSWORD", ""),
        from_addr=os.getenv("SMTP_FROM", ""),
        alert_to=os.getenv("ALERT_TO", ""),
    )
    telegram = TelegramConfig(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        enabled=os.getenv("ENABLE_TELEGRAM", "false").lower() == "true",
    )
    return AppConfig(
        accounts=accounts,
        smtp=smtp,
        telegram=telegram,
        db=DbConfig(
            host=os.getenv("DB_HOST", "postgres"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER", "apsystems"),
            password=os.getenv("DB_PASSWORD", "changeme"),
            name=os.getenv("DB_NAME", "apsystems_monitor"),
        ),
        check_interval_hours=int(os.getenv("CHECK_INTERVAL_HOURS", "24")),
        alert_retention_days=int(os.getenv("ALERT_RETENTION_DAYS", "90")),
    )


def load_config_from_db(db) -> AppConfig:
    return load_config()
