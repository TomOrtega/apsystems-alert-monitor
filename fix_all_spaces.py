import os, sys
sys.path.insert(0, '/app')
from src.storage.db import Database
from src.config import DbConfig

db = Database(DbConfig(host='postgres', port=5432, user='apsystems', password='apsystems_secret_2024', name='apsystems_monitor'))
db.connect()
conn = db._get_conn()

# Trim ALL account values
with conn.cursor() as cur:
    cur.execute("UPDATE config SET value = TRIM(value) WHERE section = 'accounts'")
    print(f"Trimmed {cur.rowcount} rows")
conn.commit()

# Verify
with conn.cursor() as cur:
    cur.execute("SELECT key, value FROM config WHERE section = 'accounts' ORDER BY id")
    for r in cur.fetchall():
        print(f"{r[0]}: {repr(r[1])}")

db.close()
