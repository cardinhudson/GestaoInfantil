import traceback
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
print('starting')
try:
    from db import init_db
    import services
    print('calling init_db')
    init_db()
    print('init_db done')
    print('calling seed')
    services.seed_sample_data()
    print('seed done')
    users = services.list_users()
    print('USERS:', [(u.id,u.name,u.email,u.roles) for u in users])
    tasks = services.list_tasks()
    print('TASKS len:', len(tasks))
    report = services.get_report()
    print('REPORT entries:', len(report))
except Exception:
    traceback.print_exc()
    raise
print('finished')
