# Gestão Infantil (Streamlit)

Sistema simples para gerenciar tarefas de crianças com pontuação, conversão para horas/dinheiro, validação por responsável e controle de débitos.

Funcionalidades principais:
- Cadastro de integrantes (crianças e responsáveis)
- Cadastro de tarefas com pontos e destino de conversão
- Validação de tarefas por responsáveis
- Conversões pontos→dinheiro e pontos→horas configuráveis
- Registro de débitos (horas/dinheiro)
- Notificações por e-mail (placeholder, configurável via SMTP)

Como usar (local):
1. Criar um venv e instalar dependências:
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt

2. Rodar:
   streamlit run app.py

Dica: para abrir o navegador automaticamente, execute o helper (ele inicia o Streamlit em background e tenta abrir o URL local):
   python run_local.py

Supervisor (reinício e logs) 🛡️
- Para manter o app rodando mesmo que o processo Streamlit pare, use o supervisor (inicia o Streamlit, grava logs e reinicia automaticamente):
   python run_supervisor.py
- Logs do Streamlit e do supervisor ficam em `logs/streamlit.log` com rotação (5MB por arquivo, 5 backups).
- O supervisor tenta abrir o navegador automaticamente ao detectar a "Local URL" na saída do Streamlit.

Se preferir rodar diretamente com `streamlit run`, passe o flag para permitir abertura automática do navegador (sobrescreve `headless` do config):
   streamlit run app.py --server.headless=false

Se seu `.streamlit/config.toml` contém `headless = true`, o Streamlit não abrirá o navegador automaticamente sem o flag acima.

Fotos de usuários 📸
- Você pode adicionar fotos ao criar ou editar usuários no app.
- As fotos são salvas em `uploads/users/` por padrão. Atenção: em serviços como Streamlit Cloud o filesystem pode ser efêmero; para persistência a longo prazo considere integrar um bucket S3 ou armazenar BLOB no DB.

Atalho `run streamlit app.py` (opcional) 🧰
- Criei dois wrappers no repositório para quem quer usar exatamente `run streamlit app.py`:
  - `run.cmd` (para CMD/duplo-clique)
  - `run.ps1` (para PowerShell: use `./run.ps1 streamlit app.py`)

- Observação PowerShell: executar `run streamlit app.py` sem `./` funciona somente se houver um comando chamado `run` no PATH ou se você definir uma função no seu profile.
  Se quiser, adicione a função abaixo ao seu `$PROFILE` (edite com `notepad $PROFILE`) para poder usar `run streamlit app.py` diretamente no PowerShell:

```powershell
function run {
  param($first, [Parameter(ValueFromRemainingArguments=$true)][string[]]$rest)
  if ($first -ieq 'streamlit') { python -m streamlit run @rest --server.headless=false }
  else { & $first @rest }
}
```

- Após adicionar, salve e abra um novo terminal PowerShell; então `run streamlit app.py` funcionará como esperado.

Configurar envio de e-mails (Streamlit Cloud):
- Definir secrets com as chaves SMTP em Settings -> Secrets:
  [smtp]
  server = "smtp.exemplo.com"
  port = 587
  user = "seu@usuario"
  password = "senha"
  from = "app@seu-dominio.com"
  # use_ssl = true  # opcional: usar SMTPS (porta 465). Se falso, será usado STARTTLS (porta 587)

Observações:
- Use `st.secrets` no Streamlit Cloud (Settings -> Secrets). Localmente você pode usar variáveis de ambiente ou um arquivo `.streamlit/secrets.toml`.
- **Importante:** nunca commit este arquivo de secrets no repositório. Para conveniência, você pode criar `.streamlit/secrets.toml` localmente com as chaves (veja exemplo em `.streamlit/secrets.toml.example` ou no repositório), e ele já está listado em `.gitignore`.
- Na página `E-mails` do app há botões para testar a conexão SMTP e enviar um e-mail de teste. Se SMTP não estiver configurado, o sistema apenas simula o envio e loga a mensagem.

Script auxiliar para inserir secrets de forma confidencial
- Para facilitar e não expor credenciais no chat, use o script local `configure_secrets.py` que pede as credenciais de forma segura (senha não é exibida) e grava `.streamlit/secrets.toml` com permissões restritas.

Como usar:
1. Ative seu venv e execute:
   `python configure_secrets.py`
2. Preencha os dados quando solicitado. O script tentará testar a conexão SMTP ao final.
3. Verifique no app (página `E-mails`) com o botão "Testar conexão SMTP".

Notas:
- O projeto usa SQLite para persistência (`gestaoinfantil.db`).
- Autenticação real não está implementada; o usuário atual é selecionado via dropdown.
- Código preparado para integrações futuras.
