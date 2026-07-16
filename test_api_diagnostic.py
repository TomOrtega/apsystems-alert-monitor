import http.client, ssl, hmac, hashlib, base64, time, uuid

# Test 1: Simple connectivity
print("=== TEST 1: Conectividad basica (sin auth) ===")
conn = http.client.HTTPSConnection("api.apsystemsema.com", 9282, timeout=15, context=ssl._create_unverified_context())
conn.request("GET", "/")
r1 = conn.getresponse()
print("Status:", r1.status)
print("Server:", r1.getheader("Server", "unknown"))
body1 = r1.read().decode("utf-8", errors="replace")[:200]
print("Body:", body1)
conn.close()

# Test 2: POST without auth
print()
print("=== TEST 2: POST /patch/api/v2/systems SIN auth ===")
conn2 = http.client.HTTPSConnection("api.apsystemsema.com", 9282, timeout=15, context=ssl._create_unverified_context())
conn2.request("POST", "/patch/api/v2/systems?page=1&size=1")
r2 = conn2.getresponse()
print("Status:", r2.status)
body2 = r2.read().decode("utf-8", errors="replace")[:300]
print("Body:", body2)
conn2.close()

# Test 3: POST with auth
print()
print("=== TEST 3: POST /patch/api/v2/systems CON auth ===")
APP_ID = "2c9f934a9f59f04b019f5b7618ef3194"
APP_SECRET = "5b766f58761e"
ts = str(int(time.time() * 1000))
nonce = uuid.uuid4().hex
string_to_sign = "/".join([ts, nonce, APP_ID, "systems", "POST", "HmacSHA256"])
sig = base64.b64encode(hmac.new(APP_SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()).decode()
print("String to sign:", string_to_sign)

conn3 = http.client.HTTPSConnection("api.apsystemsema.com", 9282, timeout=15, context=ssl._create_unverified_context())
headers = {
    "X-CA-AppId": APP_ID,
    "X-CA-Timestamp": ts,
    "X-CA-Nonce": nonce,
    "X-CA-Signature-Method": "HmacSHA256",
    "X-CA-Signature": sig,
    "Content-Type": "application/json",
}
conn3.request("POST", "/patch/api/v2/systems?page=1&size=1", body="{}", headers=headers)
r3 = conn3.getresponse()
print("Status:", r3.status)
body3 = r3.read().decode("utf-8", errors="replace")[:500]
print("Body:", body3)
conn3.close()

# Test 4: GET /user/api/v2/systems/details/{sid} with auth
print()
print("=== TEST 4: GET /user/api/v2/systems/details/TEST with auth ===")
ts4 = str(int(time.time() * 1000))
nonce4 = uuid.uuid4().hex
string_to_sign4 = "/".join([ts4, nonce4, APP_ID, "TEST", "GET", "HmacSHA256"])
sig4 = base64.b64encode(hmac.new(APP_SECRET.encode(), string_to_sign4.encode(), hashlib.sha256).digest()).decode()
print("String to sign:", string_to_sign4)

conn4 = http.client.HTTPSConnection("api.apsystemsema.com", 9282, timeout=15, context=ssl._create_unverified_context())
headers4 = {
    "X-CA-AppId": APP_ID,
    "X-CA-Timestamp": ts4,
    "X-CA-Nonce": nonce4,
    "X-CA-Signature-Method": "HmacSHA256",
    "X-CA-Signature": sig4,
}
conn4.request("GET", "/user/api/v2/systems/details/TEST", headers=headers4)
r4 = conn4.getresponse()
print("Status:", r4.status)
body4 = r4.read().decode("utf-8", errors="replace")[:500]
print("Body:", body4)
conn4.close()

# Test 5: GET /user without auth
print()
print("=== TEST 5: GET /user/api/v2/systems/details/TEST SIN auth ===")
conn5 = http.client.HTTPSConnection("api.apsystemsema.com", 9282, timeout=15, context=ssl._create_unverified_context())
conn5.request("GET", "/user/api/v2/systems/details/TEST")
r5 = conn5.getresponse()
print("Status:", r5.status)
body5 = r5.read().decode("utf-8", errors="replace")[:300]
print("Body:", body5)
conn5.close()
