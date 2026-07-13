import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.config import SmtpConfig
from src.api.models import Alerta, LightStatus, LIGHT_LABELS

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _light_color(light: int | None) -> str:
    if light is None:
        return "unknown"
    try:
        return LightStatus(light).name.lower()
    except ValueError:
        return "unknown"


def _light_label(light: int | None) -> str:
    if light is None:
        return "Sin datos"
    try:
        return LIGHT_LABELS[LightStatus(light)]
    except ValueError:
        return f"Desconocido ({light})"


class EmailSender:
    def __init__(self, config: SmtpConfig):
        self.config = config
        self._env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=True,
        )

    def _send(self, to: str, subject: str, html_body: str):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.config.from_addr
        msg["To"] = to

        text_part = MIMEText(html_body, "plain", "utf-8")
        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(text_part)
        msg.attach(html_part)

        try:
            with smtplib.SMTP(self.config.host, self.config.port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.config.user, self.config.password)
                server.sendmail(self.config.from_addr, [to], msg.as_string())
            logger.info("Email enviado a %s: %s", to, subject)
        except Exception as e:
            logger.error("Error enviando email a %s: %s", to, e)
            raise

    def send_alert(self, alerta: Alerta):
        template = self._env.get_template("alert.html")
        html = template.render(
            account_name=alerta.account_name,
            sid=alerta.sid,
            tipo=alerta.tipo,
            severidad=alerta.severidad,
            mensaje=alerta.mensaje,
            light_anterior=alerta.light_anterior,
            light_nuevo=alerta.light_nuevo,
            light_anterior_color=_light_color(alerta.light_anterior),
            light_nuevo_color=_light_color(alerta.light_nuevo),
            light_anterior_label=_light_label(alerta.light_anterior),
            light_nuevo_label=_light_label(alerta.light_nuevo),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        severity_emoji = {
            "critical": "[CRITICO]",
            "warning": "[ALERTA]",
            "info": "[INFO]",
        }
        prefix = severity_emoji.get(alerta.severidad, "")
        subject = f"{prefix} APsystems - {alerta.account_name} - {alerta.sid}"

        self._send(self.config.alert_to, subject, html)

    def send_daily_report(
        self,
        accounts_data: list[dict],
        api_usage: list[dict],
    ):
        template = self._env.get_template("daily_report.html")
        html = template.render(
            date=datetime.now().strftime("%Y-%m-%d"),
            accounts=accounts_data,
            api_usage=api_usage,
        )

        subject = f"Reporte Diario APsystems Monitor - {datetime.now().strftime('%Y-%m-%d')}"
        self._send(self.config.alert_to, subject, html)
