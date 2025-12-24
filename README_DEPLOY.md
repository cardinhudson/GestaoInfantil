# Deploy e persistência do banco

Este projeto usa SQLite por padrão (arquivo `gestaoinfantil.db`) quando `GESTAO_DB` não está configurada.

Para produção (recomendado), use um banco externo (Postgres) e a variável de ambiente `GESTAO_DB` apontando para a URL de conexão.

Exemplo (Postgres):

- URL típica: `postgresql+psycopg2://user:password@host:5432/dbname`
- No Streamlit Cloud/Deploy: adicione `GESTAO_DB` nas Environment Variables / Secrets com essa URL.

Passos rápidos:

1. Crie uma instância Postgres (Supabase, Railway, ElephantSQL, ou similar).
2. Se for usar Postgres, adicione `psycopg2-binary` ao `requirements.txt` (ex.: `psycopg2-binary==2.9.7`).
	- No Streamlit Cloud você também pode definir um Secret com a chave `GESTAO_DB` ou `DATABASE_URL` contendo a URL de conexão; `db.py` irá buscar esses valores automaticamente.
3. No painel do deploy (Streamlit Cloud), defina `GESTAO_DB` com a URL de conexão.
4. Redeploy a aplicação.

Notas:
- O arquivo SQLite (`gestaoinfantil.db`) é criado localmente e não é persistido entre deploys em ambientes efêmeros.
 - Se você prefere continuar com SQLite em produção, monte um volume persistente no host (quando possível) ou use um banco gerenciado.
 - Observação: instalar `psycopg2-binary` pode falhar em alguns ambientes sem dependências de compilação. Se o deploy falhar ao instalar requisitos, considere usar um serviço gerenciado (que aceite builds com `psycopg2`) ou configurar o Postgres externamente e apontar `GESTAO_DB` para ele.

Se quiser, eu posso adicionar exemplos de comandos `psql` para criar o banco, ou um script `migrate.sh` mínimo.

## Instruções passo-a-passo: Supabase + Streamlit Cloud

1. Crie um projeto no Supabase: https://app.supabase.com/
	- Clique em "New project", escolha nome, senha e região. A criação pode levar alguns minutos.
2. No painel do projeto Supabase, vá em `Settings` → `Database` → `Connection string` e copie a connection string do Postgres.
	- Exemplo: `postgresql://username:password@db.abcd.supabase.co:5432/postgres`
	- Para o SQLAlchemy/psycopg2 use o prefixo `postgresql+psycopg2://...` (opcional se o driver já suportado).
3. No Streamlit Cloud (ou seu host), adicione um Secret/Environment Variable:
	- Key: `GESTAO_DB`
	- Value: a URL de conexão do Supabase (ex.: `postgresql+psycopg2://username:password@host:5432/dbname`)
	- Alternativamente, use `DATABASE_URL` como chave, pois `db.py` aceita ambos.
4. Se o deploy exigir o driver `psycopg2-binary`, confirme que `requirements.txt` contém `psycopg2-binary` (já incluído). Se a instalação falhar, verifique o log do deploy; alguns hosts exigem imagens/buildpacks que tenham dependências nativas.
5. (Opcional) Forçar criação das tabelas via script de migração local ou em um job no deploy:

```bash
# Rode localmente com a variável de ambiente apontando para o Supabase (ou rode como job no servidor)
export GESTAO_DB="postgresql+psycopg2://username:password@host:5432/dbname"
python -c "from db import init_db; init_db()"
```

Agora existe um script auxiliar `migrate.sh` e um workflow GitHub Actions `/.github/workflows/migrate.yml` que você pode usar para automatizar a migração:

- Rodar localmente:

```bash
chmod +x migrate.sh
./migrate.sh
```

- Rodar no GitHub Actions (automático): configure um Secret `GESTAO_DB` no repositório (Settings → Secrets) e o workflow `DB Migrate` pode ser executado manualmente (Actions → DB Migrate → Run workflow) ou corre automaticamente ao dar push na branch `main`.


6. Redeploy a aplicação no Streamlit Cloud. O app criará/atualizará as tabelas automaticamente na primeira execução graças a `init_db()`.

7. Verifique o log do app para confirmações como `DB_URL=` e mensagens de seed; em caso de erro consulte o log do deploy e traga aqui que eu ajudo.

Se quiser, eu posso gerar um `migrate.sh` e um `ci` job de exemplo para automatizar o passo 5 no seu pipeline de deploy.
