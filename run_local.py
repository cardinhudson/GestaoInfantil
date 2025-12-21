"""Helper para iniciar o app Streamlit localmente e abrir o navegador automaticamente.
Uso: python run_local.py

Ele executa: streamlit run app.py e tenta abrir o URL local no navegador padrão.
"""
import subprocess
import sys
import time
import webbrowser

def main():
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless=false"]
    print("Iniciando Streamlit... (Ctrl+C para parar). Usando --server.headless=false para abrir o navegador automaticamente.")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    url = None
    try:
        # Ler linhas até encontrarmos a URL ou até 10 segundos
        start = time.time()
        while True:
            if proc.stdout is None:
                break
            line = proc.stdout.readline()
            if not line:
                time.sleep(0.1)
            else:
                print(line, end='')
                if 'Local URL:' in line or 'Local URL' in line:
                    # Exemplo: "Local URL: http://localhost:8501"
                    parts = line.split()
                    for p in parts:
                        if p.startswith('http'):
                            url = p.strip()
                            break
                if time.time() - start > 10:
                    break

        if not url:
            url = 'http://localhost:8501'
        print(f'Abrindo navegador em {url} ...')
        webbrowser.open(url)

        # Manter o processo rodando até o usuário interromper
        proc.wait()
    except KeyboardInterrupt:
        print('Interrompendo...')
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    main()
