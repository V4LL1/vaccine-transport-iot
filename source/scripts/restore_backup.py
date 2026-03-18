"""
restore_backup.py — Restaura um backup criptografado (.sql.gpg)
Uso: python restore_backup.py <arquivo.sql.gpg>
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR  = Path(__file__).resolve().parents[2]
ENV_FILE  = BASE_DIR / "source" / "app" / ".env"
MYSQL_BIN = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"

load_dotenv(ENV_FILE)

DB_HOST     = os.getenv("DB_HOST",      "127.0.0.1")
DB_USER     = os.getenv("DB_USER",      "root")
DB_PASSWORD = os.getenv("DB_PASSWORD",  "")
DB_NAME     = os.getenv("DB_NAME",      "vaccine_transport")
GPG_PASS    = os.getenv("BACKUP_GPG_PASSPHRASE", "")


def main():
    if len(sys.argv) < 2:
        print("Uso: python restore_backup.py <arquivo.sql.gpg>")
        sys.exit(1)

    gpg_path = Path(sys.argv[1])
    if not gpg_path.exists():
        print(f"[ERRO] Arquivo não encontrado: {gpg_path}")
        sys.exit(1)

    sql_path = gpg_path.with_suffix("")  # remove .gpg → .sql

    print(f"[1/3] Descriptografando {gpg_path.name}...")
    decrypt_cmd = [
        "gpg", "--batch", "--yes",
        "--passphrase", GPG_PASS,
        "--output", str(sql_path),
        "--decrypt", str(gpg_path),
    ]
    r = subprocess.run(decrypt_cmd, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        print(f"[ERRO] GPG: {r.stderr.strip()}")
        sys.exit(1)
    print(f"[OK]  {sql_path.name} gerado")

    print(f"[2/3] Restaurando no banco {DB_NAME}...")
    restore_cmd = [
        MYSQL_BIN,
        f"--host={DB_HOST}",
        f"--user={DB_USER}",
        f"--password={DB_PASSWORD}",
        DB_NAME,
    ]
    with open(sql_path, "r", encoding="utf-8") as f:
        r = subprocess.run(restore_cmd, stdin=f, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        print(f"[ERRO] MySQL: {r.stderr.strip()}")
        sql_path.unlink(missing_ok=True)
        sys.exit(1)
    print("[OK]  Banco restaurado com sucesso")

    print("[3/3] Removendo .sql temporário...")
    sql_path.unlink()
    print("[OK]  Restauração concluída!")


if __name__ == "__main__":
    main()
