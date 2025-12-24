"""Helper para iniciar o app Streamlit localmente e abrir o navegador automaticamente.
Uso: python run_local.py

Ele executa: streamlit run app.py e tenta abrir o URL local no navegador padrão.
"""
import subprocess
import sys
import time
import webbrowser

def _is_port_open(host: str, port: int) -> bool:
    import socket
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except Exception:
        return False


def _open_url(url: str):
    logpath = os.path.join('logs', 'run_local_open.log')
    try:
        with open(logpath, 'a', encoding='utf-8') as logf:
            logf.write(f"[RUN_LOCAL] Tentando abrir URL: {url}\n")

        # Em Windows, tente várias estratégias mais confiáveis
        if os.name == 'nt':
            # 1) os.startfile (rápido e simples)
            try:
                os.startfile(url)
                print('Abrido via os.startfile')
                with open(logpath, 'a', encoding='utf-8') as logf:
                    logf.write('[RUN_LOCAL] Aberto via os.startfile\n')
                return True
            except Exception as e:
                print(f'os.startfile falhou: {e}')
                with open(logpath, 'a', encoding='utf-8') as logf:
                    logf.write(f'[RUN_LOCAL] os.startfile falhou: {e}\n')
            # 2) cmd start (com título vazio) — funciona em ambientes Windows padrão
            try:
                subprocess.run(["cmd", "/c", "start", "", url], check=False, shell=False)
                print('Abrido via cmd start')
                with open(logpath, 'a', encoding='utf-8') as logf:
                    logf.write('[RUN_LOCAL] Aberto via cmd start\n')
                return True
            except Exception as e:
                print(f'cmd start falhou: {e}')
                with open(logpath, 'a', encoding='utf-8') as logf:
                    logf.write(f'[RUN_LOCAL] cmd start falhou: {e}\n')
            # 3) PowerShell Start-Process
            try:
                subprocess.run(["powershell", "-Command", "Start-Process", url], check=False, shell=False)
                print('Abrido via PowerShell Start-Process')
                with open(logpath, 'a', encoding='utf-8') as logf:
                    logf.write('[RUN_LOCAL] Aberto via PowerShell Start-Process\n')
                return True
            except Exception as e:
                print(f'Powershell Start-Process falhou: {e}')
                with open(logpath, 'a', encoding='utf-8') as logf:
                    logf.write(f'[RUN_LOCAL] Powershell Start-Process falhou: {e}\n')

            # 4) Microsoft Edge (microsoft-edge: URL handler)
            try:
                subprocess.run(["cmd", "/c", "start", "", f"microsoft-edge:{url}"], check=False, shell=False)
                print('Abrido via microsoft-edge:')
                with open(logpath, 'a', encoding='utf-8') as logf:
                    logf.write('[RUN_LOCAL] Aberto via microsoft-edge handler\n')
                return True
            except Exception as e:
                with open(logpath, 'a', encoding='utf-8') as logf:
                    logf.write(f'[RUN_LOCAL] microsoft-edge handler falhou: {e}\n')

            # 5) Tentar localizações comuns de navegadores (Chrome, Edge, Firefox)
            common_paths = [
                r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                r"C:\\Program Files\\Mozilla Firefox\\firefox.exe",
                r"C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe",
                r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
                r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            ]
            for path in common_paths:
                try:
                    if os.path.exists(path):
                        subprocess.Popen([path, url], shell=False)
                        print(f'Abrido via {path}')
                        with open(logpath, 'a', encoding='utf-8') as logf:
                            logf.write(f'[RUN_LOCAL] Aberto via exe {path}\n')
                        return True
                except Exception as e:
                    with open(logpath, 'a', encoding='utf-8') as logf:
                        logf.write(f'[RUN_LOCAL] Exec {path} falhou: {e}\n')

        # Fallback genérico (tenta abrir com o módulo webbrowser)
        ok = webbrowser.open(url)
        if ok:
            print('Abrido via webbrowser.open')
            with open(logpath, 'a', encoding='utf-8') as logf:
                logf.write('[RUN_LOCAL] Aberto via webbrowser.open\n')
        else:
            with open(logpath, 'a', encoding='utf-8') as logf:
                logf.write('[RUN_LOCAL] webbrowser.open retornou False\n')
        return ok
    except Exception as exc:
        print(f'Erro ao tentar abrir URL: {exc}')
        with open(logpath, 'a', encoding='utf-8') as logf:
            logf.write(f'[RUN_LOCAL] Erro ao tentar abrir URL: {exc}\n')
        return False


def main():
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless=false"]
    print("Iniciando Streamlit... (Ctrl+C para parar). Usando --server.headless=false para abrir o navegador automaticamente.")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    url = None
    try:
        start = time.time()
        # Primeiro, tentar ler a saída para encontrar a URL (10s)
        while True:
            if proc.stdout is None:
                break
            line = proc.stdout.readline()
            if not line:
                time.sleep(0.1)
            else:
                print(line, end='')
                if 'Local URL:' in line or 'Local URL' in line:
                    parts = line.split()
                    for p in parts:
                        if p.startswith('http'):
                            url = p.strip()
                            break
            if time.time() - start > 10:
                break

        # Se não detectamos a URL na saída, procurar por portas comuns (8501-8510)
        if not url:
            print('Não detectei a URL na saída — tentando portas locais 8501-8510...')
            host = 'localhost'
            found_port = None
            deadline = time.time() + 15
            while time.time() < deadline and found_port is None:
                for port in range(8501, 8511):
                    if _is_port_open(host, port):
                        found_port = port
                        break
                if found_port is None:
                    time.sleep(0.5)
            if found_port:
                url = f'http://{host}:{found_port}'
                print(f'Encontrado servidor em {url}')

        if not url:
            url = 'http://localhost:8501'
            print(f'Usando fallback {url}')

        print(f'Abrindo navegador em {url} ...')
        ok = _open_url(url)
        if not ok:
            print('Falha ao abrir navegador automaticamente; por favor, abra manualmente no endereço acima.')

        # Manter o processo rodando até o usuário interromper
        proc.wait()
    except KeyboardInterrupt:
        print('Interrompendo...')
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    main()
