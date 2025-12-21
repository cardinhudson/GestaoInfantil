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


def open_browser_once(local_url=None):
    try:
        url = local_url or 'http://localhost:8501'
        webbrowser.open(url)
        logger.info(f'Opened browser at {url}')
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
            while running:
                line = proc.stdout.readline()
                if line == '' and proc.poll() is not None:
                    break
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
