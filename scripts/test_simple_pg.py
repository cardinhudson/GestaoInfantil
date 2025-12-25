import traceback
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
print('starting simple test')
try:
    import os
    print('DB TARGET', os.environ.get('GESTAO_DB') is not None)
    from db import get_connection, DB_KIND
    print('DB_KIND', DB_KIND)
    conn = get_connection()
    print('got connection', type(conn))
    cur = conn.cursor()
    cur.execute('SELECT 1')
    r = cur.fetchone()
    print('SELECT 1 ->', r)
    cur.close()
    conn.close()
except Exception:
    traceback.print_exc()
    raise
print('done')
