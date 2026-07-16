#!/usr/bin/env python3
"""
Test oficial de credenciales APsystems (basado en la integracion HA que funciona)
Ejecutar: python test_oficial_ha.py
"""
import asyncio, aiohttp, time, uuid, hmac, hashlib, base64, json

APP_ID     = "2c9f934a9f49a1fb019f64766c1c7965"
APP_SECRET = "64766c1b7964"
SID        = "215000024993"
BASE_URL   = "https://api.apsystemsema.com:9282"
SIG_METHOD = "HmacSHA256"

def build_headers(app_id, app_secret, path, method="GET"):
    ts = str(int(time.time() * 1000))
    nonce = uuid.uuid4().hex
    request_path_to_sign = path.rsplit("/", 1)[-1]
    s2s = "/".join([ts, nonce, app_id, request_path_to_sign, method.upper(), SIG_METHOD])
    sig = base64.b64encode(
        hmac.new(app_secret.encode(), s2s.encode(), hashlib.sha256).digest()
    ).decode()
    return {
        "Content-Type": "application/json",
        "X-CA-AppId": app_id,
        "X-CA-Timestamp": ts,
        "X-CA-Nonce": nonce,
        "X-CA-Signature-Method": SIG_METHOD,
        "X-CA-Signature": sig,
    }, s2s

async def main():
    print("=" * 60)
    print("TEST OFICIAL APsystems (metodo Home Assistant)")
    print("=" * 60)
    print(f"AppID:  {APP_ID}")
    print(f"Secret: {APP_SECRET}")
    print(f"SID:    {SID}")
    print()

    async with aiohttp.ClientSession() as session:
        # Test 1: Summary
        summary_path = f"/user/api/v2/systems/summary/{SID}"
        headers, s2s = build_headers(APP_ID, APP_SECRET, summary_path, "GET")
        print(f"[1] GET {summary_path}")
        print(f"    StringToSign: {s2s}")
        try:
            async with session.get(BASE_URL + summary_path, headers=headers) as resp:
                text = await resp.text()
                print(f"    Status: {resp.status}")
                print(f"    Body: {text[:300]}")
        except Exception as e:
            print(f"    ERROR: {e}")
        print()

        # Test 2: System details
        detail_path = f"/user/api/v2/systems/details/{SID}"
        headers2, s2s2 = build_headers(APP_ID, APP_SECRET, detail_path, "GET")
        print(f"[2] GET {detail_path}")
        print(f"    StringToSign: {s2s2}")
        try:
            async with session.get(BASE_URL + detail_path, headers=headers2) as resp:
                text = await resp.text()
                print(f"    Status: {resp.status}")
                print(f"    Body: {text[:300]}")
        except Exception as e:
            print(f"    ERROR: {e}")
        print()

        # Test 3: Inverters
        inv_path = f"/user/api/v2/systems/inverters/{SID}"
        headers3, s2s3 = build_headers(APP_ID, APP_SECRET, inv_path, "GET")
        print(f"[3] GET {inv_path}")
        print(f"    StringToSign: {s2s3}")
        try:
            async with session.get(BASE_URL + inv_path, headers=headers3) as resp:
                text = await resp.text()
                print(f"    Status: {resp.status}")
                print(f"    Body: {text[:300]}")
        except Exception as e:
            print(f"    ERROR: {e}")
        print()

        # Test 4: Sin auth (control)
        print("[4] GET (sin auth - control)")
        try:
            async with session.get(BASE_URL + "/user/api/v2/systems/details/TEST") as resp:
                text = await resp.text()
                print(f"    Status: {resp.status}")
                print(f"    Body: {text[:200]}")
        except Exception as e:
            print(f"    ERROR: {e}")

asyncio.run(main())
