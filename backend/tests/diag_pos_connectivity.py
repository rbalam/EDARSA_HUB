"""
Diagnóstico de conectividad POS desde preview (SOLO LECTURA).
No modifica nada. Reporta: EDARSAHUB OK?, credenciales desencriptables?, red a POS.
"""
import os, sys, socket, time
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

from core.config.edarsahub_config import get_edarsahub_sql_config
from core.sql_first.db import get_sql_connection
from core.secret_manager import decrypt_secret, is_encrypted_secret, validate_secret_key_config

print("=" * 70)
print("PASO 1: SERVER_SECRET_KEY")
print("=" * 70)
print("validate_secret_key_config:", validate_secret_key_config())

print("=" * 70)
print("PASO 2: EDARSAHUB connectivity")
print("=" * 70)
cfg = get_edarsahub_sql_config()
print(f"EDARSAHUB host={cfg.host} port={cfg.port} db={cfg.database} user={cfg.user}")
try:
    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print("EDARSAHUB CONNECT: OK ->", cur.fetchone())
    # Read Servidores_Conexiones
    cur.execute("""
        SELECT id, nombre, host, port, database_name, username,
               CASE WHEN password_encrypted IS NULL OR password_encrypted='' THEN 0 ELSE 1 END AS has_pwd,
               password_encrypted, system_type, tipo_conexion, activo
        FROM Servidores_Conexiones
        WHERE activo = 1
    """)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    print(f"\nServidores_Conexiones activos: {len(rows)}")
    pos_servers = []
    for r in rows:
        pwd_enc = r.get("password_encrypted") or ""
        enc_flag = is_encrypted_secret(pwd_enc)
        dec_ok = False
        dec_len = 0
        try:
            dec = decrypt_secret(pwd_enc)
            dec_ok = True
            dec_len = len(dec or "")
        except Exception as e:
            dec_ok = f"FAIL:{type(e).__name__}"
        print(f"  - id={r['id']} nombre={r['nombre']!r} host={r['host']!r}:{r['port']} "
              f"sys={r['system_type']} tipo={r['tipo_conexion']} "
              f"has_pwd={r['has_pwd']} encrypted={enc_flag} decrypt={dec_ok} pwd_len={dec_len}")
        if r['host']:
            pos_servers.append((r['nombre'], r['host'], int(r['port'] or 1433)))
except Exception as e:
    print("EDARSAHUB CONNECT: FAIL ->", type(e).__name__, str(e)[:300])
    pos_servers = []

print("=" * 70)
print("PASO 3: TCP reachability a cada POS (timeout 6s)")
print("=" * 70)
seen = set()
for nombre, host, port in pos_servers:
    key = (host, port)
    if key in seen:
        continue
    seen.add(key)
    # DNS
    try:
        ip = socket.gethostbyname(host)
        dns = f"DNS->{ip}"
    except Exception as e:
        dns = f"DNS_FAIL:{type(e).__name__}"
        ip = None
    # TCP
    tcp = "n/a"
    if ip:
        t0 = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(6)
        try:
            s.connect((host, port))
            tcp = f"TCP_OPEN ({time.time()-t0:.1f}s)"
        except Exception as e:
            tcp = f"TCP_FAIL:{type(e).__name__} ({time.time()-t0:.1f}s)"
        finally:
            s.close()
    print(f"  - {nombre}: {host}:{port}  {dns}  {tcp}")

print("=" * 70)
print("DIAGNOSTICO COMPLETO")
print("=" * 70)
