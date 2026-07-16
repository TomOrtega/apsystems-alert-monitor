import http.client, ssl, hmac, hashlib, base64, time, uuid, json

APP_ID = "2c9f934a9f59f04b019f5b7618ef3194"
APP_SECRET = "5b766f58761e"
SID = "215000024993"

def sign(method, request_path, ts, nonce):
    string_to_sign = "/".join([ts, nonce, APP_ID, request_path, method, "HmacSHA256"])
    sig = base64.b64encode(hmac.new(APP_SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()).decode()
    return string_to_sign, sig

def test(desc, method, path, body=None, extra_headers=None):
    ts = str(int(time.time() * 1000))
    nonce = uuid.uuid4().hex
    request_path = path.split("?")[0].rsplit("/", 1)[-1]
    sts, sig = sign(method, request_path, ts, nonce)
    
    headers = {
        "X-CA-AppId": APP_ID,
        "X-CA-Timestamp": ts,
        "X-CA-Nonce": nonce,
        "X-CA-Signature-Method": "HmacSHA256",
        "X-CA-Signature": sig,
    }
    if extra_headers:
        headers.update(extra_headers)
    
    conn = http.client.HTTPSConnection("api.apsystemsema.com", 9282, timeout=15, context=ssl._create_unverified_context())
    conn.request(method, path, body=body, headers=headers)
    r = conn.getresponse()
    resp = r.read().decode("utf-8", errors="replace")[:500]
    print(f"  [{r.status}] {desc}")
    print(f"  StringToSign: {sts}")
    print(f"  Body: {resp}")
    print()
    conn.close()

print("=== GET /patch/api/v2/systems?page=1&size=1 (listar sistemas) ===")
test("GET systems list (Patch mode)", "GET", "/patch/api/v2/systems?page=1&size=1")

print("=== GET /patch/api/v2/systems/{sid}/realtime ===")
test("GET system realtime (Patch)", "GET", f"/patch/api/v2/systems/{SID}/realtime")

print("=== GET /patch/api/v2/systems/{sid} ===")
test("GET system detail (Patch)", "GET", f"/patch/api/v2/systems/{SID}")

print("=== GET /user/api/v2/systems/details/{sid} ===")
test("GET system detail (End User)", "GET", f"/user/api/v2/systems/details/{SID}")

print("=== GET /patch/api/v2/systems/{sid}/energy?start=2025-01-01&end=2025-01-31 ===")
test("GET energy data (Patch)", "GET", f"/patch/api/v2/systems/{SID}/energy?start=2025-01-01&end=2025-01-31")

print("=== GET /user/api/v2/systems/{sid}/realtime ===")
test("GET system realtime (End User)", "GET", f"/user/api/v2/systems/{SID}/realtime")
