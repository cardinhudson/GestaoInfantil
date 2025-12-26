"""Script de teste para verificar se as secrets do Supabase estão carregadas corretamente"""
import streamlit as st
import os

st.title("🔍 Teste de Configuração do Supabase")

st.subheader("1. Verificando st.secrets")
try:
    if hasattr(st, 'secrets') and st.secrets:
        st.success("✅ st.secrets está disponível")
        
        # Verificar cada secret
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        bucket = st.secrets.get("SUPABASE_BUCKET", "")
        
        st.write(f"**SUPABASE_URL:** {url if url else '❌ NÃO ENCONTRADO'}")
        st.write(f"**SUPABASE_KEY:** {'✅ Encontrado (' + str(len(key)) + ' caracteres)' if key else '❌ NÃO ENCONTRADO'}")
        st.write(f"**SUPABASE_BUCKET:** {bucket if bucket else '❌ NÃO ENCONTRADO'}")
        
        if key and len(key) > 100:
            st.success(f"✅ SUPABASE_KEY parece válido ({len(key)} caracteres)")
        elif key:
            st.warning(f"⚠️ SUPABASE_KEY muito curto ({len(key)} caracteres) - deve ter mais de 200")
        else:
            st.error("❌ SUPABASE_KEY não foi encontrado!")
    else:
        st.error("❌ st.secrets não está disponível")
except Exception as e:
    st.error(f"❌ Erro ao acessar st.secrets: {e}")

st.subheader("2. Verificando variáveis de ambiente (os.environ)")
url_env = os.environ.get("SUPABASE_URL", "")
key_env = os.environ.get("SUPABASE_KEY", "")
bucket_env = os.environ.get("SUPABASE_BUCKET", "")

st.write(f"**SUPABASE_URL (env):** {url_env if url_env else '❌ NÃO ENCONTRADO'}")
st.write(f"**SUPABASE_KEY (env):** {'✅ Encontrado (' + str(len(key_env)) + ' caracteres)' if key_env else '❌ NÃO ENCONTRADO'}")
st.write(f"**SUPABASE_BUCKET (env):** {bucket_env if bucket_env else '❌ NÃO ENCONTRADO'}")

st.subheader("3. Teste de Upload (Simples)")
if st.button("Testar conexão com Supabase Storage"):
    try:
        import requests
        from services import SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET
        
        st.write(f"**URL:** {SUPABASE_URL}")
        st.write(f"**Bucket:** {SUPABASE_BUCKET}")
        st.write(f"**Key length:** {len(SUPABASE_KEY) if SUPABASE_KEY else 0}")
        
        if not SUPABASE_KEY:
            st.error("❌ SUPABASE_KEY está vazio!")
        else:
            # Testar upload simples
            test_file = b"test content"
            url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/test/test.txt"
            headers = {
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "text/plain",
                "x-upsert": "true"
            }
            
            resp = requests.put(url, headers=headers, data=test_file)
            st.write(f"**Status code:** {resp.status_code}")
            st.write(f"**Response:** {resp.text}")
            
            if resp.ok:
                st.success("✅ Upload de teste bem-sucedido!")
            else:
                st.error(f"❌ Falha no upload: {resp.status_code} - {resp.text}")
    except Exception as e:
        st.error(f"❌ Erro ao testar: {e}")

st.markdown("---")
st.info("""
**Como resolver:**
1. Vá em **Manage app** > **Secrets** no Streamlit Cloud
2. Cole as secrets no formato TOML (veja SUPABASE_SECRETS_GUIDE.md)
3. Salve e reinicie o app
""")
