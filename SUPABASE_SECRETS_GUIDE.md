# Guia: Configurar Supabase Secrets no Streamlit Cloud

## Passo 1: Obter a Service Role Key do Supabase

1. Acesse o painel do seu projeto Supabase: https://app.supabase.com
2. Selecione seu projeto
3. No menu lateral esquerdo, clique em **Settings** (⚙️)
4. Clique em **API**
5. Na seção **Project API keys**, localize **service_role** (NÃO use a anon/public key!)
6. Clique para revelar e copie **TODA** a chave (ela começa com `eyJ...` e é muito longa - mais de 200 caracteres)

## Passo 2: Configurar Secrets no Streamlit Cloud

1. Acesse seu app no Streamlit Cloud
2. No canto inferior direito, clique em **Manage app**
3. Clique em **Secrets** (ou **⋮** > **Settings** > **Secrets**)
4. **APAGUE TODO O CONTEÚDO** que estiver lá
5. Cole **EXATAMENTE** o texto abaixo (substitua `SUA_SERVICE_ROLE_KEY_AQUI` pela chave copiada):

```toml
SUPABASE_URL = "https://qusavydxnnctnrqfwoua.supabase.co"
SUPABASE_KEY = "SUA_SERVICE_ROLE_KEY_AQUI"
SUPABASE_BUCKET = "user-photos"
```

**Exemplo:**
```toml
SUPABASE_URL = "https://qusavydxnnctnrqfwoua.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1c2F2eWR4bm5jdG5ycWZ3b3VhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjU4MjIyNiwiZXhwIjoyMDgyMTU4MjI2fQ.JUl-ZpeLhO5WNxwBrQpaVFXi60pzBLl1IbTGHh0Ijfo"
SUPABASE_BUCKET = "user-photos"
```

6. Clique em **Save**
7. Reinicie o app

## Passo 3: Verificar o Bucket no Supabase Storage

1. No painel do Supabase, vá em **Storage** (menu lateral esquerdo)
2. Verifique se o bucket **user-photos** existe
3. Se não existir, clique em **New bucket** e crie um bucket com nome **user-photos**
4. Configure as permissões (RLS Policy) se necessário

## Checklist de Verificação

- [ ] A service_role key foi copiada COMPLETA (não cortada)
- [ ] As aspas duplas estão presentes ao redor dos valores
- [ ] Não há espaços extras antes/depois do `=`
- [ ] O nome do bucket está exatamente igual ao do Supabase Storage
- [ ] As secrets foram salvas no Streamlit Cloud
- [ ] O app foi reiniciado após salvar as secrets

## Solução de Problemas

Se o erro "Invalid Compact JWS" persistir:
1. Certifique-se de que está usando a **service_role** key, NÃO a anon/public key
2. Verifique se a chave não está truncada (deve ter mais de 200 caracteres)
3. Apague e recrie as secrets no Streamlit Cloud
4. Reinicie o app após cada alteração

Se o aviso "[AVISO] SUPABASE_KEY não foi carregada!" aparecer:
1. Verifique se as secrets foram salvas corretamente no painel do Streamlit Cloud
2. Confirme que o formato TOML está correto (aspas duplas, sem erros de sintaxe)
3. Reinicie o app

## Contato

Para mais informações, consulte:
- Documentação do Supabase Storage: https://supabase.com/docs/guides/storage
- Documentação do Streamlit Secrets: https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management
