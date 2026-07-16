#!/usr/bin/env python3
"""
Test exhaustivo de endpoints Installer API de APsystems.
Explora todos los endpoints posibles con diferentes parámetros.
"""
import asyncio, aiohttp, time, uuid, hmac, hashlib, base64, json

APP_ID     = "2c9f934a9f49a1fb019f64766c1c7965"
APP_SECRET = "64766c1b7964"
SID        = "215000024993"
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

async def test(session, desc, path, method="GET", params=None):
    headers = build_headers(path, method)
    url = BASE_URL + path
    try:
        async with session.request(method, url, headers=headers, params=params) as resp:
            text = await resp.text()
            try:
                data = json.loads(text)
                code = data.get("code")
                status = "OK" if code == 0 else f"code={code}"
                print(f"  {resp.status} {status} | {method} {path}")
                if params:
                    print(f"    params: {params}")
                if code == 0:
                    d = data.get("data")
                    print(f"    DATA: {json.dumps(d, indent=2)[:600]}")
                elif code and code != 0:
                    print(f"    msg: {data.get('msg', 'N/A')}")
            except json.JSONDecodeError:
                print(f"  {resp.status} NO-JSON | {method} {path}")
                if resp.status != 200:
                    print(f"    body: {text[:150]}")
    except Exception as e:
        print(f"  ERROR | {method} {path}: {e}")

async def main():
    print("=" * 60)
    print("TEST EXHAUSTIVO INSTALLER API")
    print("=" * 60)

    async with aiohttp.ClientSession() as s:
        # --- /installer/api/v2/systems with params ---
        print("\n--- /installer/api/v2/systems ---")
        await test(s, "sin params", "/installer/api/v2/systems")
        await test(s, "page=1,size=50", "/installer/api/v2/systems", params={"page": "1", "size": "50"})
        await test(s, "page=1,size=10", "/installer/api/v2/systems", params={"page": "1", "size": "10"})
        await test(s, "pageNum=1,pageSize=10", "/installer/api/v2/systems", params={"pageNum": "1", "pageSize": "10"})

        # --- Installer endpoints with SID ---
        print("\n--- /installer/api/v2/systems/{sid} ---")
        await test(s, "details", f"/installer/api/v2/systems/details/{SID}")
        await test(s, "summary", f"/installer/api/v2/systems/summary/{SID}")
        await test(s, "inverters", f"/installer/api/v2/systems/inverters/{SID}")
        await test(s, "energy", f"/installer/api/v2/systems/energy/{SID}", params={"energy_level": "daily", "date_range": "2025-07-01"})
        await test(s, "devices", f"/installer/api/v2/systems/{SID}/devices")
        await test(s, "devices/ecu", f"/installer/api/v2/systems/{SID}/devices/ecu")

        # --- Installer with SID in path ---
        print("\n--- Other installer patterns ---")
        await test(s, "installer systems/list", "/installer/api/v2/systems/list")
        await test(s, "installer systems/{SID}", f"/installer/api/v2/systems/{SID}")

        # --- Try POST on /installer/api/v2/systems ---
        print("\n--- POST /installer/api/v2/systems ---")
        await test(s, "POST systems", "/installer/api/v2/systems", method="POST")
        await test(s, "POST systems with body", "/installer/api/v2/systems", method="POST",
                   params={"page": "1", "size": "10"})

        # --- Also try /patch/api/v2/ endpoints ---
        print("\n--- /patch/api/v2/ endpoints ---")
        await test(s, "patch systems", "/patch/api/v2/systems")
        await test(s, "patch systems page", "/patch/api/v2/systems", params={"page": "1", "size": "10"})
        await test(s, "patch details", f"/patch/api/v2/systems/details/{SID}")
        await test(s, "patch summary", f"/patch/api/v2/systems/summary/{SID}")

        # --- Maybe the SID format is different ---
        print("\n--- /user/api/v2/ with SID in different format ---")
        await test(s, "user systems", "/user/api/v2/systems", params={"page": "1", "size": "10"})

    print("\n" + "=" * 60)
    print("FIN")
    print("=" * 60)

asyncio.run(main())
