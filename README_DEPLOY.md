# Deploy e persistência do banco

Este projeto usa SQLite por padrão (arquivo `gestaoinfantil.db`) quando `GESTAO_DB` não está configurada.

Para produção (recomendado), use um banco externo (Postgres) e a variável de ambiente `GESTAO_DB` apontando para a URL de conexão.

Exemplo (Postgres):

- URL típica: `postgresql+psycopg2://user:password@host:5432/dbname`
- No Streamlit Cloud/Deploy: adicione `GESTAO_DB` nas Environment Variables / Secrets com essa URL.

Passos rápidos:

1. Crie uma instância Postgres (Supabase, Railway, ElephantSQL, ou similar).
2. Se for usar Postgres, adicione `psycopg2-binary` ao `requirements.txt` (ex.: `psycopg2-binary==2.9.7`).
3. No painel do deploy (Streamlit Cloud), defina `GESTAO_DB` com a URL de conexão.
4. Redeploy a aplicação.

Notas:
- O arquivo SQLite (`gestaoinfantil.db`) é criado localmente e não é persistido entre deploys em ambientes efêmeros.
- Se você prefere continuar com SQLite em produção, implemente um armazenamento de arquivo persistente (S3) ou monte um volume persistente no host.
- Observação: instalar `psycopg2-binary` pode falhar em alguns ambientes sem dependências de compilação. Se o deploy falhar ao instalar requisitos, remova temporariamente `psycopg2-binary` do `requirements.txt`, faça o deploy e depois configure o banco externo localmente ou via um build que suporte `psycopg2`.

Se quiser, eu posso adicionar exemplos de comandos `psql` para criar o banco, ou um script `migrate.sh` mínimo.
