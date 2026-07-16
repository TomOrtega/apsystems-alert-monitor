import hmac, hashlib, base64, time, uuid
import requests

APP_ID = "2c9f934a9f59f04b019f5b7618ef3194"
APP_SECRET = "5b766f58761e"
BASE_URL = "https://api.apsystemsema.com:9282"

ts = str(int(time.time() * 1000))
nonce = uuid.uuid4().hex
path = "/patch/api/v2/systems"
request_path = path.rsplit("/", 1)[-1]
string_to_sign = "/".join([ts, nonce, APP_ID, request_path, "POST", "HmacSHA256"])
sig = base64.b64encode(hmac.new(APP_SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()).decode()

print("String to sign:", string_to_sign)
print()

r = requests.post(BASE_URL + path, headers={
    "X-CA-AppId": APP_ID,
    "X-CA-Timestamp": ts,
    "X-CA-Nonce": nonce,
    "X-CA-Signature-Method": "HmacSHA256",
    "X-CA-Signature": sig,
}, params={"page": 1, "size": 1}, timeout=15, verify=True)

print("Status:", r.status_code)
print("Body:", r.text[:500])
