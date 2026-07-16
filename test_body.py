import requests, hmac, hashlib, base64, time, uuid, json

APP_ID = '2c9f934a9f49a1fb019f64766c1c7965'
APP_SECRET = '64766c1b7964'
BASE = 'https://api.apsystemsema.com:9282'

ts = str(int(time.time() * 1000))
nonce = uuid.uuid4().hex
s2s = f'{ts}/{nonce}/{APP_ID}/systems/POST/HmacSHA256'
sig = base64.b64encode(hmac.new(APP_SECRET.encode(), s2s.encode(), hashlib.sha256).digest()).decode()
headers = {
    'X-CA-AppId': APP_ID,
    'X-CA-Timestamp': ts,
    'X-CA-Nonce': nonce,
    'X-CA-Signature-Method': 'HmacSHA256',
    'X-CA-Signature': sig,
    'Content-Type': 'application/json',
}
r = requests.post(BASE + '/installer/api/v2/systems', headers=headers, json={'page': 1, 'size': 2}, timeout=30)
d = r.json()
print(f"code={d.get('code')} total={d['data']['total']} size={d['data']['size']} systems={len(d['data']['systems'])}")
print(f"first sid={d['data']['systems'][0]['sid']}")
