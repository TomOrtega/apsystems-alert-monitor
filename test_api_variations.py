import http.client, ssl, hmac, hashlib, base64, time, uuid, json

APP_ID = "2c9f934a9f59f04b019f5b7618ef3194"
APP_SECRET = "5b766f58761e"

def sign(method, request_path, ts, nonce):
    string_to_sign = "/".join([ts, nonce, APP_ID, request_path, method, "HmacSHA256"])
    sig = base64.b64encode(hmac.new(APP_SECRET.encode(), string_to_sign.encode(), hashlib.sha256).digest()).decode()
    return string_to_sign, sig

def test(desc, method, path, body=None, extra_headers=None):
    ts = str(int(time.time() * 1000))
    nonce = uuid.uuid4().hex
    request_path = path.rsplit("/", 1)[-1]
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
    resp = r.read().decode("utf-8", errors="replace")[:300]
    print(f"  [{r.status}] {desc}")
    print(f"  Body: {resp}")
    print()
    conn.close()

print("=== POST con JSON body vacio ===")
test("POST body='{}' + Content-Type:application/json",
     "POST", "/patch/api/v2/systems?page=1&size=1",
     body="{}", extra_headers={"Content-Type": "application/json"})

print("=== POST sin body, sin Content-Type ===")
test("POST sin body ni Content-Type",
     "POST", "/patch/api/v2/systems?page=1&size=1")

print("=== POST con body form-urlencoded ===")
test("POST Content-Type:application/x-www-form-urlencoded",
     "POST", "/patch/api/v2/systems",
     body="page=1&size=1",
     extra_headers={"Content-Type": "application/x-www-form-urlencoded"})

print("=== POST /patch/api/v2/systems con page/size en body JSON ===")
test("POST JSON body={page:1, size:1}",
     "POST", "/patch/api/v2/systems",
     body=json.dumps({"page": 1, "size": 1}),
     extra_headers={"Content-Type": "application/json"})

print("=== POST /user/api/v2/systems (end user endpoint) ===")
ts = str(int(time.time() * 1000))
nonce = uuid.uuid4().hex
sts, sig = sign("POST", "systems", ts, nonce)
print(f"  String to sign: {sts}")
test("POST /user/api/v2/systems",
     "POST", "/user/api/v2/systems?page=1&size=1",
     body="{}", extra_headers={"Content-Type": "application/json"})

print("=== POST /patch con query string diferente ===")
test("POST /patch/api/v2/systems (sin query params)",
     "POST", "/patch/api/v2/systems",
     body="{}", extra_headers={"Content-Type": "application/json"})

print("=== POST /patch con system_id ===")
test("POST /patch/api/v2/systems?system_id=215000024993",
     "POST", "/patch/api/v2/systems?system_id=215000024993",
     body="{}", extra_headers={"Content-Type": "application/json"})
