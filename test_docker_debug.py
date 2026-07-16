from src.storage.db import Database
from src.config import DbConfig
import os

db = Database(DbConfig(host='postgres', port=5432, user='apsystems', password='changeme', name='apsystems_monitor'))
db.connect()
conn = db._get_conn()
with conn.cursor() as cur:
    cur.execute("SELECT key, value FROM config WHERE section = 'accounts' ORDER BY id")
    raw = {r[0]: r[1] for r in cur.fetchall()}
for k, v in sorted(raw.items()):
    print(f"{k}: {v[:20]}..." if len(v) > 20 else f"{k}: {v}")

# Now test the actual endpoint logic
from src.api.client import ApsystemsClient, ApiAccount

prefix = "account2"
app_id = raw.get(f"{prefix}_app_id", "")
app_secret = raw.get(f"{prefix}_app_secret", "")
base_url = raw.get(f"{prefix}_base_url", "https://api.apsystemsema.com:9282")

print(f"\nUsing: {prefix} -> app_id={app_id[:15]}... secret={app_secret[:15]}... url={base_url}")

client = ApsystemsClient(account=ApiAccount(app_id=app_id, app_secret=app_secret, base_url=base_url))
try:
    data = client.get_systems_batch(page=1, size=1)
    total = data.get("total", 0)
    print(f"SUCCESS: {total} systems found")
except Exception as e:
    print(f"ERROR: {e}")

db.close()
