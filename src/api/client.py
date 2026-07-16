import hmac
import hashlib
import base64
import time
import uuid
import logging
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger(__name__)

SIGNATURE_METHOD = "HmacSHA256"


@dataclass
class ApiAccount:
    app_id: str
    app_secret: str
    base_url: str


class ApsystemsApiError(Exception):
    def __init__(self, code: int, message: str, path: str):
        self.code = code
        self.message = message
        self.path = path
        super().__init__(f"API error {code}: {message} on {path}")


class ApsystemsClient:
    def __init__(self, account: ApiAccount):
        self.account = account
        self._session = requests.Session()

    def _build_signature(self, path: str, method: str) -> dict[str, str]:
        ts = str(int(time.time() * 1000))
        nonce = uuid.uuid4().hex
        request_path = path.rsplit("/", 1)[-1]
        string_to_sign = "/".join(
            [ts, nonce, self.account.app_id, request_path, method.upper(), SIGNATURE_METHOD]
        )
        sig_bytes = hmac.new(
            self.account.app_secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        signature = base64.b64encode(sig_bytes).decode("utf-8")
        return {
            "X-CA-AppId": self.account.app_id,
            "X-CA-Timestamp": ts,
            "X-CA-Nonce": nonce,
            "X-CA-Signature-Method": SIGNATURE_METHOD,
            "X-CA-Signature": signature,
        }

    def _request(
        self, path: str, method: str = "GET",
        params: dict | None = None,
        body: dict | None = None,
    ) -> dict[str, Any]:
        url = self.account.base_url + path
        headers = self._build_signature(path, method)
        if body:
            headers["Content-Type"] = "application/json"

        start = time.time()
        try:
            kwargs = dict(method=method, url=url, headers=headers, timeout=30)
            if params:
                kwargs["params"] = params
            if body:
                kwargs["json"] = body
            resp = self._session.request(**kwargs)
            elapsed_ms = int((time.time() - start) * 1000)

            if resp.status_code != 200:
                body_text = resp.text[:500]
                logger.error("API HTTP %d: %s %s -> body: %s", resp.status_code, method, path, body_text)
                resp.raise_for_status()

        except requests.RequestException as e:
            logger.error("Request failed: %s %s -> %s", method, path, e)
            raise

        data = resp.json()
        code = data.get("code", -1)

        if code != 0:
            raise ApsystemsApiError(code, f"code={code}, msg={data.get('msg', '')}", path)

        logger.debug("API %s %s -> %d (%dms)", method, path, resp.status_code, elapsed_ms)
        return data

    def get_systems_batch(self, page: int = 1, size: int = 50) -> dict[str, Any]:
        """List all systems via Installer API (POST, no body).
        Returns: {"total": N, "size": N, "systems": [...]}
        """
        resp = self._request(
            "/installer/api/v2/systems",
            method="POST",
        )
        return resp.get("data", resp)

    def get_system_details(self, sid: str) -> dict[str, Any]:
        return self._request(f"/installer/api/v2/systems/details/{sid}")

    def get_system_inverters(self, sid: str) -> dict[str, Any]:
        return self._request(f"/installer/api/v2/systems/inverters/{sid}")

    def get_system_summary(self, sid: str) -> dict[str, Any]:
        return self._request(f"/installer/api/v2/systems/summary/{sid}")

    def get_system_energy(self, sid: str, energy_level: str, date_range: str) -> dict[str, Any]:
        """Get system energy data.
        energy_level: "hourly", "daily", "monthly", "yearly"
        date_range: "YYYY-MM-DD" or "YYYY-MM-DD YYYY-MM-DD"
        """
        return self._request(
            f"/installer/api/v2/systems/energy/{sid}",
            params={"energy_level": energy_level, "date_range": date_range},
        )

    def get_ecu_summary(self, sid: str, eid: str) -> dict[str, Any]:
        return self._request(f"/installer/api/v2/systems/{sid}/devices/ecu/summary/{eid}")

    def get_inverter_batch_energy(
        self, sid: str, eid: str, date_range: str
    ) -> dict[str, Any]:
        return self._request(
            f"/installer/api/v2/systems/{sid}/devices/inverter/batch/energy/{eid}",
            params={"energy_level": "power", "date_range": date_range},
        )

    def get_inverter_energy(
        self, sid: str, uid: str, energy_level: str, date_range: str
    ) -> dict[str, Any]:
        return self._request(
            f"/installer/api/v2/systems/{sid}/devices/inverter/energy/{uid}",
            params={"energy_level": energy_level, "date_range": date_range},
        )
