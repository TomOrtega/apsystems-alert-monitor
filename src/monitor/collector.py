"""Collects detailed metrics for monitored systems and writes to InfluxDB.

Called after run_check() to gather energy/telemetry data for monitored systems.
Respects the 1000 calls/month limit by doing a limited pass per cycle.
"""

import logging
import time
from datetime import datetime

from src.api.client import ApsystemsClient, ApsystemsApiError, ApiAccount
from src.config import AccountConfig, InfluxConfig
from src.storage.influx_writer import InfluxWriter

logger = logging.getLogger(__name__)

MAX_COLLECT_CALLS = 400
BATCH_PAUSE_SEC = 1.0


def collect_and_write(
    accounts: list[AccountConfig],
    influx_cfg: InfluxConfig,
    db,
) -> dict:
    if not influx_cfg.enabled:
        logger.info("InfluxDB deshabilitado, saltando coleccion")
        return {"calls_used": 0, "systems_collected": 0, "errors": 0}

    writer = InfluxWriter(
        url=influx_cfg.url,
        token=influx_cfg.token,
        org=influx_cfg.org,
        bucket=influx_cfg.bucket,
    )
    try:
        writer.connect()
    except Exception as e:
        logger.error("No se pudo conectar a InfluxDB: %s", e)
        return {"calls_used": 0, "systems_collected": 0, "errors": 1}

    total_calls = 0
    systems_collected = 0
    errors = 0

    for account in accounts:
        if total_calls >= MAX_COLLECT_CALLS:
            logger.warning("Limite de llamadas alcanzado (%d), deteniendo", MAX_COLLECT_CALLS)
            break

        client = ApsystemsClient(
            account=ApiAccount(
                app_id=account.app_id,
                app_secret=account.app_secret,
                base_url=account.base_url,
            )
        )

        monitored_sids = db.get_monitored_sids(account_name=account.name)
        if not monitored_sids:
            logger.info("Cuenta %s: sin sistemas monitoreados en DB", account.name)
            continue

        logger.info("Cuenta %s: recolectando datos de %d sistemas", account.name, len(monitored_sids))

        for sid in monitored_sids:
            if total_calls >= MAX_COLLECT_CALLS:
                break

            try:
                calls = _collect_system(client, sid, account.name, writer)
                total_calls += calls
                systems_collected += 1

                if systems_collected % 10 == 0:
                    time.sleep(BATCH_PAUSE_SEC)
                    logger.info(
                        "Progreso: %d/%d sistemas (%d llamadas API)",
                        systems_collected, len(monitored_sids), total_calls,
                    )

            except Exception as e:
                errors += 1
                logger.error("Error coleccionando %s: %s", sid, e)

    logger.info(
        "Recoleccion completada: %d sistemas, %d llamadas API, %d errores",
        systems_collected, total_calls, errors,
    )
    writer.close()
    return {"calls_used": total_calls, "systems_collected": systems_collected, "errors": errors}


def _collect_system(client: ApsystemsClient, sid: str, account_name: str, writer: InfluxWriter) -> int:
    calls = 0

    # 1. System energy summary
    try:
        summary = client.get_system_summary(sid)
        data = summary.get("data", summary)
        writer.write_system_energy(sid, account_name, data)
        calls += 1
    except ApsystemsApiError:
        pass
    except Exception as e:
        logger.debug("get_system_summary error %s: %s", sid, e)

    # 2. Inverters list (ECUs + UIDs)
    inverters_data = {}
    try:
        resp = client.get_system_inverters(sid)
        inverters_data = resp.get("data", resp)
        calls += 1
    except ApsystemsApiError:
        pass
    except Exception as e:
        logger.debug("get_system_inverters error %s: %s", sid, e)

    ecu_list = inverters_data if isinstance(inverters_data, list) else []
    today_str = datetime.now().strftime("%Y-%m-%d")

    for ecu in ecu_list:
        eid = ecu.get("eid", "")
        if not eid:
            continue

        # 3. ECU batch power (energy per inverter)
        try:
            batch = client.get_inverter_batch_energy(sid, eid, today_str)
            batch_data = batch.get("data", batch)
            writer.write_ecu_power(sid, eid, account_name, batch_data)
            writer.write_batch_inverter_power(sid, eid, account_name, batch_data)
            calls += 1
        except ApsystemsApiError:
            pass
        except Exception:
            pass

        # 4. Meter data
        try:
            meter = client.get_meter_summary(sid, eid)
            meter_data = meter.get("data", meter)
            writer.write_meter_energy(sid, eid, account_name, meter_data)
            calls += 1
        except ApsystemsApiError:
            pass
        except Exception:
            pass

        # 5. Storage data
        try:
            storage = client.get_storage_latest(sid, eid)
            storage_data = storage.get("data", storage)
            writer.write_storage_status(sid, eid, account_name, storage_data)
            calls += 1
        except ApsystemsApiError:
            pass
        except Exception:
            pass

        # 6. Per-inverter detailed telemetry
        for inv in ecu.get("inverter", []):
            uid = inv.get("uid", "")
            if not uid:
                continue
            try:
                inv_summary = client.get_inverter_summary(sid, uid)
                inv_data = inv_summary.get("data", inv_summary)
                writer.write_inverter_telemetry(sid, uid, account_name, inv_data)
                calls += 1
            except ApsystemsApiError:
                pass
            except Exception:
                pass

    return calls
