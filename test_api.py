import hmac, hashlib, base64, time, uuid
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

print("=" * 60)
print("TEST CREDENCIALES APsystems")
print("=" * 60)

# Test 1: Probar si el servidor responde
print("\n[1] Probando conexion al servidor...")
try:
    r = requests.get(BASE_URL, timeout=10)
    print(f"    Status: {r.status_code}")
    print(f"    Body: {r.text[:150]}")
except Exception as e:
    print(f"    Error: {e}")

# Test 2: GET /user/api/v2/systems/details/TEST (End User mode)
print("\n[2] Probando End User mode: GET /user/api/v2/systems/details/TEST")
path = "/user/api/v2/systems/details/TEST"
headers = build_signature(path, "GET")
try:
    r = requests.get(BASE_URL + path, headers=headers, timeout=10)
    print(f"    Status: {r.status_code}")
    print(f"    Body: {r.text[:300]}")
except Exception as e:
    print(f"    Error: {e}")

# Test 3: POST /patch/api/v2/systems (Patch/Installer mode)
print("\n[3] Probando Patch mode: POST /patch/api/v2/systems")
path = "/patch/api/v2/systems"
headers = build_signature(path, "POST")
try:
    r = requests.post(BASE_URL + path, headers=headers, params={"page": 1, "size": 1}, timeout=10)
    print(f"    Status: {r.status_code}")
    print(f"    Body: {r.text[:300]}")
except Exception as e:
    print(f"    Error: {e}")

# Test 4: GET /user/api/v2/systems/inverters/TEST
print("\n[4] Probando End User inverters: GET /user/api/v2/systems/inverters/TEST")
path = "/user/api/v2/systems/inverters/TEST"
headers = build_signature(path, "GET")
try:
    r = requests.get(BASE_URL + path, headers=headers, timeout=10)
    print(f"    Status: {r.status_code}")
    print(f"    Body: {r.text[:300]}")
except Exception as e:
    print(f"    Error: {e}")

# Test 5: POST /user/api/v2/systems/summary/TEST
print("\n[5] Probando End User summary: POST /user/api/v2/systems/summary/TEST")
path = "/user/api/v2/systems/summary/TEST"
headers = build_signature(path, "POST")
try:
    r = requests.post(BASE_URL + path, headers=headers, timeout=10)
    print(f"    Status: {r.status_code}")
    print(f"    Body: {r.text[:300]}")
except Exception as e:
    print(f"    Error: {e}")

print("\n" + "=" * 60)
print("Si los tests 2, 4 o 5 funcionan pero el 3 falla,")
print("tu credencial es de END USER, no de PATCH/INSTALLER.")
print("Necesitamos cambiar los endpoints a /user/api/v2/...")
print("=" * 60)
