import http.client, ssl, hmac, hashlib, base64, time, uuid

APP_ID = "2c9f934a9f59f04b019f5b7618ef3194"
APP_SECRET = "5b766f58761e"

print("Esperando 10 segundos...")
time.sleep(10)

# 1. Test sin auth (should return 200 + code 4000)
print("=== TEST 1: Sin auth (deberia funcionar) ===")
conn = http.client.HTTPSConnection("api.apsystemsema.com", 9282, timeout=15, context=ssl._create_unverified_context())
conn.request("GET", "/user/api/v2/systems/details/TEST")
r = conn.getresponse()
print(f"Status: {r.status}")
print(f"Body: {r.read().decode('utf-8', errors='replace')[:200]}")
conn.close()

time.sleep(3)

# 2. Test con auth a details/TEST
print()
print("=== TEST 2: Con auth a /user/api/v2/systems/details/TEST ===")
ts = str(int(time.time() * 1000))
nonce = uuid.uuid4().hex
request_path = "TEST"
string_to_sign = "/".join([ts, nonce, APP_ID, request_path, "GET", "HmacSHA256"])
sig = base64.b64encode(hmac.new(APP_SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()).decode()
print(f"StringToSign: {string_to_sign}")

conn2 = http.client.HTTPSConnection("api.apsystemsema.com", 9282, timeout=15, context=ssl._create_unverified_context())
conn2.request("GET", "/user/api/v2/systems/details/TEST", headers={
    "X-CA-AppId": APP_ID,
    "X-CA-Timestamp": ts,
    "X-CA-Nonce": nonce,
    "X-CA-Signature-Method": "HmacSHA256",
    "X-CA-Signature": sig,
})
r2 = conn2.getresponse()
print(f"Status: {r2.status}")
print(f"Body: {r2.read().decode('utf-8', errors='replace')[:300]}")
conn2.close()

time.sleep(3)

# 3. Test con auth a GET /patch/api/v2/systems?page=1&size=1
print()
print("=== TEST 3: Con auth a /patch/api/v2/systems?page=1&size=1 ===")
ts3 = str(int(time.time() * 1000))
nonce3 = uuid.uuid4().hex
request_path3 = "systems"
string_to_sign3 = "/".join([ts3, nonce3, APP_ID, request_path3, "GET", "HmacSHA256"])
sig3 = base64.b64encode(hmac.new(APP_SECRET.encode(), string_to_sign3.encode(), hashlib.sha256).digest()).decode()
print(f"StringToSign: {string_to_sign3}")

conn3 = http.client.HTTPSConnection("api.apsystemsema.com", 9282, timeout=15, context=ssl._create_unverified_context())
conn3.request("GET", "/patch/api/v2/systems?page=1&size=1", headers={
    "X-CA-AppId": APP_ID,
    "X-CA-Timestamp": ts3,
    "X-CA-Nonce": nonce3,
    "X-CA-Signature-Method": "HmacSHA256",
    "X-CA-Signature": sig3,
})
r3 = conn3.getresponse()
print(f"Status: {r3.status}")
print(f"Body: {r3.read().decode('utf-8', errors='replace')[:500]}")
conn3.close()
