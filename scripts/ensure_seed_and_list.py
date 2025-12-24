from services import seed_sample_data, list_users, authenticate_user, hash_password

print('Running seed_sample_data()...')
seed_sample_data()
print('Listing users:')
users = list_users()
for u in users:
    print(u.id, repr(u.name), repr(u.email), repr(u.roles), repr(u.password_hash))

print('\nAuth tests:')
for email in ['admin@example.com','joao@example.com','ana@example.com']:
    ok = authenticate_user(email,'123')
    print(email, '->', 'OK' if ok else 'FAIL')

print('HASH(123)=', hash_password('123'))
