#!/usr/bin/env python3
"""
Test con SIDs reales de la API Installer.
POST /installer/api/v2/systems para listar, luego detalles/summary con SID correcto.
"""
import asyncio, aiohttp, time, uuid, hmac, hashlib, base64, json

APP_ID     = "2c9f934a9f49a1fb019f64766c1c7965"
APP_SECRET = "64766c1b7964"
BASE_URL   = "https://api.apsystemsema.com:9282"
SIG_METHOD = "HmacSHA256"

def build_headers(path, method="GET"):
    ts = str(int(time.time() * 1000))
    nonce = uuid.uuid4().hex
    request_path = path.rsplit("/", 1)[-1]
    s2s = "/".join([ts, nonce, APP_ID, request_path, method.upper(), SIG_METHOD])
    sig = base64.b64encode(hmac.new(APP_SECRET.encode(), s2s.encode(), hashlib.sha256).digest()).decode()
    return {
        "Content-Type": "application/json",
        "X-CA-AppId": APP_ID,
        "X-CA-Timestamp": ts,
        "X-CA-Nonce": nonce,
        "X-CA-Signature-Method": SIG_METHOD,
        "X-CA-Signature": sig,
    }

async def test(session, desc, path, method="GET", params=None, body=None):
    headers = build_headers(path, method)
    url = BASE_URL + path
    try:
        kwargs = {"headers": headers}
        if params:
            kwargs["params"] = params
        if body:
            kwargs["data"] = json.dumps(body)
        async with session.request(method, url, **kwargs) as resp:
            text = await resp.text()
            try:
                data = json.loads(text)
                code = data.get("code")
                status = "OK" if code == 0 else f"code={code}"
                print(f"  {resp.status} {status} | {method} {path}")
                if code == 0:
                    d = data.get("data")
                    print(f"    DATA: {json.dumps(d, indent=2)[:1200]}")
                elif code and code != 0:
                    print(f"    msg: {data.get('msg', 'N/A')}")
                return data
            except json.JSONDecodeError:
                print(f"  {resp.status} NO-JSON | {method} {path}")
                return None
    except Exception as e:
        print(f"  ERROR | {method} {path}: {e}")
        return None

async def main():
    print("=" * 60)
    print("TEST CON SIDs REALES")
    print("=" * 60)

    async with aiohttp.ClientSession() as s:
        # 1) Listar sistemas con POST
        print("\n--- 1. POST /installer/api/v2/systems (listar) ---")
        data = await test(s, "list systems page 1", "/installer/api/v2/systems", method="POST",
                          body={"page": 1, "size": 5})

        if data and data.get("code") == 0:
            systems = data["data"]["systems"]
            first = systems[0]
            real_sid = first["sid"]
            ecu_id = first["ecu"][0] if first.get("ecu") else None
            print(f"\n  Primer sistema encontrado:")
            print(f"    SID: {real_sid}")
            print(f"    ECU: {ecu_id}")
            print(f"    Username: {first.get('username', 'N/A')}")
            print(f"    Capacity: {first.get('capacity', 'N/A')} kW")

            # 2) Test endpoints con el SID real
            print(f"\n--- 2. Detalles con SID real: {real_sid} ---")
            await test(s, "details", f"/installer/api/v2/systems/details/{real_sid}")
            await test(s, "summary", f"/installer/api/v2/systems/summary/{real_sid}")
            await test(s, "inverters", f"/installer/api/v2/systems/inverters/{real_sid}")

            # Energy con date_range de hoy
            from datetime import date
            today = date.today().strftime("%Y-%m-%d")
            yesterday = "2025-07-15"
            await test(s, "energy daily", f"/installer/api/v2/systems/energy/{real_sid}",
                       params={"energy_level": "daily", "date_range": yesterday})
            await test(s, "energy hourly", f"/installer/api/v2/systems/energy/{real_sid}",
                       params={"energy_level": "hourly", "date_range": today})

            # 3) Test ECU-level endpoints
            if ecu_id:
                print(f"\n--- 3. ECU endpoints (ECU={ecu_id}) ---")
                await test(s, "ecu summary", f"/installer/api/v2/systems/{real_sid}/devices/ecu/summary/{ecu_id}")
                await test(s, "ecu energy", f"/installer/api/v2/systems/{real_sid}/devices/ecu/energy/{ecu_id}",
                           params={"energy_level": "daily", "date_range": yesterday})

                # 4) Inverter-level
                print(f"\n--- 4. Inverter endpoints ---")
                # Try getting inverters list first
                inv_data = await test(s, "inverters list", f"/installer/api/v2/systems/inverters/{real_sid}")
                if inv_data and inv_data.get("code") == 0:
                    inv_list = inv_data.get("data", {})
                    print(f"    Inverters data keys: {list(inv_list.keys()) if isinstance(inv_list, dict) else type(inv_list)}")
                    # Try to find inverter UIDs
                    if isinstance(inv_list, dict):
                        for key, val in inv_list.items():
                            print(f"    {key}: {json.dumps(val)[:300]}")
                            if isinstance(val, list) and len(val) > 0:
                                inv_uid = val[0].get("uid") if isinstance(val[0], dict) else val[0]
                                if inv_uid:
                                    await test(s, f"inverter energy {inv_uid}",
                                               f"/installer/api/v2/systems/{real_sid}/devices/inverter/energy/{inv_uid}",
                                               params={"energy_level": "daily", "date_range": yesterday})
                                    await test(s, f"inverter batch energy {inv_uid}",
                                               f"/installer/api/v2/systems/{real_sid}/devices/inverter/batch/energy/{inv_uid}",
                                               params={"energy_level": "power", "date_range": today})

        # 5) Pagination - get more systems
        print(f"\n--- 5. Paginacion (page 2) ---")
        await test(s, "list systems page 2", "/installer/api/v2/systems", method="POST",
                   body={"page": 2, "size": 5})

    print("\n" + "=" * 60)
    print("FIN")
    print("=" * 60)

asyncio.run(main())
