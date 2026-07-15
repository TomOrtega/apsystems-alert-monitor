import hmac, hashlib, base64, time, uuid, json
import requests

APP_ID = "TU_APP_ID"
APP_SECRET = "TU_APP_SECRET"
BASE_URL = "https://api.apsystemsema.com:9282"

def build_signature(path, method):
    ts = str(int(time.time() * 1000))
    nonce = uuid.uuid4().hex
    request_path = path.rsplit("/", 1)[-1]
    string_to_sign = "/".join([ts, nonce, APP_ID, request_path, method, "HmacSHA256"])
    sig = base64.b64encode(hmac.new(APP_SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()).decode()
    return {"X-CA-AppId": APP_ID, "X-CA-Timestamp": ts, "X-CA-Nonce": nonce, "X-CA-Signature-Method": "HmacSHA256", "X-CA-Signature": sig}

# Test 1: Probe base URL (GET)
print("=== Test 1: GET base URL ===")
try:
    r = requests.get(BASE_URL, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: POST /patch/api/v2/systems (como lo hace el cliente)
print("\n=== Test 2: POST /patch/api/v2/systems ===")
path = "/patch/api/v2/systems"
headers = build_signature(path, "POST")
try:
    r = requests.post(BASE_URL + path, headers=headers, params={"page": 1, "size": 1}, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Headers: {dict(r.headers)}")
    print(f"Body: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: GET /patch/api/v2/systems (por si es GET)
print("\n=== Test 3: GET /patch/api/v2/systems ===")
headers = build_signature(path, "GET")
try:
    r = requests.get(BASE_URL + path, headers=headers, params={"page": 1, "size": 1}, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 4: GET /user/api/v2/systems/details (otro endpoint)
print("\n=== Test 4: GET /user/api/v2/systems/details/TEST ===")
path4 = "/user/api/v2/systems/details/TEST"
headers = build_signature(path4, "GET")
try:
    r = requests.get(BASE_URL + path4, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
