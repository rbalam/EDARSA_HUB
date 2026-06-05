# backend/modules/edge/servidor_local_contingencia.py

import json
import sqlite3
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Any

DB_PATH = "edarsa_edge_server_master.db"

# ============================================================================
# INITIALIZATION: INMUNICIÓN CENTRAL DE PISO
# ============================================================================
def inicializar_base_servidor_local():
    """
    Crea el contenedor centralizado de piso. Recibe las colas FIFO de todas 
    las terminales para unificar el inventario y la contabilidad local[cite: 237, 285].
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cola_unificada_piso (
                uuid_transaccion TEXT PRIMARY KEY,
                dispositivo_origen TEXT NOT NULL,
                estado TEXT DEFAULT 'PENDING_SYNC',
                payload_json TEXT NOT NULL,
                creado_at INTEGER NOT NULL
            )
        ''')
        conn.commit()

# ============================================================================
# API GATEWAY LOCAL: RECEPTOR DE COMANDAS DE DISPOSITIVOS MÓVILES
# ============================================================================
class EdgeServerRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return # Desactivar logs por consola para maximizar la velocidad de procesamiento

    def do_POST(self):
        """
        Escucha las ráfagas LAN de las tablets. Guarda de forma inmutable el JSON 
        en el disco del servidor local en microsegundos[cite: 238, 318].
        """
        if self.path == "/v1/edge/sincronizar_ticket":
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode('utf-8'))
            
            tx = payload["registro_transaccion"]
            control = payload["offline_payload_control"]
            
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cola_unificada_piso (uuid_transaccion, dispositivo_origen, payload_json, creado_at)
                        VALUES (?, ?, ?, ?)
                    ''', (tx["id_transaccion_global"], control["dispositivo_origen_id"], json.dumps(payload), int(time.time())))
                    conn.commit()
                
                # Respuesta inmediata a la tablet para liberar la interfaz del vendedor [cite: 425]
                self.send_response(202) # Accepted para procesamiento asíncrono
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "LOCAL_CONSOLIDATED", "uuid": tx["id_transaccion_global"]}).encode('utf-8'))
                
            except sqlite3.IntegrityError:
                # Idempotencia: Si el UUID ya existía, se confirma exitoso sin duplicar [cite: 240, 241]
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "IDEMPOTENT_OK"}).encode('utf-8'))

# ============================================================================
# RUNNER: ORQUESTADOR DEL SERVIDOR FÍSICO
# ============================================================================
def ejecutar_servidor_local(puerto: int = 8080):
    inicializar_base_servidor_local()
    server_address = ('', puerto)
    httpd = HTTPServer(server_address, EdgeServerRequestHandler)
    print(f"[EDGE SERVER ALPHA]: Servidor físico de contingencia operativo localmente en puerto {puerto}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

if __name__ == "__main__":
    ejecutar_servidor_local()
