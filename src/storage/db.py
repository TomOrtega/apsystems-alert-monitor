import logging
import json
from datetime import datetime, date

import psycopg2
import psycopg2.extras

from src.config import DbConfig
from src.api.models import SystemInfo, Alerta, DailySummary

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, config: DbConfig):
        self.config = config
        self._conn = None

    def connect(self):
        try:
            self._conn = psycopg2.connect(self.config.dsn)
            self._conn.autocommit = True
            logger.info("Conexion a PostgreSQL establecida")
        except psycopg2.OperationalError as e:
            logger.error("Error conectando a PostgreSQL: %s", e)
            raise

    def _get_conn(self):
        if self._conn is None or self._conn.closed:
            self.connect()
        try:
            self._conn.cursor().execute("SELECT 1")
        except Exception:
            self.connect()
        return self._conn

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
            logger.info("Conexion a PostgreSQL cerrada")

    def upsert_system(self, system: SystemInfo):
        sql = """
            INSERT INTO sistemas (account_name, sid, ecu_list, light_actual, capacity, type, timezone)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (sid) DO UPDATE SET
                account_name = EXCLUDED.account_name,
                ecu_list = EXCLUDED.ecu_list,
                light_anterior = sistemas.light_actual,
                light_actual = EXCLUDED.light_actual,
                capacity = EXCLUDED.capacity,
                type = EXCLUDED.type,
                timezone = EXCLUDED.timezone,
                updated_at = NOW()
        """
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    system.account_name,
                    system.sid,
                    json.dumps(system.ecu_list),
                    system.light,
                    system.capacity,
                    system.system_type,
                    system.timezone,
                ),
            )

    def get_system_light(self, sid: str) -> int | None:
        sql = "SELECT light_actual FROM sistemas WHERE sid = %s"
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, (sid,))
            row = cur.fetchone()
            return row[0] if row else None

    def insert_alerta(self, alerta: Alerta) -> int:
        sql = """
            INSERT INTO alertas (account_name, sid, tipo, severidad, mensaje,
                                 light_anterior, light_nuevo, email_enviado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    alerta.account_name,
                    alerta.sid,
                    alerta.tipo,
                    alerta.severidad,
                    alerta.mensaje,
                    alerta.light_anterior,
                    alerta.light_nuevo,
                    alerta.email_enviado,
                ),
            )
            return cur.fetchone()[0]

    def mark_email_sent(self, alerta_id: int):
        sql = "UPDATE alertas SET email_enviado = TRUE WHERE id = %s"
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, (alerta_id,))

    def log_api_call(
        self,
        account_name: str,
        sid: str | None,
        endpoint: str,
        response_code: int,
        response_time_ms: int,
    ):
        sql = """
            INSERT INTO api_calls (account_name, sid, endpoint, response_code, response_time_ms)
            VALUES (%s, %s, %s, %s, %s)
        """
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, (account_name, sid, endpoint, response_code, response_time_ms))

    def get_calls_this_month(self, account_name: str) -> int:
        sql = """
            SELECT COUNT(*) FROM api_calls
            WHERE account_name = %s
              AND created_at >= date_trunc('month', NOW())
        """
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, (account_name,))
            return cur.fetchone()[0]

    def upsert_daily_summary(self, summary: DailySummary):
        sql = """
            INSERT INTO daily_summary
                (date, account_name, total_sistemas, green_count, yellow_count,
                 red_count, grey_count, unknown_count, api_calls_used, alertas_generadas)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date, account_name) DO UPDATE SET
                total_sistemas = EXCLUDED.total_sistemas,
                green_count = EXCLUDED.green_count,
                yellow_count = EXCLUDED.yellow_count,
                red_count = EXCLUDED.red_count,
                grey_count = EXCLUDED.grey_count,
                unknown_count = EXCLUDED.unknown_count,
                api_calls_used = EXCLUDED.api_calls_used,
                alertas_generadas = EXCLUDED.alertas_generadas
        """
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    summary.date,
                    summary.account_name,
                    summary.total_sistemas,
                    summary.green_count,
                    summary.yellow_count,
                    summary.red_count,
                    summary.grey_count,
                    summary.unknown_count,
                    summary.api_calls_used,
                    summary.alertas_generadas,
                ),
            )

    def cleanup_old_alertas(self, days: int):
        sql = "DELETE FROM alertas WHERE created_at < NOW() - INTERVAL '%s days'"
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, (days,))
            deleted = cur.rowcount
            if deleted > 0:
                logger.info("Eliminadas %d alertas antiguas (>%d dias)", deleted, days)

    def cleanup_old_api_calls(self, days: int):
        sql = "DELETE FROM api_calls WHERE created_at < NOW() - INTERVAL '%s days'"
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, (days,))
            deleted = cur.rowcount
            if deleted > 0:
                logger.info("Eliminados %d registros de API calls antiguos", deleted)

    def run_migrations(self):
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sistemas_disponibles (
                    id SERIAL PRIMARY KEY,
                    account_index INT NOT NULL,
                    sid TEXT NOT NULL,
                    account_name TEXT DEFAULT '',
                    ecu_list JSONB DEFAULT '[]',
                    capacity FLOAT DEFAULT 0,
                    system_type INT DEFAULT 1,
                    timezone TEXT DEFAULT 'UTC',
                    light INT DEFAULT 0,
                    monitorear BOOLEAN DEFAULT false,
                    discovered_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(account_index, sid)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sistemas_disponibles_account ON sistemas_disponibles(account_index)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sistemas_disponibles_monitorear ON sistemas_disponibles(monitorear)")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS ecus (
                    eid TEXT PRIMARY KEY,
                    sid TEXT NOT NULL,
                    ecu_type INT DEFAULT 0,
                    model TEXT,
                    capacity_kwh FLOAT,
                    timezone TEXT,
                    has_meter BOOLEAN DEFAULT false,
                    has_storage BOOLEAN DEFAULT false,
                    inventory_updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(eid, sid)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ecus_sid ON ecus(sid)")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS microinversores (
                    uid TEXT PRIMARY KEY,
                    eid TEXT NOT NULL,
                    sid TEXT NOT NULL,
                    inverter_model TEXT,
                    expected_channels INT DEFAULT 4,
                    inventory_updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_microinversores_sid ON microinversores(sid)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_microinversores_eid ON microinversores(eid)")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS canales_inversor (
                    id SERIAL PRIMARY KEY,
                    uid TEXT NOT NULL,
                    channel_number INT NOT NULL CHECK (channel_number BETWEEN 1 AND 4),
                    connected BOOLEAN DEFAULT true,
                    module_model TEXT,
                    module_power_w INT,
                    UNIQUE(uid, channel_number)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_canales_uid ON canales_inversor(uid)")

        logger.info("Migraciones ejecutadas correctamente")

    def insert_discover_systems(self, account_index: int, account_name: str, systems: list[dict]):
        conn = self._get_conn()
        with conn.cursor() as cur:
            for s in systems:
                cur.execute("""
                    INSERT INTO sistemas_disponibles (account_index, sid, account_name, ecu_list, capacity, system_type, timezone, light, monitorear)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
                    ON CONFLICT (account_index, sid) DO UPDATE SET
                        account_name = EXCLUDED.account_name,
                        ecu_list = EXCLUDED.ecu_list,
                        capacity = EXCLUDED.capacity,
                        system_type = EXCLUDED.system_type,
                        timezone = EXCLUDED.timezone,
                        light = EXCLUDED.light,
                        monitorear = true,
                        discovered_at = NOW()
                """, (account_index, s["sid"], account_name, json.dumps(s.get("ecu_list", [])), s.get("capacity", 0), s.get("system_type", 1), s.get("timezone", "UTC"), s.get("light", 0)))

    def get_discovered_systems(self, account_index: int) -> list[dict]:
        sql = "SELECT id, sid, account_name, ecu_list, capacity, system_type, timezone, light, monitorear, discovered_at FROM sistemas_disponibles WHERE account_index = %s ORDER BY sid"
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, (account_index,))
            def _parse_ecu(val):
                if not val:
                    return []
                if isinstance(val, (list, dict)):
                    return val
                return json.loads(val)

            return [{"id": r[0], "sid": r[1], "account_name": r[2], "ecu_list": _parse_ecu(r[3]), "capacity": r[4], "system_type": r[5], "timezone": r[6], "light": r[7], "monitorear": r[8], "discovered_at": r[9].isoformat() if r[9] else None} for r in cur.fetchall()]

    def update_monitored_systems(self, account_index: int, sids: list[str]):
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute("UPDATE sistemas_disponibles SET monitorear = false WHERE account_index = %s", (account_index,))
            for sid in sids:
                cur.execute("UPDATE sistemas_disponibles SET monitorear = true WHERE account_index = %s AND sid = %s", (account_index, sid))

    def get_monitored_sids(self, account_index: int) -> list[str]:
        sql = "SELECT sid FROM sistemas_disponibles WHERE account_index = %s AND monitorear = true ORDER BY sid"
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, (account_index,))
            return [r[0] for r in cur.fetchall()]

    def upsert_inventory(self, sid: str, details: dict, inverters_data: list, meters_data: list, storages_data):
        conn = self._get_conn()
        ecu_ids_in_details = details.get("ecu", [])

        has_meter = False
        meter_eids = set()
        if isinstance(meters_data, list):
            meter_eids = set(meters_data)
            has_meter = len(meter_eids) > 0

        has_storage = False
        storage_eids = set()
        if isinstance(storages_data, list):
            storage_eids = set(storages_data)
            has_storage = len(storage_eids) > 0

        with conn.cursor() as cur:
            for ecu in inverters_data:
                eid = ecu.get("eid", "")
                ecu_type = ecu.get("type", 0)
                model = ecu.get("model")
                capacity_kwh = ecu.get("capacity")
                tz = ecu.get("timezone", details.get("timezone", "UTC"))
                ecu_has_meter = eid in meter_eids
                ecu_has_storage = eid in storage_eids

                cur.execute("""
                    INSERT INTO ecus (eid, sid, ecu_type, model, capacity_kwh, timezone, has_meter, has_storage, inventory_updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (eid, sid) DO UPDATE SET
                        ecu_type = EXCLUDED.ecu_type,
                        model = EXCLUDED.model,
                        capacity_kwh = EXCLUDED.capacity_kwh,
                        timezone = EXCLUDED.timezone,
                        has_meter = EXCLUDED.has_meter,
                        has_storage = EXCLUDED.has_storage,
                        inventory_updated_at = NOW()
                """, (eid, sid, ecu_type, model, capacity_kwh, tz, ecu_has_meter, ecu_has_storage))

                for inv in ecu.get("inverter", []):
                    uid = inv.get("uid", "")
                    inv_model = inv.get("type", "")

                    cur.execute("""
                        INSERT INTO microinversores (uid, eid, sid, inverter_model, inventory_updated_at)
                        VALUES (%s, %s, %s, %s, NOW())
                        ON CONFLICT (uid) DO UPDATE SET
                            eid = EXCLUDED.eid,
                            sid = EXCLUDED.sid,
                            inverter_model = EXCLUDED.inverter_model,
                            inventory_updated_at = NOW()
                    """, (uid, eid, sid, inv_model))

                    for ch in range(1, 5):
                        cur.execute("""
                            INSERT INTO canales_inversor (uid, channel_number, connected)
                            VALUES (%s, %s, true)
                            ON CONFLICT (uid, channel_number) DO UPDATE SET connected = true
                        """, (uid, ch))

    def get_inventory_summary(self, sid: str) -> dict:
        conn = self._get_conn()
        result = {"sid": sid, "ecus": [], "total_inverters": 0, "total_channels": 0}

        with conn.cursor() as cur:
            cur.execute("SELECT eid, ecu_type, model, capacity_kwh, timezone, has_meter, has_storage FROM ecus WHERE sid = %s", (sid,))
            ecus = cur.fetchall()
            for ecu in ecus:
                eid, etype, model, cap, tz, hm, hs = ecu
                cur.execute("SELECT uid, inverter_model FROM microinversores WHERE eid = %s AND sid = %s", (eid, sid))
                inverters = cur.fetchall()
                inv_list = []
                for uid, imodel in inverters:
                    cur.execute("SELECT channel_number, connected FROM canales_inversor WHERE uid = %s ORDER BY channel_number", (uid,))
                    channels = cur.fetchall()
                    inv_list.append({"uid": uid, "model": imodel, "channels": [{"number": c[0], "connected": c[1]} for c in channels]})
                result["ecus"].append({
                    "eid": eid, "type": etype, "model": model, "capacity_kwh": cap,
                    "timezone": tz, "has_meter": hm, "has_storage": hs,
                    "inverters": inv_list,
                })
                result["total_inverters"] += len(inv_list)
                result["total_channels"] += sum(len(inv["channels"]) for inv in inv_list)

        return result

    def get_inventory_stats(self) -> dict:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM ecus")
            ecu_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM microinversores")
            inv_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM canales_inversor WHERE connected = true")
            ch_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT sid) FROM ecus")
            sys_count = cur.fetchone()[0]
        return {"sistemas": sys_count, "ecus": ecu_count, "microinversores": inv_count, "canales": ch_count}
