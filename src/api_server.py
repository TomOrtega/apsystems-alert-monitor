import os
import json
import logging
import subprocess
from datetime import datetime, date
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import DbConfig
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
