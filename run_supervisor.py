"""run_supervisor.py

Supervisor simples para executar o Streamlit em loop, registrar stdout/stderr em arquivo rotativo
e re-iniciar o processo automaticamente se ele terminar. Útil para desenvolvimento local.

Uso: python run_supervisor.py
"""
import subprocess
import sys
import time
import webbrowser
import logging
from logging.handlers import RotatingFileHandler
import os
import signal

LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'streamlit.log')
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5

# Configurar logger
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger('supervisor')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
console = logging.StreamHandler(sys.stdout)
console.setFormatter(formatter)
logger.addHandler(console)

# Comando a executar
CMD = [sys.executable, '-m', 'streamlit', 'run', 'app.py', '--server.headless=false']

# Control flags
running = True


def _is_port_open(host: str, port: int) -> bool:
    import socket
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except Exception:
        return False


def _open_url(url: str) -> bool:
    open_log = os.path.join(LOG_DIR, 'supervisor_open.log')
    try:
        with open(open_log, 'a', encoding='utf-8') as f:
            f.write(f"[SUPERVISOR] Attempting to open URL: {url}\n")

        # Windows-specific strategies
        if os.name == 'nt':
            try:
                os.startfile(url)
                logger.info(f'Opened browser via os.startfile: {url}')
                with open(open_log, 'a', encoding='utf-8') as f:
                    f.write('[SUPERVISOR] Opened via os.startfile\n')
                return True
            except Exception as e:
                logger.debug(f'os.startfile failed: {e}')

            try:
                subprocess.run(["cmd", "/c", "start", "", url], check=False, shell=False)
                logger.info(f'Opened browser via cmd start: {url}')
                with open(open_log, 'a', encoding='utf-8') as f:
                    f.write('[SUPERVISOR] Opened via cmd start\n')
                return True
            except Exception as e:
                logger.debug(f'cmd start failed: {e}')

            try:
                subprocess.run(["powershell", "-Command", "Start-Process", url], check=False, shell=False)
                logger.info(f'Opened browser via PowerShell Start-Process: {url}')
                with open(open_log, 'a', encoding='utf-8') as f:
                    f.write('[SUPERVISOR] Opened via PowerShell Start-Process\n')
                return True
            except Exception as e:
                logger.debug(f'PowerShell Start-Process failed: {e}')

            # microsoft-edge: handler
            try:
                subprocess.run(["cmd", "/c", "start", "", f"microsoft-edge:{url}"], check=False, shell=False)
                logger.info(f'Opened via microsoft-edge handler: {url}')
                with open(open_log, 'a', encoding='utf-8') as f:
                    f.write('[SUPERVISOR] Opened via microsoft-edge handler\n')
                return True
            except Exception:
                pass

            # Try common browser executables
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
                        logger.info(f'Opened via exe {path}: {url}')
                        with open(open_log, 'a', encoding='utf-8') as f:
                            f.write(f'[SUPERVISOR] Opened via exe {path}\n')
                        return True
                except Exception:
                    pass

        # Generic fallback
        ok = webbrowser.open(url)
        if ok:
            logger.info(f'Opened browser via webbrowser.open: {url}')
            with open(open_log, 'a', encoding='utf-8') as f:
                f.write('[SUPERVISOR] Opened via webbrowser.open\n')
        else:
            with open(open_log, 'a', encoding='utf-8') as f:
                f.write('[SUPERVISOR] webbrowser.open returned False\n')
        return bool(ok)
    except Exception as exc:
        logger.exception('Failed to open browser')
        try:
            with open(open_log, 'a', encoding='utf-8') as f:
                f.write(f'[SUPERVISOR] Exception opening URL: {exc}\n')
        except Exception:
            pass
        return False


def open_browser_once(local_url=None):
    try:
        url = local_url or 'http://localhost:8501'
        ok = _open_url(url)
        if ok:
            logger.info(f'Opened browser at {url}')
        else:
            logger.warning(f'Could not open browser at {url}')
    except Exception:
        logger.exception('Failed to open browser')


def run_loop():
    global running
    restart_count = 0
    backoff = 1
    opened_browser = False

    def _handle_sigterm(signum, frame):
        global running
        logger.info('Supervisor received termination signal; stopping...')
        running = False

    signal.signal(signal.SIGINT, _handle_sigterm)
    signal.signal(signal.SIGTERM, _handle_sigterm)

    while running:
        logger.info(f'Starting Streamlit (cmd: {CMD})')
        start_time = time.time()
        proc = subprocess.Popen(CMD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # Ler e logar linhas de stdout do processo
        try:
            port_check_done = False
            while running:
                line = proc.stdout.readline()
                if line == '' and proc.poll() is not None:
                    break
                now = time.time()
                if line:
                    logger.info(line.rstrip())
                    # Ao detectar a Local URL na saída, tentar abrir o navegador (uma vez)
                    if not opened_browser and 'Local URL' in line:
                        parts = line.split()
                        for p in parts:
                            if p.startswith('http'):
                                open_browser_once(p.strip())
                                opened_browser = True
                                break
                else:
                    time.sleep(0.1)

                # Se após alguns segundos não detectamos a URL na saída, tentar detectar porta aberta e abrir
                if not opened_browser and not port_check_done and (now - start_time) > 5:
                    logger.info('Nenhuma Local URL detectada ainda; tentando detectar porta local (8501-8510)')
                    host = 'localhost'
                    found_port = None
                    deadline = time.time() + 10
                    while time.time() < deadline and found_port is None:
                        for port in range(8501, 8511):
                            if _is_port_open(host, port):
                                found_port = port
                                break
                        if found_port is None:
                            time.sleep(0.5)
                    if found_port:
                        url = f'http://{host}:{found_port}'
                        logger.info(f'Encontrado servidor em {url}; abrindo navegador')
                        open_browser_once(url)
                        opened_browser = True
                    else:
                        logger.info('Nenhuma porta detectada entre 8501-8510')
                    port_check_done = True
        except Exception:
            logger.exception('Erro lendo stdout do processo')

        # Processo terminou
        rc = proc.poll()
        run_duration = time.time() - start_time
        logger.warning(f'Process exited with return code {rc} (ran {run_duration:.1f}s)')
        restart_count += 1

        if not running:
            break

        # Se o processo rodou por tempo razoável, resetar backoff
        if run_duration > 10:
            backoff = 1
            logger.info('Process ran >10s, resetting backoff to 1s')
        else:
            backoff = min(backoff * 2, 60)

        logger.info(f'Restarting in {backoff} seconds (attempt {restart_count})')
        time.sleep(backoff)

    logger.info('Supervisor exiting')


if __name__ == '__main__':
    run_loop()
