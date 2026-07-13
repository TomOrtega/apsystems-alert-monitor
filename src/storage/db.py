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
