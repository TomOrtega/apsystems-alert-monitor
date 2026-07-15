import logging
import requests

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


class TelegramSender:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"{TELEGRAM_API}/bot{bot_token}"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {"chat_id": self.chat_id, "text": text, "parse_mode": parse_mode}
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info("Mensaje Telegram enviado a chat %s", self.chat_id)
                return True
            logger.error("Error Telegram %d: %s", resp.status_code, resp.text)
            return False
        except Exception as e:
            logger.error("Error enviando Telegram: %s", e)
            return False

    def send_alert(self, alerta) -> bool:
        severity_emoji = {"critical": "\U0001f534", "warning": "\U0001f7e1", "info": "\U0001f7e2"}
        emoji = severity_emoji.get(alerta.severidad, "\u2753")
        text = (
            f"{emoji} <b>Alerta Solar - {alerta.severidad.upper()}</b>\n\n"
            f"Sistema: <code>{alerta.sid}</code>\n"
            f"Cuenta: {alerta.account_name}\n"
            f"Tipo: {alerta.tipo}\n"
            f"Mensaje: {alerta.mensaje}\n"
        )
        return self.send_message(text)

    def send_daily_report(self, summaries: list[dict], api_usage: list[dict]) -> bool:
        lines = ["\U0001f4ca <b>Reporte Diario - Monitor Solar</b>\n"]
        for s in summaries:
            lines.append(
                f"<b>{s['name']}</b>: {s['total']} sistemas | "
                f"\U0001f7e2 {s['green']} | \U0001f7e1 {s['yellow']} | "
                f"\U0001f534 {s['red']} | \u26aa {s['grey']}"
            )
        lines.append("\n\U0001f4bb <b>Uso API:</b>")
        for u in api_usage:
            lines.append(f"  {u['name']}: {u['used']}/1000 llamadas")
        return self.send_message("\n".join(lines))

    def test_connection(self) -> bool:
        try:
            url = f"{self.base_url}/getMe"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                logger.info("Telegram bot conectado: %s", data.get("result", {}).get("username", ""))
                return True
            return False
        except Exception as e:
            logger.error("Error verificando Telegram: %s", e)
            return False
