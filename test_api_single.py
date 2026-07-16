import http.client, ssl, hmac, hashlib, base64, time, uuid
import sys

APP_ID = "2c9f934a9f59f04b019f5b7618ef3194"
APP_SECRET = "5b766f58761e"
SID = "215000024993"

# Wait 5 seconds
print("Esperando 5 segundos...")
time.sleep(5)

ts = str(int(time.time() * 1000))
nonce = uuid.uuid4().hex
request_path = "details/" + SID
string_to_sign = "/".join([ts, nonce, APP_ID, request_path, "GET", "HmacSHA256"])
sig = base64.b64encode(hmac.new(APP_SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()).decode()

print(f"StringToSign: {string_to_sign}")
print(f"Nonce: {nonce}")
print(f"Timestamp: {ts}")
print()

conn = http.client.HTTPSConnection("api.apsystemsema.com", 9282, timeout=15, context=ssl._create_unverified_context())
headers = {
    "X-CA-AppId": APP_ID,
    "X-CA-Timestamp": ts,
    "X-CA-Nonce": nonce,
    "X-CA-Signature-Method": "HmacSHA256",
    "X-CA-Signature": sig,
}
conn.request("GET", f"/user/api/v2/systems/details/{SID}", headers=headers)
r = conn.getresponse()
print(f"Status: {r.status}")
resp = r.read().decode("utf-8", errors="replace")[:500]
print(f"Body: {resp}")
conn.close()
