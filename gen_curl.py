import hmac, hashlib, base64, time, uuid

# === CUENTA 1 (Madrid) ===
APP_ID = '2c9f934a9f59f04b019f5b7618ef3194'
APP_SECRET = '5b766f58761e'
BASE_URL = 'https://api.apsystemsema.com:9282'
PATH = '/patch/api/v2/systems'

ts = str(int(time.time() * 1000))
nonce = uuid.uuid4().hex
request_path = PATH.rsplit('/', 1)[-1]
string_to_sign = '/'.join([ts, nonce, APP_ID, request_path, 'POST', 'HmacSHA256'])
sig = base64.b64encode(hmac.new(APP_SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()).decode()

print("=" * 70)
print("CUENTA 1 (Madrid)")
print("=" * 70)
print(f"APP_ID:     {APP_ID}")
print(f"APP_SECRET: {APP_SECRET}")
print(f"BASE_URL:   {BASE_URL}")
print()

print("--- CURL (copia y pega en tu terminal) ---")
print()
print(f'curl -k -X POST "{BASE_URL}{PATH}?page=1&size=1" -H "X-CA-AppId: {APP_ID}" -H "X-CA-Timestamp: {ts}" -H "X-CA-Nonce: {nonce}" -H "X-CA-Signature-Method: HmacSHA256" -H "X-CA-Signature: {sig}"')
print()
print(f"String to sign: {string_to_sign}")
print()

# === CUENTA 2 (Valencia) ===
APP_ID2 = '2c9f934a9f49a1fb019f64766c1c7965'
APP_SECRET2 = '64766c1b7964'

ts2 = str(int(time.time() * 1000))
nonce2 = uuid.uuid4().hex
string_to_sign2 = '/'.join([ts2, nonce2, APP_ID2, request_path, 'POST', 'HmacSHA256'])
sig2 = base64.b64encode(hmac.new(APP_SECRET2.encode(), string_to_sign2.encode(), hashlib.sha256).digest()).decode()

print("=" * 70)
print("CUENTA 2 (Valencia)")
print("=" * 70)
print(f"APP_ID:     {APP_ID2}")
print(f"APP_SECRET: {APP_SECRET2}")
print()

print("--- CURL ---")
print()
print(f'curl -k -X POST "{BASE_URL}{PATH}?page=1&size=1" -H "X-CA-AppId: {APP_ID2}" -H "X-CA-Timestamp: {ts2}" -H "X-CA-Nonce: {nonce2}" -H "X-CA-Signature-Method: HmacSHA256" -H "X-CA-Signature: {sig2}"')
print()
print(f"String to sign: {string_to_sign2}")
