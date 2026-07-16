import os, sys
sys.path.insert(0, '/app')
from src.storage.db import Database
from src.config import DbConfig

db = Database(DbConfig(host='postgres', port=5432, user='apsystems', password='apsystems_secret_2024', name='apsystems_monitor'))
db.connect()
conn = db._get_conn()
with conn.cursor() as cur:
    cur.execute("SELECT key, value FROM config WHERE section = 'accounts' AND key LIKE 'account2_%'")
    for r in cur.fetchall():
        val = r[1]
        print(f"{r[0]}: {repr(val)} (len={len(val)}, stripped_len={len(val.strip())})")

# Fix trailing spaces
with conn.cursor() as cur:
    cur.execute("UPDATE config SET value = TRIM(value) WHERE section = 'accounts' AND key LIKE 'account2_%'")
    print(f"\nTrimmed {cur.rowcount} rows")
conn.commit()

# Verify
with conn.cursor() as cur:
    cur.execute("SELECT key, value FROM config WHERE section = 'accounts' AND key LIKE 'account2_%'")
    for r in cur.fetchall():
        print(f"{r[0]}: {repr(r[1])}")

db.close()
