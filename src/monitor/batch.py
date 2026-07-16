import logging
import time

from src.api.client import ApsystemsClient, ApsystemsApiError, ApiAccount
from src.api.models import SystemInfo
from src.config import AccountConfig

logger = logging.getLogger(__name__)


def fetch_all_systems(account: AccountConfig) -> tuple[list[SystemInfo], int]:
    client = ApsystemsClient(
        account=ApiAccount(
            app_id=account.app_id,
            app_secret=account.app_secret,
            base_url=account.base_url,
        )
    )

    systems = []
    calls_used = 0
    page = 1
    page_size = 50

    while True:
        try:
            start = time.time()
            data = client.get_systems_batch(page=page, size=page_size)
            elapsed_ms = int((time.time() - start) * 1000)
            calls_used += 1

            items = data.get("systems", data.get("data", []))
            if not items:
                break

            for item in items:
                sid = item.get("sid", "")
                if sid and sid in account.systems:
                    systems.append(
                        SystemInfo(
                            sid=sid,
                            account_name=account.name,
                            light=item.get("light"),
                            ecu_list=item.get("ecu", []),
                            capacity=item.get("capacity", ""),
                            system_type=item.get("type", 1),
                            timezone=item.get("timezone", "UTC"),
                        )
                    )

            total = data.get("total", 0)
            if page * page_size >= total:
                break
            page += 1

        except ApsystemsApiError as e:
            logger.error("API error fetching batch page %d: %s", page, e)
            break
        except Exception as e:
            logger.error("Unexpected error fetching batch: %s", e)
            break

    logger.info(
        "Cuenta %s: %d sistemas obtenidos en %d llamadas API",
        account.name,
        len(systems),
        calls_used,
    )
    return systems, calls_used


def discover_systems(account: AccountConfig) -> tuple[list[dict], int]:
    client = ApsystemsClient(
        account=ApiAccount(
            app_id=account.app_id,
            app_secret=account.app_secret,
            base_url=account.base_url,
        )
    )

    systems = []
    calls_used = 0
    page = 1
    page_size = 50

    while True:
        try:
            data = client.get_systems_batch(page=page, size=page_size)
            calls_used += 1

            items = data.get("systems", data.get("data", []))
            if not items:
                break

            for item in items:
                sid = item.get("sid", "")
                if sid:
                    systems.append({
                        "sid": sid,
                        "light": item.get("light", 0),
                        "ecu_list": item.get("ecu", []),
                        "capacity": item.get("capacity", 0),
                        "system_type": item.get("type", 1),
                        "timezone": item.get("timezone", "UTC"),
                        "username": item.get("username", ""),
                    })

            total = data.get("total", 0)
            if page * page_size >= total:
                break
            page += 1

        except ApsystemsApiError as e:
            logger.error("API error discovering page %d: %s", page, e)
            break
        except Exception as e:
            logger.error("Unexpected error discovering: %s", e)
            break

    logger.info("Cuenta %s: %d sistemas descubiertos en %d llamadas API", account.name, len(systems), calls_used)
    return systems, calls_used
