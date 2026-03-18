"""
backup.py — Backup automático do MySQL com criptografia GPG
Destino: local (backups/) + OneDrive (VaccineTransport_Backups/)
Agendamento: Task Scheduler do Windows (ver setup_backup_task.bat)
"""

import os
import sys
import subprocess
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# ── Configuração ───────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parents[2]
ENV_FILE   = BASE_DIR / "source" / "app" / ".env"
MYSQLDUMP  = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
PYTHON_GPG = "gpg"

load_dotenv(ENV_FILE)

DB_HOST      = os.getenv("DB_HOST",      "127.0.0.1")
DB_USER      = os.getenv("DB_USER",      "root")
DB_PASSWORD  = os.getenv("DB_PASSWORD",  "")
DB_NAME      = os.getenv("DB_NAME",      "vaccine_transport")
GPG_PASS     = os.getenv("BACKUP_GPG_PASSPHRASE", "")
LOCAL_DIR    = Path(os.getenv("BACKUP_LOCAL_DIR",    str(BASE_DIR / "backups")))
ONEDRIVE_DIR = Path(os.getenv("BACKUP_ONEDRIVE_DIR", r"C:/Users/guilh/OneDrive/VaccineTransport_Backups"))
KEEP_DAYS    = int(os.getenv("BACKUP_KEEP_DAYS", "30"))

# ── Logging ────────────────────────────────────────────────────────────────────
LOCAL_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOCAL_DIR / "backup.log"

import io
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")),
    ],
)
log = logging.getLogger("backup")


def dump_database(sql_path: Path) -> bool:
    """Executa mysqldump e salva o .sql em sql_path."""
    log.info("Iniciando mysqldump -> %s", sql_path.name)
    cmd = [
        MYSQLDUMP,
        f"--host={DB_HOST}",
        f"--user={DB_USER}",
        f"--password={DB_PASSWORD}",
        "--single-transaction",
        "--routines",
        "--triggers",
        DB_NAME,
    ]
    try:
        with open(sql_path, "w", encoding="utf-8") as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            log.error("mysqldump falhou: %s", result.stderr.strip())
            return False
        size_kb = sql_path.stat().st_size // 1024
        log.info("mysqldump OK — %d KB", size_kb)
        return True
    except FileNotFoundError:
        log.error("mysqldump não encontrado em: %s", MYSQLDUMP)
        return False


def encrypt_file(sql_path: Path, gpg_path: Path) -> bool:
    """Criptografa sql_path com GPG (AES256) → gpg_path."""
    log.info("Criptografando com GPG → %s", gpg_path.name)
    if not GPG_PASS:
        log.error("BACKUP_GPG_PASSPHRASE não definido no .env")
        return False
    cmd = [
        PYTHON_GPG,
        "--batch",
        "--yes",
        "--passphrase", GPG_PASS,
        "--symmetric",
        "--cipher-algo", "AES256",
        "--output", str(gpg_path),
        str(sql_path),
    ]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        log.error("GPG falhou: %s", result.stderr.strip())
        return False
    log.info("GPG OK — arquivo cifrado gerado")
    return True


def copy_to_onedrive(gpg_path: Path) -> bool:
    """Copia o .gpg para a pasta do OneDrive."""
    try:
        ONEDRIVE_DIR.mkdir(parents=True, exist_ok=True)
        dest = ONEDRIVE_DIR / gpg_path.name
        shutil.copy2(gpg_path, dest)
        log.info("OneDrive OK — copiado para %s", dest)
        return True
    except Exception as e:
        log.error("Falha ao copiar para OneDrive: %s", e)
        return False


def cleanup_old_backups():
    """Remove backups locais e do OneDrive com mais de KEEP_DAYS dias."""
    cutoff = datetime.now() - timedelta(days=KEEP_DAYS)
    removed = 0
    for folder in [LOCAL_DIR, ONEDRIVE_DIR]:
        if not folder.exists():
            continue
        for f in folder.glob("backup_*.gpg"):
            if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                f.unlink()
                log.info("Removido backup antigo: %s", f.name)
                removed += 1
    if removed == 0:
        log.info("Nenhum backup antigo para remover (política: %d dias)", KEEP_DAYS)


def run():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    sql_path  = LOCAL_DIR / f"backup_{timestamp}.sql"
    gpg_path  = LOCAL_DIR / f"backup_{timestamp}.sql.gpg"

    log.info("=" * 50)
    log.info("Backup iniciado - %s", timestamp)

    success = True

    # 1. Dump
    if not dump_database(sql_path):
        success = False
    else:
        # 2. Criptografar
        if not encrypt_file(sql_path, gpg_path):
            success = False
        else:
            # 3. Copiar para OneDrive
            copy_to_onedrive(gpg_path)

        # Remove .sql em texto puro após criptografar
        if sql_path.exists():
            sql_path.unlink()
            log.info(".sql em texto puro removido")

    # 4. Limpeza de backups antigos
    cleanup_old_backups()

    if success:
        log.info("Backup concluido com sucesso - %s", gpg_path.name)
    else:
        log.error("Backup FALHOU - verifique o log em %s", LOG_FILE)
        sys.exit(1)

    log.info("=" * 50)


if __name__ == "__main__":
    run()
