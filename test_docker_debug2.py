import sys, os
sys.path.insert(0, '/app')
from src.storage.db import Database
from src.config import DbConfig

db = Database(DbConfig(
    host=os.getenv('DB_HOST', 'postgres'),
    port=int(os.getenv('DB_PORT', '5432')),
    user=os.getenv('DB_USER', 'apsystems'),
    password=os.getenv('DB_PASSWORD', 'changeme'),
    name=os.getenv('DB_NAME', 'apsystems_monitor'),
))
db.connect()
conn = db._get_conn()
with conn.cursor() as cur:
    cur.execute("SELECT key, value FROM config WHERE section = %s ORDER BY id", ('accounts',))
    raw = {r[0]: r[1] for r in cur.fetchall()}

prefix = 'account2'
app_id = raw.get(f'{prefix}_app_id', '')
app_secret = raw.get(f'{prefix}_app_secret', '')
base_url = raw.get(f'{prefix}_base_url', '')
print(f'Using: app_id={app_id!r} secret={app_secret!r} url={base_url!r}')

from src.api.client import ApsystemsClient, ApiAccount
client = ApsystemsClient(account=ApiAccount(app_id=app_id, app_secret=app_secret, base_url=base_url))
data = client.get_systems_batch(page=1, size=1)
total = data.get('total', 0)
print(f'SUCCESS: {total} systems found')

db.close()
