#!/usr/bin/env python3
"""
Test limpio de credenciales APsystems.
Ejecutar tras esperar 1 hora para que se reinicie el rate limit.

Uso: pip install aiohttp && python test_clean.py
"""
import asyncio, aiohttp, time, uuid, hmac, hashlib, base64, json, sys

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

async def test_endpoint(session, desc, path):
    headers, s2s = build_headers(APP_ID, APP_SECRET, path)
    print(f"\n  [{desc}]")
    print(f"  GET {path}")
    print(f"  s2s: {s2s}")
    try:
        async with session.get(BASE_URL + path, headers=headers) as resp:
            text = await resp.text()
            try:
                data = json.loads(text)
                code = data.get("code")
                print(f"  Status: {resp.status} | code: {code}")
                if code == 0:
                    print(f"  DATA: {json.dumps(data.get('data'), indent=4)[:500]}")
                else:
                    print(f"  Body: {text[:300]}")
            except json.JSONDecodeError:
                print(f"  Status: {resp.status} (no JSON)")
                print(f"  Body: {text[:200]}")
    except Exception as e:
        print(f"  ERROR: {e}")

async def main():
    print("=" * 60)
    print("TEST LIMPIO APsystems API")
    print("=" * 60)
    print(f"App ID:  {APP_ID}")
    print(f"Secret:  {APP_SECRET}")
    print(f"SID:     {SID}")
    print(f"Base:    {BASE_URL}")

    async with aiohttp.ClientSession() as session:
        # Test 0: Connectivity
        print("\n--- 0. Connectivity ---")
        try:
            async with session.get(BASE_URL + "/") as resp:
                print(f"  Status: {resp.status} (server OK)")
        except Exception as e:
            print(f"  ERROR: {e}")

        # Test 1: System details
        await test_endpoint(session, "System details (End User)", f"/user/api/v2/systems/details/{SID}")

        # Test 2: System summary
        await test_endpoint(session, "System summary (End User)", f"/user/api/v2/systems/summary/{SID}")

        # Test 3: Inverters
        await test_endpoint(session, "Inverters list (End User)", f"/user/api/v2/systems/inverters/{SID}")

        # Test 4: Installer systems
        await test_endpoint(session, "Systems list (Installer)", "/installer/api/v2/systems")

        # Test 5: User systems
        await test_endpoint(session, "Systems list (End User)", "/user/api/v2/systems")

    print("\n" + "=" * 60)
    print("FIN DEL TEST")
    print("=" * 60)

asyncio.run(main())
