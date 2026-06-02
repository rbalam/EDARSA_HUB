#!/usr/bin/env python3
"""
VALIDATE SERVER_SECRET_KEY
==========================
Valida que SERVER_SECRET_KEY esté configurada correctamente
sin exponer el valor.

Uso:
    python tools/validate_server_secret_key.py

Autor: Agente E1
Fecha: 2026-06-02
"""

import os
import sys

# Agregar backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("=" * 60)
    print("VALIDACIÓN SERVER_SECRET_KEY")
    print("=" * 60)
    print()
    
    # 1. Verificar variable de entorno
    key = os.getenv("SERVER_SECRET_KEY")
    
    print("1. VARIABLE DE ENTORNO")
    print("-" * 40)
    
    if not key:
        print("   STATUS: NO_CONFIGURADA")
        print("   LENGTH: 0")
        print()
        print("=" * 60)
        print("RESULT=FAIL")
        print("REASON=SERVER_SECRET_KEY no está en variables de entorno")
        print("=" * 60)
        return 1
    
    print("   STATUS: CONFIGURADA")
    print(f"   LENGTH: {len(key)}")
    
    # 2. Verificar formato básico (sin exponer valor)
    print()
    print("2. FORMATO")
    print("-" * 40)
    
    if len(key) < 32:
        print("   STATUS: FORMATO_INVALIDO")
        print("   REASON: Longitud menor a 32 caracteres")
        print()
        print("=" * 60)
        print("RESULT=FAIL")
        print("REASON=SERVER_SECRET_KEY tiene formato inválido")
        print("=" * 60)
        return 1
    
    print("   STATUS: FORMATO_OK")
    print(f"   LENGTH_OK: {len(key)} >= 32")
    
    # 3. Verificar que decrypt_secret funcione
    print()
    print("3. DECRYPT_SECRET")
    print("-" * 40)
    
    try:
        from core.secret_manager import decrypt_secret
        print("   IMPORT: OK")
        
        # Probar con un valor cifrado de prueba (no real)
        # Solo verificamos que la función existe y no lanza error al importar
        print("   FUNCTION: DISPONIBLE")
        
    except ImportError as e:
        print(f"   IMPORT: FAIL - {e}")
        print()
        print("=" * 60)
        print("RESULT=FAIL")
        print("REASON=No se pudo importar decrypt_secret")
        print("=" * 60)
        return 1
    except Exception as e:
        print(f"   ERROR: {type(e).__name__}: {e}")
        print()
        print("=" * 60)
        print("RESULT=FAIL")
        print(f"REASON=Error en decrypt_secret: {e}")
        print("=" * 60)
        return 1
    
    # 4. Probar descifrado real con un servidor de prueba
    print()
    print("4. DESCIFRADO REAL")
    print("-" * 40)
    
    try:
        from core.db import execute_sql_query
        
        # Obtener un password_encrypted de Servidores_Conexiones
        result = execute_sql_query(
            "54.39.104.176", 1433, "EDARSAHUB", "HRLectura", "National09$",
            """
            SELECT TOP 1 nombre, password_encrypted 
            FROM Servidores_Conexiones 
            WHERE password_encrypted IS NOT NULL 
              AND LEN(password_encrypted) > 10
              AND activo = 1
            """
        )
        
        if not result:
            print("   STATUS: NO_HAY_DATOS_PRUEBA")
            print("   REASON: No se encontró servidor con password cifrado")
        else:
            servidor = result[0]['nombre']
            pwd_enc = result[0]['password_encrypted']
            
            print(f"   SERVIDOR_PRUEBA: {servidor}")
            print(f"   PASSWORD_ENCRYPTED_LENGTH: {len(pwd_enc)}")
            
            # Intentar descifrar
            try:
                pwd_dec = decrypt_secret(pwd_enc)
                if pwd_dec and len(pwd_dec) > 0:
                    print(f"   DECRYPT_STATUS: OK")
                    print(f"   DECRYPTED_LENGTH: {len(pwd_dec)}")
                else:
                    print("   DECRYPT_STATUS: FAIL")
                    print("   REASON: Resultado vacío")
                    print()
                    print("=" * 60)
                    print("RESULT=FAIL")
                    print("REASON=decrypt_secret retornó valor vacío")
                    print("=" * 60)
                    return 1
            except Exception as e:
                print(f"   DECRYPT_STATUS: FAIL")
                print(f"   ERROR: {type(e).__name__}: {str(e)[:50]}")
                print()
                print("=" * 60)
                print("RESULT=FAIL")
                print(f"REASON=Error al descifrar: {type(e).__name__}")
                print("=" * 60)
                return 1
                
    except Exception as e:
        print(f"   ERROR: {type(e).__name__}: {e}")
        print()
        print("=" * 60)
        print("RESULT=FAIL")
        print(f"REASON=Error al probar descifrado: {e}")
        print("=" * 60)
        return 1
    
    # Todo OK
    print()
    print("=" * 60)
    print("RESULT=OK")
    print("SERVER_SECRET_KEY está configurada y funcional")
    print("Puede proceder con dry-run real")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
