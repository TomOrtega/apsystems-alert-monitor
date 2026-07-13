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
    db: DbConfig
    check_interval_hours: int
    alert_retention_days: int


def _load_accounts() -> list[AccountConfig]:
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

        accounts.append(
            AccountConfig(
                name=name,
                app_id=app_id,
                app_secret=app_secret,
                base_url=base_url,
                systems=systems,
            )
        )
        logger.info("Cuenta cargada: %s (%d sistemas)", name, len(systems))
        idx += 1

    return accounts


def load_config() -> AppConfig:
    accounts = _load_accounts()

    smtp = SmtpConfig(
        host=os.getenv("SMTP_HOST", "smtp.office365.com"),
        port=int(os.getenv("SMTP_PORT", "587")),
        user=os.getenv("SMTP_USER", ""),
        password=os.getenv("SMTP_PASSWORD", ""),
        from_addr=os.getenv("SMTP_FROM", ""),
        alert_to=os.getenv("ALERT_TO", ""),
    )

    db = DbConfig(
        host=os.getenv("DB_HOST", "postgres"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "apsystems"),
        password=os.getenv("DB_PASSWORD", "changeme"),
        name=os.getenv("DB_NAME", "apsystems_monitor"),
    )

    config = AppConfig(
        accounts=accounts,
        smtp=smtp,
        db=db,
        check_interval_hours=int(os.getenv("CHECK_INTERVAL_HOURS", "24")),
        alert_retention_days=int(os.getenv("ALERT_RETENTION_DAYS", "90")),
    )

    logger.info(
        "Configuracion cargada: %d cuentas, intervalo=%dh",
        len(accounts),
        config.check_interval_hours,
    )
    return config
