"""InfluxDB writer for APsystems time-series data.

Schema:
  Measurements:
    - system_energy: daily energy summary per system
    - ecu_power: ECU power/energy readings
    - inverter_channel_power: per-channel DC/AC power
    - inverter_telemetry: detailed DC/AC voltage, current, frequency, temperature
    - meter_energy: produced/consumed/imported/exported
    - storage_status: SOC, charge/discharge, mode

  Tags (indexed):
    - sid, eid, uid, channel, account_name

  Fields (values):
    - Numeric values from API responses
"""

import logging
from datetime import datetime, timezone
from typing import Any

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger(__name__)


class InfluxWriter:
    def __init__(self, url: str, token: str, org: str, bucket: str):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self._client = None
        self._write_api = None

    def connect(self):
        self._client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
        logger.info("InfluxDB conectado: %s (org=%s, bucket=%s)", self.url, self.org, self.bucket)

    def close(self):
        if self._client:
            self._client.close()

    def _write(self, points: list[Point]):
        if not self._write_api:
            return
        try:
            self._write_api.write(bucket=self.bucket, org=self.org, record=points)
        except Exception as e:
            logger.error("Error escribiendo a InfluxDB: %s", e)

    def write_system_energy(self, sid: str, account_name: str, summary: dict):
        now = datetime.now(timezone.utc)
        point = (
            Point("system_energy")
            .tag("sid", sid)
            .tag("account_name", account_name)
            .field("today_kwh", float(summary.get("today", 0)))
            .field("month_kwh", float(summary.get("month", 0)))
            .field("year_kwh", float(summary.get("year", 0)))
            .field("lifetime_kwh", float(summary.get("lifetime", 0)))
            .time(now, WritePrecision.S)
        )
        self._write([point])

    def write_ecu_power(self, sid: str, eid: str, account_name: str, ecu_data: dict):
        now = datetime.now(timezone.utc)
        point = (
            Point("ecu_power")
            .tag("sid", sid)
            .tag("eid", eid)
            .tag("account_name", account_name)
            .field("today_kwh", float(ecu_data.get("today", 0)))
            .field("month_kwh", float(ecu_data.get("month", 0)))
            .field("year_kwh", float(ecu_data.get("year", 0)))
            .field("lifetime_kwh", float(ecu_data.get("lifetime", 0)))
            .time(now, WritePrecision.S)
        )
        self._write([point])

    def write_batch_inverter_power(
        self, sid: str, eid: str, account_name: str, batch_data: dict
    ):
        now = datetime.now(timezone.utc)
        points = []
        time_list = batch_data.get("time", [])
        power_map = batch_data.get("power", {})

        for uid_channel, values in power_map.items():
            parts = uid_channel.rsplit("-", 1)
            if len(parts) == 2:
                uid, channel = parts
            else:
                uid, channel = uid_channel, "0"

            if values and len(values) > 0:
                last_val = values[-1]
                try:
                    power = float(last_val)
                except (ValueError, TypeError):
                    power = 0.0
            else:
                power = 0.0

            point = (
                Point("inverter_channel_power")
                .tag("sid", sid)
                .tag("eid", eid)
                .tag("uid", uid)
                .tag("channel", channel)
                .tag("account_name", account_name)
                .field("power_w", power)
                .time(now, WritePrecision.S)
            )
            points.append(point)

        self._write(points)

    def write_inverter_telemetry(
        self, sid: str, uid: str, account_name: str, telemetry: dict
    ):
        now = datetime.now(timezone.utc)
        points = []

        for ch in range(1, 5):
            dc_p = telemetry.get(f"dc_p{ch}")
            dc_i = telemetry.get(f"dc_i{ch}")
            dc_v = telemetry.get(f"dc_v{ch}")

            if dc_p is None and dc_i is None and dc_v is None:
                continue

            point = (
                Point("inverter_telemetry")
                .tag("sid", sid)
                .tag("uid", uid)
                .tag("channel", str(ch))
                .tag("account_name", account_name)
            )

            if dc_p is not None:
                try:
                    point = point.field("dc_power_w", float(dc_p))
                except (ValueError, TypeError):
                    pass
            if dc_i is not None:
                try:
                    point = point.field("dc_current_a", float(dc_i))
                except (ValueError, TypeError):
                    pass
            if dc_v is not None:
                try:
                    point = point.field("dc_voltage_v", float(dc_v))
                except (ValueError, TypeError):
                    pass

            points.append(point)

        ac_v1 = telemetry.get("ac_v1")
        ac_f = telemetry.get("ac_f")
        ac_t = telemetry.get("ac_t")
        ac_p = telemetry.get("ac_p")

        if any(v is not None for v in [ac_v1, ac_f, ac_t, ac_p]):
            point = (
                Point("inverter_telemetry")
                .tag("sid", sid)
                .tag("uid", uid)
                .tag("channel", "ac")
                .tag("account_name", account_name)
            )
            if ac_v1 is not None:
                try:
                    point = point.field("ac_voltage_v", float(ac_v1))
                except (ValueError, TypeError):
                    pass
            if ac_f is not None:
                try:
                    point = point.field("ac_frequency_hz", float(ac_f))
                except (ValueError, TypeError):
                    pass
            if ac_t is not None:
                try:
                    point = point.field("ac_temperature_c", float(ac_t))
                except (ValueError, TypeError):
                    pass
            if ac_p is not None:
                try:
                    point = point.field("ac_power_w", float(ac_p))
                except (ValueError, TypeError):
                    pass
            points.append(point)

        self._write(points)

    def write_meter_energy(
        self, sid: str, eid: str, account_name: str, meter_data: dict
    ):
        now = datetime.now(timezone.utc)
        for period in ["today", "month", "year", "lifetime"]:
            period_data = meter_data.get(period, {})
            if not period_data:
                continue
            point = (
                Point("meter_energy")
                .tag("sid", sid)
                .tag("eid", eid)
                .tag("account_name", account_name)
                .tag("period", period)
                .field("produced_kwh", float(period_data.get("produced", 0)))
                .field("consumed_kwh", float(period_data.get("consumed", 0)))
                .field("imported_kwh", float(period_data.get("imported", 0)))
                .field("exported_kwh", float(period_data.get("exported", 0)))
                .time(now, WritePrecision.S)
            )
            self._write([point])

    def write_storage_status(
        self, sid: str, eid: str, account_name: str, storage_data: dict
    ):
        now = datetime.now(timezone.utc)
        point = (
            Point("storage_status")
            .tag("sid", sid)
            .tag("eid", eid)
            .tag("account_name", account_name)
        )

        soc = storage_data.get("soc")
        if soc is not None:
            try:
                point = point.field("soc_pct", float(soc))
            except (ValueError, TypeError):
                pass

        mode = storage_data.get("mode")
        if mode is not None:
            point = point.field("mode", str(mode))

        for field in ["charge", "discharge", "produced", "consumed", "exported", "imported"]:
            val = storage_data.get(field)
            if val is not None:
                try:
                    point = point.field(f"{field}_w", float(val))
                except (ValueError, TypeError):
                    pass

        point = point.time(now, WritePrecision.S)
        self._write([point])
