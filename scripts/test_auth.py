from services import list_users, authenticate_user
users = list_users()
print('USERS:')
for u in users:
    print(u.id, u.name, u.email, u.roles, u.password_hash)
print('AUTH admin@example.com / 123 ->', authenticate_user('admin@example.com','123'))
