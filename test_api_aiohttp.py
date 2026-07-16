#!/usr/bin/env python3
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
    sig = base64.b64encode(hmac.new(app_secret.encode(), s2s.encode(), hashlib.sha256).digest()).decode()
    return {
        "Content-Type": "application/json",
        "X-CA-AppId": app_id,
        "X-CA-Timestamp": ts,
        "X-CA-Nonce": nonce,
        "X-CA-Signature-Method": SIG_METHOD,
        "X-CA-Signature": sig,
    }, s2s

async def main():
    async with aiohttp.ClientSession() as session:
        summary_path = f"/user/api/v2/systems/summary/{SID}"
        headers, s2s = build_headers(APP_ID, APP_SECRET, summary_path, "GET")
        print(f"StringToSign: {s2s}")
        print(f"URL: {BASE_URL}{summary_path}")
        print(f"Headers: {json.dumps({k:v for k,v in headers.items() if k != 'X-CA-Signature'}, indent=2)}")
        print()

        try:
            async with session.get(BASE_URL + summary_path, headers=headers) as resp:
                text = await resp.text()
                print(f"Status: {resp.status}")
                print(f"Body: {text[:500]}")
        except Exception as e:
            print(f"ERROR: {e}")

        print()
        print("=== Test 2: Energy ===")
        energy_path = f"/user/api/v2/systems/energy/{SID}"
        headers2, s2s2 = build_headers(APP_ID, APP_SECRET, energy_path, "GET")
        print(f"StringToSign: {s2s2}")
        try:
            async with session.get(BASE_URL + energy_path, headers=headers2, params={"energy_level": "hourly", "date_range": "2025-07-15"}) as resp:
                text = await resp.text()
                print(f"Status: {resp.status}")
                print(f"Body: {text[:500]}")
        except Exception as e:
            print(f"ERROR: {e}")

        print()
        print("=== Test 3: Inverters ===")
        inv_path = f"/user/api/v2/systems/inverters/{SID}"
        headers3, s2s3 = build_headers(APP_ID, APP_SECRET, inv_path, "GET")
        print(f"StringToSign: {s2s3}")
        try:
            async with session.get(BASE_URL + inv_path, headers=headers3) as resp:
                text = await resp.text()
                print(f"Status: {resp.status}")
                print(f"Body: {text[:500]}")
        except Exception as e:
            print(f"ERROR: {e}")

asyncio.run(main())
