import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import init_db
import services

def main():
    print('init_db...')
    init_db()
    print('seed...')
    services.seed_sample_data()
    print('creating user...')
    u = services.create_user('TesteCloud','teste.cloud@example.com','child','123')
    print('user id', u.id)
    print('creating task...')
    t = services.create_task('Ler livro',5,'money',u.id,u.id,None)
    print('task id', t.id)
    print('validating task...')
    services.validate_task(t.id, u.id)
    print('creating debit...')
    services.create_debit(u.id, points=1, reason='ajuste')
    print('list users...')
    print([(x.id,x.name,x.email,x.roles) for x in services.list_users()])
    print('list tasks...')
    print([(x.id,x.name,x.points,x.validated) for x in services.list_tasks()])
    print('report...')
    print(services.get_report())

if __name__ == '__main__':
    main()
