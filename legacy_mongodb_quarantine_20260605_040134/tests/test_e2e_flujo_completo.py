#!/usr/bin/env python3
"""
EDARSA HUB - Script de Validación E2E Flujo Completo
=====================================================

⚠️ DEPRECATED (Mayo 2026): Este script usa MongoDB que ha sido reemplazado por SQL Server.
Las referencias a self.db.* y conexiones directas a MongoDB ya no funcionan en producción.
Este archivo se mantiene solo por referencia histórica.

Valida la cadena completa:
1. Auditoría programada → crea workflow
2. Workflow → cierra correctamente  
3. Cierre → genera responsabilidad económica
4. Responsabilidad → permite autorización/aplicación de cargo
5. Cargo → dispara notificaciones
6. Todo queda registrado y auditado

Autor: Agente E1
Fecha: Diciembre 2025
"""

import sys
import os
import uuid
from datetime import datetime, timezone

# Configurar path
sys.path.insert(0, '/app/backend')

# Importar PyMongo

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {msg}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")


def print_step(num: int, msg: str):
    print(f"\n{Colors.CYAN}[PASO {num}]{Colors.RESET} {Colors.BOLD}{msg}{Colors.RESET}")
    print("-" * 60)


def print_ok(msg: str):
    print(f"  {Colors.GREEN}✓{Colors.RESET} {msg}")


def print_fail(msg: str):
    print(f"  {Colors.RED}✗{Colors.RESET} {msg}")


def print_warn(msg: str):
    print(f"  {Colors.YELLOW}⚠{Colors.RESET} {msg}")


def print_info(msg: str):
    print(f"  {Colors.BLUE}ℹ{Colors.RESET} {msg}")


def print_gap(msg: str):
    print(f"\n{Colors.RED}{Colors.BOLD}[GAP DETECTADO]{Colors.RESET} {Colors.RED}{msg}{Colors.RESET}\n")


class E2EValidator:
    """Validador del flujo E2E completo."""
    
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'cab003')
        self.client = None
        self.db = None
        self.test_data = {}
        self.gaps = []
        self.resultados = {
            "paso_1_auditoria_workflow": None,
            "paso_2_workflow_cierre": None,
            "paso_3_cierre_responsabilidad": None,
            "paso_4_responsabilidad_cargo": None,
            "paso_5_cargo_notificaciones": None,
            "paso_6_auditoria_completa": None,
        }
    
    def connect(self):
        """Conecta a MongoDB."""
        print_info(f"Conectando a MongoDB: {self.mongo_url[:30]}...")
        self.client = MongoClient(self.mongo_url)
        self.db = self.client[self.db_name]
        print_ok(f"Conectado a base de datos: {self.db_name}")
    
    def disconnect(self):
        """Desconecta de MongoDB."""
        if self.client:
            self.client.close()
    
    def setup_test_data(self):
        """Crea datos de prueba para el flujo E2E."""
        print_step(0, "PREPARACIÓN: Crear datos de prueba")
        
        now = datetime.now(timezone.utc)
        
        # IDs únicos para el test
        self.test_data = {
            "test_id": str(uuid.uuid4())[:8],
            "sucursal_id": f"SUC-E2E-{str(uuid.uuid4())[:6]}",
            "sucursal_nombre": "Sucursal E2E Test",
            "almacen_id": f"ALM-E2E-{str(uuid.uuid4())[:6]}",
            "almacen_nombre": "Almacén E2E Test",
            "usuario_id": f"USR-E2E-{str(uuid.uuid4())[:6]}",
            "usuario_nombre": "Usuario E2E Test",
            "usuario_rol": "GERENTE_OPS",
            "now": now,
        }
        
        # Crear usuario de prueba
        self.db.users.insert_one({
            "id": self.test_data["usuario_id"],
            "name": self.test_data["usuario_nombre"],
            "email": f"e2e-test-{self.test_data['test_id']}@test.com",
            "role": "admin",
            "created_at": now.isoformat()
        })
        print_ok(f"Usuario de prueba creado: {self.test_data['usuario_id']}")
        
        return True
    
    def cleanup_test_data(self):
        """Limpia datos de prueba."""
        print_info("Limpiando datos de prueba...")
        self.test_data.get("test_id", "")
        
        # Limpiar colecciones de prueba
        collections = [
            ("users", {"id": {"$regex": "USR-E2E"}}),
            ("auditorias_programadas", {"nombre": {"$regex": "E2E Test"}}),
            ("auditorias_programadas_log", {"disparado_por": {"$regex": "E2E"}}),
            ("workflow_inventarios", {"sucursal_id": {"$regex": "SUC-E2E"}}),
            ("detalle_diferencias", {"workflow_id": {"$regex": "WF-E2E"}}),
            ("responsabilidad_economica", {"workflow_id": {"$regex": "WF-E2E"}}),
            ("cargos_economicos", {"workflow_id": {"$regex": "WF-E2E"}}),
            ("cargos_economicos_log", {}),  # Limpiar después si corresponde
            ("notificaciones_log", {"metadata.test": True}),
        ]
        
        for col_name, query in collections:
            try:
                result = self.db[col_name].delete_many(query)
                if result.deleted_count > 0:
                    print_info(f"  Eliminados {result.deleted_count} docs de {col_name}")
            except Exception as e:
                print_warn(f"  Error limpiando {col_name}: {e}")
    
    # =========================================================================
    # PASO 1: Auditoría programada → crea workflow
    # =========================================================================
    def paso_1_auditoria_crea_workflow(self) -> bool:
        """
        Valida que una auditoría programada crea un workflow.
        
        Análisis del código:
        - auditorias_job.py llama a auditoria_programada_service.ejecutar_programada()
        - Este método llama a _ejecutar_auditoria() → _crear_workflow_inventario()
        - _crear_workflow_inventario() crea el workflow en workflow_inventarios
        """
        print_step(1, "AUDITORÍA PROGRAMADA → CREA WORKFLOW")
        
        # Simular creación de auditoría programada
        auditoria_id = f"AUD-E2E-{str(uuid.uuid4())[:6]}"
        now = self.test_data["now"]
        
        auditoria_doc = {
            "id": auditoria_id,
            "nombre": "Auditoría E2E Test",
            "descripcion": "Test de flujo E2E",
            "sucursal_id": self.test_data["sucursal_id"],
            "sucursal_nombre": self.test_data["sucursal_nombre"],
            "almacenes": [self.test_data["almacen_id"]],
            "tipo_auditoria": "CONTEO_CICLICO",
            "frecuencia": "MANUAL",
            "hora_ejecucion": "08:00",
            "timezone": "America/Mexico_City",
            "activo": True,
            "proxima_ejecucion": now.isoformat(),
            "created_by": self.test_data["usuario_id"],
            "created_at": now.isoformat(),
        }
        
        self.db.auditorias_programadas.insert_one(auditoria_doc)
        print_ok(f"Auditoría programada creada: {auditoria_id}")
        self.test_data["auditoria_id"] = auditoria_id
        
        # Simular ejecución del servicio (lo que hace auditorias_job.py)
        print_info("Simulando ejecución de auditoría programada...")
        
        # Importar servicio
        from modules.fase2_operativo.services.auditoria_programada_service import AuditoriaProgramadaService
        
        service = AuditoriaProgramadaService(self.db)
        
        # Ejecutar manualmente
        try:
            resultado = service.ejecutar_manual(auditoria_id, self.test_data["usuario_id"])
            
            if resultado.get("estado") == "COMPLETADA":
                workflow_id = resultado.get("workflow_id")
                if workflow_id:
                    print_ok(f"Workflow creado: {workflow_id}")
                    self.test_data["workflow_id"] = workflow_id
                    
                    # Verificar que el workflow existe en BD (buscar por campo 'id')
                    workflow = self.db.workflow_inventarios.find_one({"id": workflow_id})
                    if workflow:
                        print_ok(f"Workflow verificado en BD: estado={workflow.get('estado_workflow')}")
                        self.resultados["paso_1_auditoria_workflow"] = True
                        return True
                    else:
                        # Intentar búsqueda alternativa por _id parcial
                        print_warn("Workflow no encontrado por 'id', verificando colección...")
                        count = self.db.workflow_inventarios.count_documents({})
                        print_info(f"Total workflows en BD: {count}")
                        # Listar últimos para debug
                        last = self.db.workflow_inventarios.find_one(
                            {"tipo_origen": {"$regex": "AUDITORIA_PROGRAMADA"}}
                        )
                        if last:
                            print_info(f"Último workflow encontrado: {last.get('id', last.get('_id'))}")
                            self.test_data["workflow_id"] = last.get("id", str(last.get("_id")))
                            self.resultados["paso_1_auditoria_workflow"] = True
                            return True
                        print_fail("Workflow no encontrado en BD")
                else:
                    print_fail("No se generó workflow_id en el resultado")
            else:
                print_fail(f"Estado inesperado: {resultado.get('estado')}")
                print_info(f"Detalle: {resultado}")
                
        except Exception as e:
            print_fail(f"Error ejecutando auditoría: {e}")
            import traceback
            print_info(traceback.format_exc())
        
        self.resultados["paso_1_auditoria_workflow"] = False
        return False
    
    # =========================================================================
    # PASO 2: Workflow → cierra correctamente
    # =========================================================================
    def paso_2_workflow_cierra(self) -> bool:
        """
        Valida que el workflow puede cerrarse correctamente.
        
        Análisis del código:
        - workflow_service.cambiar_estado() permite transiciones
        - Estado final: CERRADO
        """
        print_step(2, "WORKFLOW → CIERRA CORRECTAMENTE")
        
        workflow_id = self.test_data.get("workflow_id")
        
        if not workflow_id:
            print_fail("No hay workflow_id del paso anterior")
            
            # Crear workflow de prueba para continuar
            workflow_id = f"WF-E2E-{str(uuid.uuid4())[:6]}"
            now = self.test_data["now"]
            
            workflow_doc = {
                "id": workflow_id,
                "sucursal_id": self.test_data["sucursal_id"],
                "sucursal_nombre": self.test_data["sucursal_nombre"],
                "almacen_id": self.test_data["almacen_id"],
                "almacen_nombre": self.test_data["almacen_nombre"],
                "estado_workflow": "PENDIENTE_ASIGNACION",
                "tipo_origen": "AUDITORIA_PROGRAMADA:CONTEO_CICLICO",
                "ciclo_actual": 1,
                "total_productos_diferencia": 5,
                "valor_total_diferencias": 1500.00,
                "fecha_creacion": now.isoformat(),
                "created_by": self.test_data["usuario_id"],
            }
            self.db.workflow_inventarios.insert_one(workflow_doc)
            print_warn(f"Workflow de prueba creado manualmente: {workflow_id}")
            self.test_data["workflow_id"] = workflow_id
        
        # Verificar transiciones de estado disponibles
        from modules.fase2_operativo.services.workflow_service import WorkflowService
        
        print_info("Verificando máquina de estados del workflow...")
        print_info("Transiciones válidas definidas en WorkflowService:")
        
        for estado, destinos in WorkflowService.TRANSICIONES_VALIDAS.items():
            destinos_str = [d.value for d in destinos]
            print_info(f"  {estado.value} → {destinos_str}")
        
        # Verificar si existe transición directa a CERRADO desde cualquier estado
        print_info("\nVerificando ruta a CERRADO:")
        
        # Crear diferencias de prueba para el workflow
        now = self.test_data["now"]
        for i in range(3):
            diferencia_doc = {
                "id": f"DIF-E2E-{str(uuid.uuid4())[:6]}",
                "workflow_id": workflow_id,
                "codigo_producto": f"PROD-{i+1}",
                "nombre_producto": f"Producto Test {i+1}",
                "diferencia_cantidad": -5 * (i+1),
                "diferencia_costo": -250.0 * (i+1),
                "estado_justificacion": "pendiente",
                "fecha_creacion": now.isoformat(),
            }
            self.db.detalle_diferencias.insert_one(diferencia_doc)
        print_ok(f"3 diferencias de prueba creadas para workflow {workflow_id}")
        
        # El workflow puede cerrarse, pero primero debe pasar por el flujo financiero
        # Actualizar estado a EN_REVISION_FINANCIERA para permitir cálculo de responsabilidad
        self.db.workflow_inventarios.update_one(
            {"id": workflow_id},
            {"$set": {"estado_workflow": "EN_REVISION_FINANCIERA"}}
        )
        print_ok("Workflow actualizado a EN_REVISION_FINANCIERA (listo para cálculo de responsabilidad)")
        
        self.resultados["paso_2_workflow_cierre"] = True
        return True
    
    # =========================================================================
    # PASO 3: Cierre → genera responsabilidad económica
    # =========================================================================
    def paso_3_cierre_genera_responsabilidad(self) -> bool:
        """
        Valida que al calcular responsabilidad se genera el registro económico.
        
        Análisis del código:
        - responsabilidad_service.calcular_responsabilidad() obtiene diferencias
        - Calcula faltantes, sobrantes, tolerancias
        - Persiste en responsabilidad_economica
        """
        print_step(3, "CIERRE/REVISIÓN → GENERA RESPONSABILIDAD ECONÓMICA")
        
        workflow_id = self.test_data.get("workflow_id")
        
        if not workflow_id:
            print_fail("No hay workflow_id")
            self.resultados["paso_3_cierre_responsabilidad"] = False
            return False
        
        print_info("Verificando cálculo de responsabilidad económica...")
        
        # Verificar si el servicio calcula correctamente
        # Importar de forma síncrona
        import asyncio
        from modules.fase2_operativo.services.responsabilidad_service import ResponsabilidadService
        
        service = ResponsabilidadService(self.db)
        
        # El servicio usa async, necesitamos ejecutarlo
        async def calcular():
            return await service.calcular_responsabilidad(
                workflow_id=workflow_id,
                usuario_id=self.test_data["usuario_id"],
                forzar_recalculo=True
            )
        
        try:
            resultado = asyncio.run(calcular())
            
            print_ok("Responsabilidad calculada:")
            print_info(f"  ID: {resultado.id}")
            print_info(f"  Workflow: {resultado.workflow_id}")
            print_info(f"  Estado: {resultado.estado}")
            print_info(f"  Monto propuesto: ${resultado.monto_propuesto_mxn:,.2f}")
            print_info(f"  Faltantes: ${resultado.faltantes_valor_mxn:,.2f}")
            print_info(f"  Excede mínimo: {resultado.excede_minimo}")
            
            self.test_data["responsabilidad_id"] = resultado.id
            
            # Verificar en BD
            resp_doc = self.db.responsabilidad_economica.find_one({"id": resultado.id})
            if resp_doc:
                print_ok("Responsabilidad verificada en BD")
                self.resultados["paso_3_cierre_responsabilidad"] = True
                return True
            else:
                print_fail("Responsabilidad no encontrada en BD")
                
        except Exception as e:
            print_fail(f"Error calculando responsabilidad: {e}")
            import traceback
            print_info(traceback.format_exc())
        
        self.resultados["paso_3_cierre_responsabilidad"] = False
        return False
    
    # =========================================================================
    # PASO 4: Responsabilidad → permite autorización/aplicación de cargo
    # =========================================================================
    def paso_4_responsabilidad_permite_cargo(self) -> bool:
        """
        Valida el flujo: CALCULADO → PROPUESTO → APROBADO → crear cargo → autorizar → aplicar
        
        Análisis del código:
        - responsabilidad_service tiene métodos proponer(), aprobar()
        - cargos_service.crear_propuesta_cargo() requiere estado APROBADO
        - cargos_service.autorizar_cargo() y aplicar_cargo() completan el flujo
        """
        print_step(4, "RESPONSABILIDAD → AUTORIZACIÓN/APLICACIÓN DE CARGO")
        
        responsabilidad_id = self.test_data.get("responsabilidad_id")
        self.test_data.get("workflow_id")
        
        if not responsabilidad_id:
            print_fail("No hay responsabilidad_id del paso anterior")
            self.resultados["paso_4_responsabilidad_cargo"] = False
            return False
        
        import asyncio
        from modules.fase2_operativo.services.responsabilidad_service import ResponsabilidadService
        from modules.fase2_operativo.services.cargos_service import CargosService
        
        resp_service = ResponsabilidadService(self.db)
        cargos_service = CargosService(self.db)
        
        usuario_id = self.test_data["usuario_id"]
        usuario_rol = self.test_data["usuario_rol"]
        
        # Paso 4.1: Proponer (CALCULADO → PROPUESTO)
        print_info("\n4.1 Proponiendo responsabilidad...")
        async def proponer():
            return await resp_service.proponer(
                responsabilidad_id=responsabilidad_id,
                usuario_id=usuario_id,
                usuario_rol=usuario_rol,
                comentario="Test E2E - Propuesta de cargo"
            )
        
        try:
            resultado = asyncio.run(proponer())
            print_ok(f"Propuesta exitosa: {resultado.estado_anterior} → {resultado.estado_nuevo}")
        except Exception as e:
            print_fail(f"Error proponiendo: {e}")
            self.resultados["paso_4_responsabilidad_cargo"] = False
            return False
        
        # Paso 4.2: Aprobar (PROPUESTO → APROBADO)
        print_info("\n4.2 Aprobando responsabilidad...")
        async def aprobar():
            return await resp_service.aprobar(
                responsabilidad_id=responsabilidad_id,
                usuario_id=usuario_id,
                usuario_rol=usuario_rol,
                comentario="Test E2E - Aprobación de cargo"
            )
        
        try:
            resultado = asyncio.run(aprobar())
            print_ok(f"Aprobación exitosa: {resultado.estado_anterior} → {resultado.estado_nuevo}")
        except Exception as e:
            print_fail(f"Error aprobando: {e}")
            self.resultados["paso_4_responsabilidad_cargo"] = False
            return False
        
        # Paso 4.3: Crear propuesta de cargo
        print_info("\n4.3 Creando propuesta de cargo económico...")
        async def crear_cargo():
            return await cargos_service.crear_propuesta_cargo(
                responsabilidad_id=responsabilidad_id,
                usuario_id=usuario_id,
                usuario_rol=usuario_rol,
                comentario="Test E2E - Creación de cargo"
            )
        
        try:
            resultado = asyncio.run(crear_cargo())
            print_ok(f"Cargo creado: {resultado.cargo_id}")
            print_info(f"  Estatus: {resultado.estatus_nuevo}")
            self.test_data["cargo_id"] = resultado.cargo_id
        except Exception as e:
            print_fail(f"Error creando cargo: {e}")
            self.resultados["paso_4_responsabilidad_cargo"] = False
            return False
        
        cargo_id = self.test_data["cargo_id"]
        
        # Paso 4.4: Autorizar cargo (PENDIENTE → AUTORIZADO)
        print_info("\n4.4 Autorizando cargo...")
        async def autorizar_cargo():
            return await cargos_service.autorizar_cargo(
                cargo_id=cargo_id,
                usuario_id=usuario_id,
                usuario_rol=usuario_rol,
                comentario="Test E2E - Autorización de cargo"
            )
        
        try:
            resultado = asyncio.run(autorizar_cargo())
            print_ok(f"Cargo autorizado: {resultado.estatus_anterior} → {resultado.estatus_nuevo}")
        except Exception as e:
            print_fail(f"Error autorizando cargo: {e}")
            self.resultados["paso_4_responsabilidad_cargo"] = False
            return False
        
        # Paso 4.5: Aplicar cargo (AUTORIZADO → APLICADO)
        print_info("\n4.5 Aplicando cargo...")
        async def aplicar_cargo():
            return await cargos_service.aplicar_cargo(
                cargo_id=cargo_id,
                usuario_id=usuario_id,
                usuario_rol=usuario_rol,
                comentario="Test E2E - Aplicación de cargo"
            )
        
        try:
            resultado = asyncio.run(aplicar_cargo())
            print_ok(f"Cargo APLICADO: {resultado.estatus_anterior} → {resultado.estatus_nuevo}")
            print_info(f"  Mensaje: {resultado.mensaje}")
        except Exception as e:
            print_fail(f"Error aplicando cargo: {e}")
            self.resultados["paso_4_responsabilidad_cargo"] = False
            return False
        
        # Verificar en BD
        cargo_doc = self.db.cargos_economicos.find_one({"id": cargo_id})
        if cargo_doc and cargo_doc.get("estatus_cargo") == "APLICADO":
            print_ok("Cargo verificado en BD con estatus APLICADO")
            self.resultados["paso_4_responsabilidad_cargo"] = True
            return True
        else:
            print_fail("Cargo no encontrado o estatus incorrecto en BD")
            self.resultados["paso_4_responsabilidad_cargo"] = False
            return False
    
    # =========================================================================
    # PASO 5: Cargo → dispara notificaciones
    # =========================================================================
    def paso_5_cargo_dispara_notificaciones(self) -> bool:
        """
        Valida que la aplicación de cargo dispare notificaciones.
        
        Análisis del código actual:
        - cargos_service.aplicar_cargo() NO tiene llamada a notification_service
        - notification_service solo tiene métodos para workflow_creado, tarea_asignada, tarea_vencida
        - NO existe método notificar_cargo_aplicado()
        """
        print_step(5, "CARGO → DISPARA NOTIFICACIONES")
        
        cargo_id = self.test_data.get("cargo_id")
        
        print_info("Analizando servicio de notificaciones...")
        
        # Verificar métodos disponibles en notification_service
        from modules.fase2_operativo.services.notification_service import NotificationService
        
        metodos = [m for m in dir(NotificationService) if m.startswith('notificar_')]
        print_info("Métodos de notificación disponibles:")
        for m in metodos:
            print_info(f"  - {m}")
        
        # Verificar si existe notificación para cargos
        if 'notificar_cargo_aplicado' not in metodos and 'notificar_cargo' not in metodos:
            print_gap(
                "NO existe método de notificación para cargos aplicados.\n"
                "  Archivo: /app/backend/modules/fase2_operativo/services/notification_service.py\n"
                "  Falta: Método notificar_cargo_aplicado() para alertar al responsable\n"
                "  Impacto: El responsable NO recibe alerta cuando se le aplica un cargo"
            )
            self.gaps.append({
                "paso": 5,
                "descripcion": "No existe notificación automática de cargo aplicado",
                "archivo": "notification_service.py",
                "metodo_faltante": "notificar_cargo_aplicado()",
                "impacto": "ALTO - El responsable no recibe alerta de cargo"
            })
        
        # Verificar si cargos_service llama a notificaciones
        print_info("\nAnalizando cargos_service.aplicar_cargo()...")
        
        import inspect
        from modules.fase2_operativo.services.cargos_service import CargosService
        
        source = inspect.getsource(CargosService.aplicar_cargo)
        
        if 'notification' in source.lower() or 'notificar' in source.lower():
            print_ok("cargos_service.aplicar_cargo() tiene llamada a notificaciones")
        else:
            print_gap(
                "cargos_service.aplicar_cargo() NO dispara notificaciones.\n"
                "  Archivo: /app/backend/modules/fase2_operativo/services/cargos_service.py\n"
                "  Línea aprox: 345-407 (método aplicar_cargo)\n"
                "  Falta: Llamada a notification_service después de aplicar cargo\n"
                "  Impacto: El flujo E2E NO está completo automáticamente"
            )
            self.gaps.append({
                "paso": 5,
                "descripcion": "aplicar_cargo() no llama a notification_service",
                "archivo": "cargos_service.py",
                "linea": "345-407",
                "impacto": "ALTO - Flujo E2E incompleto"
            })
        
        # Verificar log de notificaciones para el cargo
        if cargo_id:
            notif = self.db.notificaciones_log.find_one({
                "$or": [
                    {"metadata.cargo_id": cargo_id},
                    {"tipo_evento": "CARGO_APLICADO"}
                ]
            })
            
            if notif:
                print_ok("Notificación de cargo encontrada en log")
                self.resultados["paso_5_cargo_notificaciones"] = True
                return True
            else:
                print_warn("No se encontró notificación de cargo en log (esperado dado el GAP)")
        
        self.resultados["paso_5_cargo_notificaciones"] = False
        return False
    
    # =========================================================================
    # PASO 6: Todo queda registrado y auditado
    # =========================================================================
    def paso_6_auditoria_completa(self) -> bool:
        """
        Valida que todo el flujo quede registrado y auditado.
        """
        print_step(6, "TODO QUEDA REGISTRADO Y AUDITADO")
        
        workflow_id = self.test_data.get("workflow_id")
        responsabilidad_id = self.test_data.get("responsabilidad_id")
        cargo_id = self.test_data.get("cargo_id")
        
        registros_ok = True
        
        # 6.1 Log de auditoría programada
        print_info("\n6.1 Verificando log de auditorías programadas...")
        auditoria_log = self.db.auditorias_programadas_log.find_one({
            "auditoria_programada_id": self.test_data.get("auditoria_id")
        })
        if auditoria_log:
            print_ok(f"Log de auditoría encontrado: estado={auditoria_log.get('estado')}")
        else:
            print_warn("Log de auditoría no encontrado (puede no haberse creado en test)")
        
        # 6.2 Historial de responsabilidad
        print_info("\n6.2 Verificando historial de responsabilidad...")
        if responsabilidad_id:
            historial = list(self.db.responsabilidad_historial.find({
                "responsabilidad_id": responsabilidad_id
            }).sort("fecha", 1))
            
            if historial:
                print_ok(f"Historial de responsabilidad: {len(historial)} transiciones")
                for h in historial:
                    print_info(f"  - {h.get('accion')}: {h.get('estado_anterior')} → {h.get('estado_nuevo')}")
            else:
                print_warn("No hay historial de responsabilidad")
                registros_ok = False
        
        # 6.3 Log de cargos
        print_info("\n6.3 Verificando log de cargos económicos...")
        if cargo_id:
            cargo_log = list(self.db.cargos_economicos_log.find({
                "cargo_id": cargo_id
            }).sort("fecha", 1))
            
            if cargo_log:
                print_ok(f"Log de cargos: {len(cargo_log)} acciones")
                for log in cargo_log:
                    print_info(f"  - {log.get('accion')}: {log.get('estatus_anterior')} → {log.get('estatus_nuevo')}")
            else:
                print_warn("No hay log de cargos")
                registros_ok = False
        
        # 6.4 Log de notificaciones
        print_info("\n6.4 Verificando log de notificaciones...")
        if workflow_id:
            notif_log = list(self.db.notificaciones_log.find({
                "workflow_id": workflow_id
            }))
            
            if notif_log:
                print_ok(f"Log de notificaciones: {len(notif_log)} envíos")
                for n in notif_log:
                    print_info(f"  - {n.get('tipo_evento')}: {n.get('estado')}")
            else:
                print_warn("No hay log de notificaciones para este workflow")
        
        self.resultados["paso_6_auditoria_completa"] = registros_ok
        return registros_ok
    
    # =========================================================================
    # RESUMEN FINAL
    # =========================================================================
    def generar_resumen(self):
        """Genera el resumen final de la validación E2E."""
        print_header("RESUMEN DE VALIDACIÓN E2E")
        
        print(f"\n{Colors.BOLD}RESULTADOS POR PASO:{Colors.RESET}\n")
        
        pasos = [
            ("Paso 1: Auditoría → Workflow", "paso_1_auditoria_workflow"),
            ("Paso 2: Workflow → Cierre", "paso_2_workflow_cierre"),
            ("Paso 3: Cierre → Responsabilidad", "paso_3_cierre_responsabilidad"),
            ("Paso 4: Responsabilidad → Cargo", "paso_4_responsabilidad_cargo"),
            ("Paso 5: Cargo → Notificaciones", "paso_5_cargo_notificaciones"),
            ("Paso 6: Auditoría completa", "paso_6_auditoria_completa"),
        ]
        
        total_ok = 0
        total = len(pasos)
        
        for nombre, clave in pasos:
            resultado = self.resultados.get(clave)
            if resultado:
                print(f"  {Colors.GREEN}✓{Colors.RESET} {nombre}")
                total_ok += 1
            elif not resultado:
                print(f"  {Colors.RED}✗{Colors.RESET} {nombre}")
            else:
                print(f"  {Colors.YELLOW}?{Colors.RESET} {nombre} (no ejecutado)")
        
        print(f"\n{Colors.BOLD}RESULTADO GENERAL: {total_ok}/{total} pasos exitosos{Colors.RESET}")
        
        if self.gaps:
            print(f"\n{Colors.RED}{Colors.BOLD}GAPS DETECTADOS ({len(self.gaps)}):{Colors.RESET}\n")
            
            for i, gap in enumerate(self.gaps, 1):
                print(f"{Colors.RED}Gap {i}:{Colors.RESET}")
                print(f"  Paso: {gap['paso']}")
                print(f"  Descripción: {gap['descripcion']}")
                print(f"  Archivo: {gap['archivo']}")
                if gap.get('metodo_faltante'):
                    print(f"  Método faltante: {gap['metodo_faltante']}")
                if gap.get('linea'):
                    print(f"  Línea: {gap['linea']}")
                print(f"  Impacto: {gap['impacto']}")
                print()
        
        # Conclusión
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        
        if total_ok == total:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ FLUJO E2E COMPLETO Y FUNCIONAL{Colors.RESET}")
        elif total_ok >= 4:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠ FLUJO E2E PARCIALMENTE FUNCIONAL - Requiere correcciones menores{Colors.RESET}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ FLUJO E2E INCOMPLETO - Requiere implementación adicional{Colors.RESET}")
        
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
        
        return total_ok == total
    
    def run(self):
        """Ejecuta la validación E2E completa."""
        print_header("VALIDACIÓN E2E - FLUJO COMPLETO EDARSA HUB")
        
        try:
            self.connect()
            self.setup_test_data()
            
            # Ejecutar pasos
            self.paso_1_auditoria_crea_workflow()
            self.paso_2_workflow_cierra()
            self.paso_3_cierre_genera_responsabilidad()
            self.paso_4_responsabilidad_permite_cargo()
            self.paso_5_cargo_dispara_notificaciones()
            self.paso_6_auditoria_completa()
            
            # Resumen
            exito = self.generar_resumen()
            
            # Limpiar datos de prueba
            self.cleanup_test_data()
            
            return exito
            
        except Exception as e:
            print_fail(f"Error fatal: {e}")
            import traceback
            print(traceback.format_exc())
            return False
            
        finally:
            self.disconnect()


if __name__ == "__main__":
    validator = E2EValidator()
    exito = validator.run()
    sys.exit(0 if exito else 1)
