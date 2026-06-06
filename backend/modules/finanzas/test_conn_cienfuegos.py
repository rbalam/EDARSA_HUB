"""
Archivo desactivado como runtime module.

La prueba manual fue movida a scripts/diagnostico_conexiones/.
No debe abrir conexiones SQL directas dentro de modules/.
"""

def disabled_runtime_test():
    return {
        "status": "disabled",
        "reason": "diagnostico manual movido fuera de runtime modules"
    }
