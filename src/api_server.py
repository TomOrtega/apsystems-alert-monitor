import os
import json
import logging
from datetime import datetime, date
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import DbConfig, AccountConfig
from src.storage.db import Database

logger = logging.getLogger(__name__)

LOG_FILE = Path("/app/logs/monitor.log")


def _get_db() -> Database:
    db = Database(DbConfig(
        host=os.getenv("DB_HOST", "postgres"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "apsystems"),
        password=os.getenv("DB_PASSWORD", "changeme"),
        name=os.getenv("DB_NAME", "apsystems_monitor"),
    ))
    db.connect()
    return db


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        db = _get_db()
        db.run_migrations()
        db.close()
    except Exception as e:
        logger.warning("Error ejecutando migraciones: %s", e)
    yield


app = FastAPI(title="APsystems Monitor API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConfigUpdate(BaseModel):
    value: str


class SystemRename(BaseModel):
    nombre: str


class AccountData(BaseModel):
    name: str = ""
    app_id: str = ""
    app_secret: str = ""
    base_url: str = "https://api.apsystemsema.com:9282"
    systems: str = ""


class SmtpData(BaseModel):
    enabled: str = "true"
    host: str = "smtp.office365.com"
    port: str = "587"
    user: str = ""
    password: str = ""
    from_addr: str = ""
    alert_to: str = ""


class TelegramData(BaseModel):
    enabled: str = "false"
    bot_token: str = ""
    chat_id: str = ""


class SchedulerData(BaseModel):
    check_interval_hours: str = "24"
    alert_retention_days: str = "90"


class MonitoredSystemsData(BaseModel):
    sids: list[str]


LIGHT_LABELS = {1: "Normal", 2: "Alarma inversor", 3: "ECU offline", 4: "Sin datos"}
LIGHT_COLORS = {1: "green", 2: "yellow", 3: "red", 4: "grey"}


@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/dashboard")
def dashboard():
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT sid, account_name, light_actual, updated_at FROM sistemas ORDER BY sid")
            systems = [{"sid": r[0], "account_name": r[1], "light": r[2], "updated_at": r[3].isoformat() if r[3] else None} for r in cur.fetchall()]

            counts = {"green": 0, "yellow": 0, "red": 0, "grey": 0, "unknown": 0}
            for s in systems:
                key = LIGHT_COLORS.get(s["light"], "unknown")
                counts[key] += 1

            cur.execute("SELECT id, sid, account_name, tipo, severidad, mensaje, light_anterior, light_nuevo, created_at FROM alertas ORDER BY created_at DESC LIMIT 10")
            recent_alertas = [{"id": r[0], "sid": r[1], "account_name": r[2], "tipo": r[3], "severidad": r[4], "mensaje": r[5], "light_anterior": r[6], "light_nuevo": r[7], "created_at": r[8].isoformat() if r[8] else None} for r in cur.fetchall()]

            cur.execute("SELECT account_name, COUNT(*) FROM api_calls WHERE created_at >= date_trunc('month', NOW()) GROUP BY account_name")
            api_usage = {r[0]: r[1] for r in cur.fetchall()}

            cur.execute("SELECT COUNT(*) FROM alertas WHERE created_at >= NOW() - INTERVAL '24 hours'")
            alertas_24h = cur.fetchone()[0]

        return {
            "sistemas": systems,
            "counts": counts,
            "recent_alertas": recent_alertas,
            "api_usage": api_usage,
            "alertas_24h": alertas_24h,
            "total_sistemas": len(systems),
        }
    finally:
        db.close()


@app.get("/api/sistemas")
def get_sistemas(
    cuenta: str | None = Query(None),
    estado: str | None = Query(None),
):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            sql = "SELECT id, sid, account_name, light_actual, light_anterior, capacity, type, timezone, updated_at FROM sistemas"
            conditions = []
            params = []
            if cuenta:
                conditions.append("account_name = %s")
                params.append(cuenta)
            if estado:
                light_val = {"green": 1, "yellow": 2, "red": 3, "grey": 4}.get(estado)
                if light_val:
                    conditions.append("light_actual = %s")
                    params.append(light_val)
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY sid"
            cur.execute(sql, params)
            return [{"id": r[0], "sid": r[1], "account_name": r[2], "light": r[3], "light_anterior": r[4], "capacity": r[5], "type": r[6], "timezone": r[7], "updated_at": r[8].isoformat() if r[8] else None} for r in cur.fetchall()]
    finally:
        db.close()


@app.get("/api/sistemas/{sid}")
def get_sistema(sid: str):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT id, sid, account_name, light_actual, light_anterior, capacity, type, timezone, ecu_list, created_at, updated_at FROM sistemas WHERE sid = %s", (sid,))
            r = cur.fetchone()
            if not r:
                raise HTTPException(status_code=404, detail="Sistema no encontrado")
            return {"id": r[0], "sid": r[1], "account_name": r[2], "light": r[3], "light_anterior": r[4], "capacity": r[5], "type": r[6], "timezone": r[7], "ecu_list": json.loads(r[8]) if r[8] else [], "created_at": r[9].isoformat() if r[9] else None, "updated_at": r[10].isoformat() if r[10] else None}
    finally:
        db.close()


@app.put("/api/sistemas/{sid}/nombre")
def rename_sistema(sid: str, data: SystemRename):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("UPDATE sistemas SET capacity = %s WHERE sid = %s", (data.nombre, sid))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Sistema no encontrado")
        return {"ok": True}
    finally:
        db.close()


@app.delete("/api/sistemas/{sid}")
def delete_sistema(sid: str):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sistemas WHERE sid = %s", (sid,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Sistema no encontrado")
        return {"ok": True}
    finally:
        db.close()


@app.get("/api/alertas")
def get_alertas(
    severidad: str | None = Query(None),
    sid: str | None = Query(None),
    cuenta: str | None = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            sql = "SELECT id, sid, account_name, tipo, severidad, mensaje, light_anterior, light_nuevo, email_enviado, created_at FROM alertas"
            conditions = []
            params = []
            if severidad:
                conditions.append("severidad = %s")
                params.append(severidad)
            if sid:
                conditions.append("sid = %s")
                params.append(sid)
            if cuenta:
                conditions.append("account_name = %s")
                params.append(cuenta)
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            cur.execute(sql, params)
            rows = cur.fetchall()

            count_sql = "SELECT COUNT(*) FROM alertas"
            if conditions:
                count_sql += " WHERE " + " AND ".join(conditions[:len(conditions)])
            cur.execute(count_sql, params[:len(conditions)])
            total = cur.fetchone()[0]

            return {
                "alertas": [{"id": r[0], "sid": r[1], "account_name": r[2], "tipo": r[3], "severidad": r[4], "mensaje": r[5], "light_anterior": r[6], "light_nuevo": r[7], "email_enviado": r[8], "created_at": r[9].isoformat() if r[9] else None} for r in rows],
                "total": total,
            }
    finally:
        db.close()


@app.get("/api/reportes")
def get_reportes(
    dias: int = Query(30),
):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT date, account_name, total_sistemas, green_count, yellow_count,
                       red_count, grey_count, unknown_count, api_calls_used, alertas_generadas
                FROM daily_summary
                WHERE date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY date DESC, account_name
            """, (dias,))
            return [{"date": r[0].isoformat() if r[0] else None, "account_name": r[1], "total_sistemas": r[2], "green_count": r[3], "yellow_count": r[4], "red_count": r[5], "grey_count": r[6], "unknown_count": r[7], "api_calls_used": r[8], "alertas_generadas": r[9]} for r in cur.fetchall()]
    finally:
        db.close()


@app.get("/api/config/{section}")
def get_config(section: str):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT key, value, value_type, description FROM config WHERE section = %s ORDER BY id", (section,))
            rows = cur.fetchall()
            if not rows:
                raise HTTPException(status_code=404, detail=f"Seccion '{section}' no encontrada")
            return {r[0]: {"value": r[1], "type": r[2], "description": r[3]} for r in rows}
    finally:
        db.close()


@app.get("/api/config")
def get_all_config():
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT section, key, value, value_type, description FROM config ORDER BY section, id")
            result = {}
            for r in cur.fetchall():
                sec = r[0]
                if sec not in result:
                    result[sec] = {}
                result[sec][r[1]] = {"value": r[2], "type": r[3], "description": r[4]}
            return result
    finally:
        db.close()


@app.put("/api/config/{section}/{key}")
def update_config(section: str, key: str, data: ConfigUpdate):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("UPDATE config SET value = %s, updated_at = NOW() WHERE section = %s AND key = %s", (data.value, section, key))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Config no encontrada")
        return {"ok": True}
    finally:
        db.close()


@app.put("/api/config/accounts")
def update_accounts(accounts: list[AccountData]):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM config WHERE section = 'accounts'")
            for i, acc in enumerate(accounts, 1):
                prefix = f"account{i}"
                for k, v in [("name", acc.name), ("app_id", acc.app_id), ("app_secret", acc.app_secret), ("base_url", acc.base_url), ("systems", acc.systems)]:
                    ctype = "password" if "secret" in k else "text"
                    cur.execute(
                        "INSERT INTO config (section, key, value, value_type, description) VALUES (%s, %s, %s, %s, %s)",
                        ("accounts", f"{prefix}_{k}", v, ctype, f"{k} de cuenta {i}"),
                    )
        return {"ok": True}
    finally:
        db.close()


@app.put("/api/config/smtp")
def update_smtp(data: SmtpData):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            for k, v in [("enabled", data.enabled), ("host", data.host), ("port", data.port), ("user", data.user), ("password", data.password), ("from_addr", data.from_addr), ("alert_to", data.alert_to)]:
                ctype = "password" if k == "password" else ("boolean" if k == "enabled" else "text")
                cur.execute(
                    "INSERT INTO config (section, key, value, value_type, updated_at) VALUES (%s, %s, %s, %s, NOW()) ON CONFLICT (section, key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()",
                    ("smtp", k, v, ctype),
                )
        return {"ok": True}
    finally:
        db.close()


@app.put("/api/config/telegram")
def update_telegram(data: TelegramData):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            for k, v in [("enabled", data.enabled), ("bot_token", data.bot_token), ("chat_id", data.chat_id)]:
                ctype = "password" if k == "bot_token" else ("boolean" if k == "enabled" else "text")
                cur.execute(
                    "INSERT INTO config (section, key, value, value_type, updated_at) VALUES (%s, %s, %s, %s, NOW()) ON CONFLICT (section, key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()",
                    ("telegram", k, v, ctype),
                )
        return {"ok": True}
    finally:
        db.close()


@app.put("/api/config/scheduler")
def update_scheduler(data: SchedulerData):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            for k, v in [("check_interval_hours", data.check_interval_hours), ("alert_retention_days", data.alert_retention_days)]:
                cur.execute(
                    "INSERT INTO config (section, key, value, value_type, updated_at) VALUES (%s, %s, %s, %s, NOW()) ON CONFLICT (section, key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()",
                    ("scheduler", k, v, "integer"),
                )
        return {"ok": True}
    finally:
        db.close()


@app.post("/api/check")
def trigger_check():
    db = _get_db()
    try:
        from src.config import AccountConfig, load_config_from_db
        config = load_config_from_db(db)
        from src.monitor.checker import run_check
        alertas = run_check(config.accounts, db)
        return {"ok": True, "alertas_generadas": len(alertas)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/logs")
def get_logs(lines: int = Query(100)):
    try:
        if LOG_FILE.exists():
            with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
                return {"logs": [l.rstrip() for l in all_lines[-lines:]], "total": len(all_lines)}
        return {"logs": [], "total": 0}
    except Exception as e:
        return {"logs": [f"Error reading logs: {e}"], "total": 0}


@app.delete("/api/logs")
def clear_logs():
    try:
        if LOG_FILE.exists():
            with open(LOG_FILE, "w") as f:
                f.write("")
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/accounts")
def get_accounts():
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT key, value FROM config WHERE section = 'accounts' ORDER BY id")
            raw = {r[0]: r[1] for r in cur.fetchall()}
            accounts = []
            i = 1
            while True:
                prefix = f"account{i}"
                if f"{prefix}_app_id" not in raw:
                    break
                accounts.append({
                    "index": i,
                    "name": raw.get(f"{prefix}_name", ""),
                    "app_id": raw.get(f"{prefix}_app_id", ""),
                    "app_secret": raw.get(f"{prefix}_app_secret", ""),
                    "base_url": raw.get(f"{prefix}_base_url", ""),
                    "systems": raw.get(f"{prefix}_systems", ""),
                })
                i += 1
            return accounts
    finally:
        db.close()


@app.post("/api/accounts")
def add_account(acc: AccountData):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(CAST(SUBSTRING(key FROM 8) AS INT)) FROM config WHERE section = 'accounts' AND key LIKE 'account%_app_id'")
            max_idx = cur.fetchone()[0] or 0
            new_idx = max_idx + 1
            prefix = f"account{new_idx}"
            for k, v in [("name", acc.name), ("app_id", acc.app_id), ("app_secret", acc.app_secret), ("base_url", acc.base_url), ("systems", acc.systems)]:
                ctype = "password" if "secret" in k else "text"
                cur.execute(
                    "INSERT INTO config (section, key, value, value_type, description) VALUES (%s, %s, %s, %s, %s)",
                    ("accounts", f"{prefix}_{k}", v, ctype, f"{k} de cuenta {new_idx}"),
                )
        return {"ok": True, "index": new_idx}
    finally:
        db.close()


@app.delete("/api/accounts/{index}")
def delete_account(index: int):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            prefix = f"account{index}"
            cur.execute("DELETE FROM config WHERE section = 'accounts' AND key LIKE %s", (f"{prefix}_%",))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Cuenta no encontrada")
        return {"ok": True}
    finally:
        db.close()


@app.post("/api/accounts/{index}/test")
def test_account_api(index: int):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT key, value FROM config WHERE section = 'accounts' ORDER BY id")
            raw = {r[0]: r[1] for r in cur.fetchall()}

        prefix = f"account{index}"
        app_id = raw.get(f"{prefix}_app_id", "")
        if not app_id:
            raise HTTPException(status_code=404, detail=f"Cuenta {index} no encontrada")

        app_secret = raw.get(f"{prefix}_app_secret", "")
        base_url = raw.get(f"{prefix}_base_url", "https://api.apsystemsema.com:9282")

        if not app_id or not app_secret:
            raise HTTPException(status_code=400, detail="App ID y App Secret son obligatorios")

        from src.api.client import ApsystemsClient, ApiAccount
        client = ApsystemsClient(account=ApiAccount(app_id=app_id, app_secret=app_secret, base_url=base_url))

        try:
            data = client.get_systems_batch(page=1, size=1)
            total = data.get("total", 0)
            systems = data.get("systems", data.get("data", []))
            sample = systems[0] if systems else {}
            return {
                "ok": True,
                "message": f"Autenticacion exitosa. {total} sistemas encontrados en la cuenta.",
                "total_systems": total,
                "sample_sid": sample.get("sid", ""),
                "sample_capacity": sample.get("capacity", ""),
            }
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                raise HTTPException(status_code=401, detail="Credenciales invalidas - verifica App ID y App Secret")
            elif "403" in error_msg or "Forbidden" in error_msg:
                raise HTTPException(status_code=403, detail="Acceso denegado - verifica los permisos de la cuenta")
            elif "500" in error_msg:
                raise HTTPException(status_code=502, detail=f"Error del servidor APsystems: {error_msg}")
            else:
                raise HTTPException(status_code=500, detail=f"Error conectando con APsystems: {error_msg}")

    finally:
        db.close()


@app.post("/api/test/smtp")
def test_smtp():
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT key, value FROM config WHERE section = 'smtp'")
            raw = {r[0]: r[1] for r in cur.fetchall()}
        db.close()

        host = raw.get("host", "")
        port = int(raw.get("port", "587"))
        user = raw.get("user", "")
        password = raw.get("password", "")
        from_addr = raw.get("from_addr", "")
        alert_to = raw.get("alert_to", "")

        if not all([host, user, password, alert_to]):
            raise HTTPException(status_code=400, detail="Faltan campos SMTP (host, user, password, alert_to)")

        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText("Test de APsystems Monitor - SMTP configurado correctamente")
        msg["Subject"] = "Test APsystems Monitor"
        msg["From"] = from_addr or user
        msg["To"] = alert_to

        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(msg["From"], [alert_to], msg.as_string())

        return {"ok": True, "message": f"Email de prueba enviado a {alert_to}"}
    except HTTPException:
        raise
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=400, detail="Error de autenticacion SMTP - verifica usuario y password")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error SMTP: {str(e)}")


@app.post("/api/test/telegram")
def test_telegram():
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT key, value FROM config WHERE section = 'telegram'")
            raw = {r[0]: r[1] for r in cur.fetchall()}
        db.close()

        bot_token = raw.get("bot_token", "")
        chat_id = raw.get("chat_id", "")

        if not bot_token or not chat_id:
            raise HTTPException(status_code=400, detail="Faltan Bot Token o Chat ID")

        from src.notify.telegram_sender import TelegramSender
        tg = TelegramSender(bot_token, chat_id)

        if tg.test_connection():
            tg.send_message("Test de APsystems Monitor - Telegram configurado correctamente")
            return {"ok": True, "message": "Mensaje de prueba enviado a Telegram"}
        else:
            raise HTTPException(status_code=400, detail="No se pudo conectar al bot de Telegram - verifica el token")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error Telegram: {str(e)}")


@app.post("/api/accounts/{index}/discover")
def discover_systems(index: int):
    db = _get_db()
    try:
        conn = db._get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT key, value FROM config WHERE section = 'accounts' ORDER BY id")
            raw = {r[0]: r[1] for r in cur.fetchall()}

        prefix = f"account{index}"
        app_id = raw.get(f"{prefix}_app_id", "")
        if not app_id:
            raise HTTPException(status_code=404, detail=f"Cuenta {index} no encontrada")

        account = AccountConfig(
            name=raw.get(f"{prefix}_name", ""),
            app_id=app_id,
            app_secret=raw.get(f"{prefix}_app_secret", ""),
            base_url=raw.get(f"{prefix}_base_url", "https://api.apsystemsema.com:9282"),
            systems=[],
        )

        from src.monitor.batch import discover_systems as _discover
        systems, calls_used = _discover(account)

        db.insert_discover_systems(index, account.name, systems)

        db.log_api_call(account.name, None, "/installer/api/v2/systems", 200, 0)

        return {"ok": True, "total": len(systems), "calls_used": calls_used, "systems": systems}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error descubriendo sistemas: {str(e)}")
    finally:
        db.close()


@app.get("/api/accounts/{index}/systems")
def get_discovered_systems(index: int):
    db = _get_db()
    try:
        systems = db.get_discovered_systems(index)
        return systems
    finally:
        db.close()


@app.put("/api/accounts/{index}/systems")
def update_monitored_systems(index: int, data: MonitoredSystemsData):
    db = _get_db()
    try:
        db.update_monitored_systems(index, data.sids)
        return {"ok": True, "monitored": len(data.sids)}
    finally:
        db.close()


class AddSidData(BaseModel):
    sid: str
    account_name: str = ""


@app.post("/api/accounts/{index}/systems/add")
def add_system_manually(index: int, data: AddSidData):
    db = _get_db()
    try:
        sid = data.sid.strip()
        if not sid:
            raise HTTPException(status_code=400, detail="SID vacio")
        db.insert_discover_systems(index, data.account_name or f"Account {index}", [{"sid": sid, "ecu_list": [], "capacity": 0, "system_type": 1, "timezone": "UTC", "light": 0}])
        return {"ok": True, "sid": sid}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding SID: {str(e)}")
    finally:
        db.close()


@app.post("/api/check")
def trigger_check():
    try:
        from src.config import load_config
        from src.monitor.checker import run_check
        config = load_config()
        db = _get_db()
        try:
            alertas = run_check(config.accounts, db)
            return {"ok": True, "alertas_generadas": len(alertas)}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en check: {str(e)}")


@app.post("/api/report/manual")
def manual_report():
    db = _get_db()
    try:
        from src.config import load_config
        config = load_config()

        report = {"accounts": [], "generated_at": datetime.now().isoformat(), "api_calls_used": 0}

        for account in config.accounts:
            if not account.app_id:
                continue

            account_report = {
                "name": account.name,
                "systems": [],
                "summary": {"total": 0, "green": 0, "yellow": 0, "red": 0, "grey": 0},
            }

            try:
                from src.api.client import ApsystemsClient, ApiAccount
                client = ApsystemsClient(account=ApiAccount(
                    app_id=account.app_id,
                    app_secret=account.app_secret,
                    base_url=account.base_url,
                ))

                batch_data = client.get_systems_batch(page=1, size=50)
                report["api_calls_used"] += 1
                all_systems = batch_data.get("systems", batch_data.get("data", []))

                monitored_sids = set(account.systems)

                for sys_data in all_systems:
                    sid = sys_data.get("sid", "")
                    if not sid or sid not in monitored_sids:
                        continue

                    system_report = {
                        "sid": sid,
                        "light": sys_data.get("light", 0),
                        "ecu_list": sys_data.get("ecu", []),
                        "capacity": sys_data.get("capacity", 0),
                        "type": sys_data.get("type", 1),
                        "timezone": sys_data.get("timezone", "UTC"),
                        "details": None,
                        "summary": None,
                        "energy": None,
                    }

                    light = sys_data.get("light", 0)
                    light_key = {1: "green", 2: "yellow", 3: "red", 4: "grey"}.get(light, "unknown")
                    account_report["summary"]["total"] += 1
                    if light_key in account_report["summary"]:
                        account_report["summary"][light_key] += 1

                    try:
                        details = client.get_system_details(sid)
                        report["api_calls_used"] += 1
                        system_report["details"] = details.get("data", {})
                    except Exception:
                        pass

                    try:
                        summary = client.get_system_summary(sid)
                        report["api_calls_used"] += 1
                        system_report["summary"] = summary.get("data", {})
                    except Exception:
                        pass

                    try:
                        today = datetime.now().strftime("%Y-%m-%d")
                        yesterday = (datetime.now() - __import__('datetime').timedelta(days=1)).strftime("%Y-%m-%d")
                        ecu_list = sys_data.get("ecu", [])
                        eid = ecu_list[0] if ecu_list else ""
                        if eid:
                            energy = client.get_inverter_batch_energy(sid, eid, f"{yesterday} {today}")
                            report["api_calls_used"] += 1
                            system_report["energy"] = energy.get("data", {})
                    except Exception:
                        pass

                    account_report["systems"].append(system_report)

            except Exception as e:
                account_report["error"] = str(e)

            report["accounts"].append(account_report)

        return report
    finally:
        db.close()
