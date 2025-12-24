# Deploy com Supabase (Postgres) e Streamlit Cloud

1. Crie um projeto no Supabase (https://app.supabase.com).
2. Em Project → Settings → Database → Connection info copie a *Direct connection string*.
3. No Streamlit Cloud, abra seu aplicativo → Settings → Secrets / Environment variables.
   - Adicione `GESTAO_DB` = `postgres://usuario:senha@host:5432/postgres`
   - Se a senha contiver `@`, troque por `%40` (URL-encode).
4. Salve e redeploy o app. O sistema criará as tabelas automaticamente no primeiro boot.

Testes locais:

- Para testar localmente com a mesma base:

```powershell
setx GESTAO_DB "postgres://usuario:senha@host:5432/postgres"
# Abra novo terminal
streamlit run app.py
```

- Para verificar a conexão com o banco (localmente):

```powershell
python scripts/test_db_connection.py
```

Segurança:
- NUNCA comite credenciais no repositório.
- Use `.streamlit/secrets.toml` localmente (não commitar) ou o painel de Secrets do Streamlit Cloud.
