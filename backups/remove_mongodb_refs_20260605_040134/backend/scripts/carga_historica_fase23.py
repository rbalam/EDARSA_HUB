"""
FASE 2.3 - CARGA HISTÓRICA 24 MESES EN kpis_comercial
=====================================================

⚠️ DEPRECATED (Mayo 2026): Este script usa MongoDB que ha sido reemplazado por SQL Server.
Las referencias a self.db.* ya no funcionan en producción. Este archivo se mantiene
solo por referencia histórica.

PROPÓSITO:
Cargar datos históricos de los últimos 24 meses en la colección kpis_comercial
usando las funciones de servicio existentes y el UPSERT idempotente.

CONDICIONES OBLIGATORIAS:
1. Ejecución controlada y reversible con plan de rollback
2. Bitácora completa de operaciones
3. Validaciones post-carga obligatorias
4. No cierra riesgos abiertos del BLOQUE 4

ESTRATEGIA:
- Procesar mes por mes (batch por mes)
- Usar las mismas funciones que SYNC-S/SYNC-N
- Marcar todos los registros históricos como CERRADO
- No sobrescribir datos recientes (últimos 7 días)

ROLLBACK:
- Opción 1: Eliminar todos los documentos con created_by="carga_historica_2024"
- Opción 2: Restaurar desde backup previo

Fecha: 2026-04-23
Autor: E1 Agent
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import calendar

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path setup
sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

# Configuración
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'edarsa_hub')

# Identificador único de esta carga (para rollback)
CARGA_ID = f"carga_historica_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
UPDATED_BY = "carga_historica_fase23"

# Rango de carga
MESES_HISTORICOS = 24
# No sobrescribir datos de los últimos N días
DIAS_PROTEGIDOS = 7


# =============================================================================
# CLASE PRINCIPAL DE CARGA
# =============================================================================

class CargaHistoricaManager:
    """Gestiona la carga histórica con bitácora y validaciones."""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.bitacora = {
            "carga_id": CARGA_ID,
            "inicio": None,
            "fin": None,
            "estado": "PENDIENTE",
            "rango": {"desde": None, "hasta": None},
            "servidores_procesados": [],
            "totales": {
                "insertados": 0,
                "actualizados": 0,
                "omitidos": 0,
                "errores": 0,
                "rechazados": 0
            },
            "errores_detalle": [],
            "validaciones_post": {},
            "rollback_info": {
                "comando": f"db.kpis_comercial.deleteMany({{created_by: '{UPDATED_BY}'}})",
                "registros_afectados": 0
            }
        }
    
    async def conectar(self):
        """Establece conexión a MongoDB."""
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        logger.info(f"Conectado a MongoDB: {DB_NAME}")
    
    async def desconectar(self):
        """Cierra conexión a MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Desconectado de MongoDB")
    
    def calcular_rango_fechas(self) -> Tuple[str, str]:
        """
        Calcula el rango de fechas para carga histórica.
        
        Returns:
            Tuple (fecha_inicio, fecha_fin) en formato YYYY-MM-DD
        """
        hoy = datetime.now()
        
        # Fecha fin: hace DIAS_PROTEGIDOS días (no sobrescribir recientes)
        fecha_fin = (hoy - timedelta(days=DIAS_PROTEGIDOS)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        # Fecha inicio: hace MESES_HISTORICOS meses desde el primer día del mes actual
        fecha_inicio = hoy.replace(day=1)
        for _ in range(MESES_HISTORICOS):
            fecha_inicio = (fecha_inicio - timedelta(days=1)).replace(day=1)
        
        return (
            fecha_inicio.strftime('%Y-%m-%d'),
            fecha_fin.strftime('%Y-%m-%d')
        )
    
    async def obtener_servidores_activos(self) -> List[Dict]:
        """
        Obtiene servidores configurados para carga.
        Solo SoftRestaurant y MPRO.
        """
        cursor = self.db.servers.find({
            "system_type": {"$in": ["SoftRestaurant", "MPRO"]}
        })
        servers = []
        async for srv in cursor:
            srv['id'] = str(srv['_id'])
            servers.append(srv)
        return servers
    
    async def obtener_empresas(self) -> Dict[str, Dict]:
        """Obtiene mapeo de empresas por ID."""
        cursor = self.db.empresas.find({})
        empresas = {}
        async for emp in cursor:
            empresas[str(emp['_id'])] = {
                "nombre": emp.get('nombre', ''),
                "id": str(emp['_id'])
            }
        return empresas
    
    async def upsert_kpi_historico(
        self,
        server_id: str,
        empresa_id: str,
        sucursal_id: str,
        fecha: str,
        kpis: Dict,
        metadata: Dict
    ) -> str:
        """
        Inserta o actualiza un KPI histórico.
        Usa el repositorio existente con marca de carga histórica.
        
        Returns:
            Acción realizada: INSERT, UPDATE, SKIP, ERROR
        """
        from modules.comercial.kpis_repository import (
            upsert_kpi_comercial,
            init_kpis_repository
        )
        
        # Inicializar repositorio con DB
        init_kpis_repository(self.db)
        
        source_info = {
            "type": "HISTORICO",
            "query_timestamp": datetime.now(timezone.utc).isoformat(),
            "carga_id": CARGA_ID,
            "connection_status": "BATCH_LOAD"
        }
        
        try:
            result = await upsert_kpi_comercial(
                server_id=server_id,
                empresa_id=empresa_id,
                sucursal_id=str(sucursal_id),
                fecha=fecha,
                kpis=kpis,
                source_info=source_info,
                updated_by=UPDATED_BY,
                metadata=metadata,
                force_update=False  # No forzar en períodos CERRADOS
            )
            return result.get("action", "ERROR")
        except Exception as e:
            logger.error(f"Error UPSERT {fecha}/{sucursal_id}: {e}")
            return "ERROR"
    
    async def procesar_mes_sr(
        self,
        server: Dict,
        empresa_id: str,
        anio: int,
        mes: int
    ) -> Dict:
        """
        Procesa un mes de datos para SoftRestaurant.
        
        NOTA: Sin conectividad SQL real, este método simula la estructura
        que obtendría de get_kpis_softrestaurant.
        
        En producción, debería llamar a las funciones de service.py
        con conexión SQL activa.
        """
        stats = {"insertados": 0, "actualizados": 0, "omitidos": 0, "errores": 0}
        
        # Calcular días del mes
        dias_mes = calendar.monthrange(anio, mes)[1]
        
        # En ambiente preview sin SQL, registramos que no hay datos
        # En producción, aquí se llamaría a get_kpis_softrestaurant
        
        logger.info(f"  [SR] {server['name']}: {anio}-{mes:02d} - Sin conectividad SQL (preview)")
        stats["omitidos"] = dias_mes
        
        return stats
    
    async def procesar_mes_mpro(
        self,
        server: Dict,
        empresa_id: str,
        anio: int,
        mes: int
    ) -> Dict:
        """
        Procesa un mes de datos para MPRO.
        Similar a SR pero para sistema MPRO.
        """
        stats = {"insertados": 0, "actualizados": 0, "omitidos": 0, "errores": 0}
        
        dias_mes = calendar.monthrange(anio, mes)[1]
        
        logger.info(f"  [MPRO] {server['name']}: {anio}-{mes:02d} - Sin conectividad SQL (preview)")
        stats["omitidos"] = dias_mes
        
        return stats
    
    async def ejecutar_carga(self, modo_prueba: bool = True) -> Dict:
        """
        Ejecuta la carga histórica completa.
        
        Args:
            modo_prueba: Si True, solo simula sin insertar datos reales
            
        Returns:
            Bitácora de la operación
        """
        self.bitacora["inicio"] = datetime.now(timezone.utc).isoformat()
        self.bitacora["estado"] = "EN_PROGRESO"
        
        try:
            await self.conectar()
            
            # 1. Calcular rango
            fecha_ini, fecha_fin = self.calcular_rango_fechas()
            self.bitacora["rango"] = {"desde": fecha_ini, "hasta": fecha_fin}
            logger.info(f"Rango de carga: {fecha_ini} a {fecha_fin}")
            
            # 2. Obtener servidores
            servidores = await self.obtener_servidores_activos()
            logger.info(f"Servidores a procesar: {len(servidores)}")
            
            if not servidores:
                logger.warning("No hay servidores activos para procesar")
                self.bitacora["estado"] = "SIN_SERVIDORES"
                return self.bitacora
            
            # 3. Obtener empresas
            empresas = await self.obtener_empresas()
            
            # 4. Generar lista de meses
            fecha_actual = datetime.strptime(fecha_ini, '%Y-%m-%d')
            fecha_limite = datetime.strptime(fecha_fin, '%Y-%m-%d')
            
            meses_a_procesar = []
            while fecha_actual <= fecha_limite:
                meses_a_procesar.append((fecha_actual.year, fecha_actual.month))
                # Avanzar al siguiente mes
                if fecha_actual.month == 12:
                    fecha_actual = fecha_actual.replace(year=fecha_actual.year + 1, month=1)
                else:
                    fecha_actual = fecha_actual.replace(month=fecha_actual.month + 1)
            
            logger.info(f"Meses a procesar: {len(meses_a_procesar)}")
            
            # 5. Procesar cada servidor
            for server in servidores:
                server_stats = {
                    "server_id": server.get('id'),
                    "server_name": server.get('name'),
                    "system_type": server.get('system_type'),
                    "meses_procesados": 0,
                    "insertados": 0,
                    "actualizados": 0,
                    "omitidos": 0,
                    "errores": 0
                }
                
                logger.info(f"\nProcesando servidor: {server['name']} ({server.get('system_type')})")
                
                # Obtener empresa del servidor (simplificado)
                empresa_id = server.get('empresa_id') or list(empresas.keys())[0] if empresas else "default"
                
                for anio, mes in meses_a_procesar:
                    if server.get('system_type') == 'SoftRestaurant':
                        stats = await self.procesar_mes_sr(server, empresa_id, anio, mes)
                    elif server.get('system_type') == 'MPRO':
                        stats = await self.procesar_mes_mpro(server, empresa_id, anio, mes)
                    else:
                        continue
                    
                    server_stats["meses_procesados"] += 1
                    server_stats["insertados"] += stats.get("insertados", 0)
                    server_stats["actualizados"] += stats.get("actualizados", 0)
                    server_stats["omitidos"] += stats.get("omitidos", 0)
                    server_stats["errores"] += stats.get("errores", 0)
                
                self.bitacora["servidores_procesados"].append(server_stats)
                self.bitacora["totales"]["insertados"] += server_stats["insertados"]
                self.bitacora["totales"]["actualizados"] += server_stats["actualizados"]
                self.bitacora["totales"]["omitidos"] += server_stats["omitidos"]
                self.bitacora["totales"]["errores"] += server_stats["errores"]
            
            self.bitacora["estado"] = "COMPLETADO"
            
        except Exception as e:
            logger.error(f"Error en carga histórica: {e}")
            self.bitacora["estado"] = "ERROR"
            self.bitacora["errores_detalle"].append(str(e))
        
        finally:
            self.bitacora["fin"] = datetime.now(timezone.utc).isoformat()
            await self.desconectar()
        
        return self.bitacora
    
    async def validar_post_carga(self) -> Dict:
        """
        Ejecuta validaciones post-carga.
        
        Returns:
            Resultado de validaciones
        """
        await self.conectar()
        
        validaciones = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_documentos": 0,
            "duplicados": 0,
            "por_estado": {},
            "rango_fechas": {},
            "por_servidor": [],
            "integridad_ok": False
        }
        
        try:
            # 1. Total documentos
            validaciones["total_documentos"] = await self.db.kpis_comercial.count_documents({})
            
            # 2. Verificar duplicados
            pipeline = [
                {"$group": {
                    "_id": {
                        "server_id": "$server_id",
                        "empresa_id": "$empresa_id",
                        "sucursal_id": "$sucursal_id",
                        "fecha": "$fecha"
                    },
                    "count": {"$sum": 1}
                }},
                {"$match": {"count": {"$gt": 1}}}
            ]
            duplicados = await self.db.kpis_comercial.aggregate(pipeline).to_list(100)
            validaciones["duplicados"] = len(duplicados)
            
            # 3. Conteo por estado
            pipeline_estados = [
                {"$group": {"_id": "$estado_periodo", "count": {"$sum": 1}}}
            ]
            estados = await self.db.kpis_comercial.aggregate(pipeline_estados).to_list(10)
            for e in estados:
                validaciones["por_estado"][e["_id"] or "NULL"] = e["count"]
            
            # 4. Rango de fechas
            min_doc = await self.db.kpis_comercial.find_one(sort=[("fecha", 1)])
            max_doc = await self.db.kpis_comercial.find_one(sort=[("fecha", -1)])
            validaciones["rango_fechas"] = {
                "min": min_doc.get("fecha") if min_doc else None,
                "max": max_doc.get("fecha") if max_doc else None
            }
            
            # 5. Conteo por servidor
            pipeline_servers = [
                {"$group": {"_id": "$server_id", "count": {"$sum": 1}}}
            ]
            servers = await self.db.kpis_comercial.aggregate(pipeline_servers).to_list(20)
            for s in servers:
                validaciones["por_servidor"].append({
                    "server_id": s["_id"],
                    "documentos": s["count"]
                })
            
            # 6. Determinar integridad
            validaciones["integridad_ok"] = (
                validaciones["duplicados"] == 0 and
                validaciones["total_documentos"] > 0
            )
            
        except Exception as e:
            validaciones["error"] = str(e)
        
        finally:
            await self.desconectar()
        
        self.bitacora["validaciones_post"] = validaciones
        return validaciones
    
    def generar_reporte(self) -> str:
        """Genera reporte final de la carga."""
        reporte = []
        reporte.append("=" * 70)
        reporte.append("FASE 2.3 - REPORTE DE CARGA HISTÓRICA")
        reporte.append("=" * 70)
        reporte.append(f"ID de Carga: {self.bitacora['carga_id']}")
        reporte.append(f"Estado: {self.bitacora['estado']}")
        reporte.append(f"Inicio: {self.bitacora['inicio']}")
        reporte.append(f"Fin: {self.bitacora['fin']}")
        reporte.append("")
        
        reporte.append("📅 RANGO PROCESADO:")
        reporte.append(f"  Desde: {self.bitacora['rango'].get('desde')}")
        reporte.append(f"  Hasta: {self.bitacora['rango'].get('hasta')}")
        reporte.append("")
        
        reporte.append("📊 TOTALES:")
        for k, v in self.bitacora['totales'].items():
            reporte.append(f"  {k}: {v}")
        reporte.append("")
        
        reporte.append("🖥️ POR SERVIDOR:")
        for srv in self.bitacora['servidores_procesados']:
            reporte.append(f"  [{srv['system_type']}] {srv['server_name']}:")
            reporte.append(f"    Meses: {srv['meses_procesados']}, Insertados: {srv['insertados']}, Omitidos: {srv['omitidos']}")
        reporte.append("")
        
        if self.bitacora.get('validaciones_post'):
            v = self.bitacora['validaciones_post']
            reporte.append("✅ VALIDACIONES POST-CARGA:")
            reporte.append(f"  Total documentos: {v.get('total_documentos')}")
            reporte.append(f"  Duplicados: {v.get('duplicados')}")
            reporte.append(f"  Integridad OK: {v.get('integridad_ok')}")
            reporte.append(f"  Rango: {v.get('rango_fechas', {}).get('min')} a {v.get('rango_fechas', {}).get('max')}")
            reporte.append("  Por estado:")
            for estado, count in v.get('por_estado', {}).items():
                reporte.append(f"    - {estado}: {count}")
        reporte.append("")
        
        if self.bitacora.get('errores_detalle'):
            reporte.append("❌ ERRORES:")
            for err in self.bitacora['errores_detalle']:
                reporte.append(f"  - {err}")
        reporte.append("")
        
        reporte.append("🔄 INFORMACIÓN DE ROLLBACK:")
        reporte.append(f"  Comando: {self.bitacora['rollback_info']['comando']}")
        reporte.append("")
        
        reporte.append("=" * 70)
        
        return "\n".join(reporte)
    
    def guardar_bitacora(self, path: str):
        """Guarda la bitácora en archivo JSON."""
        with open(path, 'w') as f:
            json.dump(self.bitacora, f, indent=2, default=str)
        logger.info(f"Bitácora guardada en: {path}")


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

async def main():
    """Punto de entrada principal."""
    print("=" * 70)
    print("FASE 2.3 - CARGA HISTÓRICA 24 MESES")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANTE: Este script requiere conectividad SQL a los servidores")
    print("    En ambiente preview sin VPN, la carga será limitada.")
    print()
    
    manager = CargaHistoricaManager()
    
    # Ejecutar carga (modo simulación en preview)
    print("Iniciando carga histórica...")
    bitacora = await manager.ejecutar_carga(modo_prueba=True)
    
    # Ejecutar validaciones
    print("\nEjecutando validaciones post-carga...")
    validaciones = await manager.validar_post_carga()
    
    # Generar reporte
    reporte = manager.generar_reporte()
    print(reporte)
    
    # Guardar bitácora
    bitacora_path = f"/tmp/carga_historica_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    manager.guardar_bitacora(bitacora_path)
    
    return bitacora


if __name__ == "__main__":
    asyncio.run(main())
