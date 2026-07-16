import http.client, ssl, hmac, hashlib, base64, time, uuid

APP_ID = "2c9f934a9f49a1fb019f64766c1c7965"
APP_SECRET = "64766c1b7964"
SID = "215000024993"

def make_request(method, url_path, request_path_for_sign):
    ts = str(int(time.time() * 1000))
    nonce = uuid.uuid4().hex
    string_to_sign = "/".join([ts, nonce, APP_ID, request_path_for_sign, method, "HmacSHA256"])
    sig = base64.b64encode(hmac.new(APP_SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()).decode()
    
    conn = http.client.HTTPSConnection("api.apsystemsema.com", 9282, timeout=15, context=ssl._create_unverified_context())
    conn.request(method, url_path, headers={
        "X-CA-AppId": APP_ID,
        "X-CA-Timestamp": ts,
        "X-CA-Nonce": nonce,
        "X-CA-Signature-Method": "HmacSHA256",
        "X-CA-Signature": sig,
    })
    r = conn.getresponse()
    resp = r.read().decode("utf-8", errors="replace")[:300]
    print(f"  [{r.status}] sign='{request_path_for_sign}' -> {resp[:120]}")
    conn.close()

print("=== Cuenta 2: Valencia ===")
print(f"AppId={APP_ID}")
print()

# Test 1: sin auth
print("--- Sin auth ---")
conn = http.client.HTTPSConnection("api.apsystemsema.com", 9282, timeout=15, context=ssl._create_unverified_context())
conn.request("GET", f"/user/api/v2/systems/details/{SID}")
r = conn.getresponse()
print(f"  [{r.status}] GET /user/.../details/{SID} sin auth -> {r.read().decode('utf-8', errors='replace')[:120]}")
conn.close()
print()

# Test 2: Different request_path interpretations for user endpoint
print("--- User API: Variaciones de RequestPath ---")
make_request("GET", f"/user/api/v2/systems/details/{SID}", SID)  # just SID
make_request("GET", f"/user/api/v2/systems/details/{SID}", f"details/{SID}")  # details/SID
make_request("GET", f"/user/api/v2/systems/details/{SID}", "/user/api/v2/systems/details")  # full minus SID
make_request("GET", f"/user/api/v2/systems/details/{SID}", "/user/api/v2/systems/details/" + SID)  # full
print()

# Test 3: Patch API
print("--- Patch API: Variaciones de RequestPath ---")
make_request("GET", "/patch/api/v2/systems?page=1&size=1", "systems")
make_request("GET", "/patch/api/v2/systems?page=1&size=1", "/patch/api/v2/systems")
make_request("GET", f"/patch/api/v2/systems/{SID}", SID)
make_request("GET", f"/patch/api/v2/systems/{SID}", f"systems/{SID}")
print()

# Test 4: realtime
print("--- Realtime ---")
make_request("GET", f"/user/api/v2/systems/{SID}/realtime", SID)
make_request("GET", f"/user/api/v2/systems/{SID}/realtime", "realtime")
make_request("GET", f"/user/api/v2/systems/{SID}/realtime", f"{SID}/realtime")
print()

# Test 5: Try with HmacSHA1 instead
print("--- HmacSHA1 ---")
ts = str(int(time.time() * 1000))
nonce = uuid.uuid4().hex
sts = "/".join([ts, nonce, APP_ID, SID, "GET", "HmacSHA1"])
sig = base64.b64encode(hmac.new(APP_SECRET.encode(), sts.encode(), hashlib.sha1).digest()).decode()
conn = http.client.HTTPSConnection("api.apsystemsema.com", 9282, timeout=15, context=ssl._create_unverified_context())
conn.request("GET", f"/user/api/v2/systems/details/{SID}", headers={
    "X-CA-AppId": APP_ID, "X-CA-Timestamp": ts, "X-CA-Nonce": nonce,
    "X-CA-Signature-Method": "HmacSHA1", "X-CA-Signature": sig,
})
r = conn.getresponse()
print(f"  [{r.status}] HmacSHA1 -> {r.read().decode('utf-8', errors='replace')[:200]}")
conn.close()
