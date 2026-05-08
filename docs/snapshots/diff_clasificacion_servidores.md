=== DIFF DE CAMBIOS REALIZADOS ===
Fecha: 2026-04-20 16:53

diff --git a/backend/modules/comercial/repository.py b/backend/modules/comercial/repository.py
index 4d51bc5..906e359 100644
--- a/backend/modules/comercial/repository.py
+++ b/backend/modules/comercial/repository.py
@@ -49,12 +49,25 @@ async def get_server_by_id(server_id: str) -> Optional[Dict]:
 
 
 async def get_servers_for_tablero() -> List[Dict]:
-    """Obtiene servidores visibles para el tablero ejecutivo."""
+    """
+    Obtiene servidores visibles para el tablero ejecutivo.
+    Solo devuelve conexiones DATA_SOURCE (excluye CORE del sistema).
+    """
     cursor = get_db().servers.find(
-        {"active": True, "visible_en_operaciones": {"$ne": False}},
+        {
+            "active": True, 
+            "visible_en_operaciones": {"$ne": False},
+            # ============ CLASIFICACIÓN: Excluir CORE ============
+            "$or": [
+                {"tipo_conexion": {"$exists": False}},  # Backward compatible
+                {"tipo_conexion": "DATA_SOURCE"}
+            ]
+        },
         {"_id": 0}
     )
-    return await cursor.to_list(100)
+    servers = await cursor.to_list(100)
+    # Filtro adicional por si acaso
+    return [s for s in servers if s.get("tipo_conexion") != "CORE"]
 
 
 async def get_sucursales_visibles_config(server_id: str) -> Dict[str, bool]:
diff --git a/backend/server.py b/backend/server.py
index cf9f08f..4add615 100644
--- a/backend/server.py
+++ b/backend/server.py
@@ -362,7 +362,7 @@ class Server(BaseModel):
     port: int = 1433
     database: str
     username: str
-    system_type: str  # "MPRO", "SoftRestaurant", "Otro"
+    system_type: str  # "MPRO", "SoftRestaurant", "Otro", "EDARSA_HUB"
     date_calculation_method: str = "inventory_dates"  # Método para calcular fechas de ventas
     sucursales: List[str] = []  # IDs de sucursales
     # Filtros configurables para consultas
@@ -377,6 +377,13 @@ class Server(BaseModel):
     visible_en_operaciones: bool = True  # Si se muestra en dashboards y menús operativos
     active: bool = True
     created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
+    # ============ CLASIFICACIÓN DE CONEXIÓN (2026-04-20) ============
+    # Permite separar conexiones CORE (cerebro del sistema) de DATA_SOURCE (fuentes externas)
+    tipo_conexion: str = "DATA_SOURCE"  # "DATA_SOURCE" | "CORE"
+    visible_en_listado: bool = True  # Si aparece en el menú de servidores de UI
+    es_editable_ui: bool = True  # Si se puede editar desde UI estándar
+    es_eliminable_ui: bool = True  # Si se puede eliminar desde UI estándar
+    uso_sistema: Optional[str] = None  # "CORE_DB" | "RH_INTERNO" | null para fuentes externas
 
 class ServerCreate(BaseModel):
     name: str
@@ -929,7 +936,23 @@ async def create_server(server_data: ServerCreate, current_user: Dict = Depends(
 
 @api_router.get("/servers", response_model=List[Server])
 async def get_servers(current_user: Dict = Depends(get_current_user)):
-    servers = await db.servers.find({"active": True}, {"_id": 0, "password": 0}).to_list(1000)
+    # ============ CLASIFICACIÓN: Solo mostrar DATA_SOURCE en listado UI ============
+    # Las conexiones CORE (cerebro del sistema) no deben aparecer en el menú de servidores
+    servers = await db.servers.find(
+        {
+            "active": True,
+            "$or": [
+                {"tipo_conexion": {"$exists": False}},  # Backward compatible
+                {"tipo_conexion": "DATA_SOURCE"},
+                {"visible_en_listado": True}
+            ]
+        },
+        {"_id": 0, "password": 0}
+    ).to_list(1000)
+    
+    # Filtrar explícitamente los que tienen tipo_conexion=CORE
+    servers = [s for s in servers if s.get("tipo_conexion") != "CORE"]
+    
     # Filtrar según permisos
     return filter_servers_by_permissions(servers, current_user)
 
@@ -953,11 +976,22 @@ async def update_server(server_id: str, server_data: Dict, current_user: Dict =
     if not existing:
         raise HTTPException(status_code=404, detail="Servidor no encontrado")
     
+    # ============ PROTECCIÓN CORE: No permitir edición desde UI estándar ============
+    if existing.get("tipo_conexion") == "CORE" or existing.get("es_editable_ui") == False:
+        raise HTTPException(
+            status_code=403, 
+            detail="Esta conexión es del sistema central (CORE) y no puede ser modificada desde la interfaz"
+        )
+    
     # Si no se envía contraseña, mantener la existente
     update_data = {k: v for k, v in server_data.items() if v is not None and v != ''}
     if 'password' not in update_data or not update_data.get('password'):
         update_data.pop('password', None)  # No actualizar la contraseña si está vacía
     
+    # Prevenir que desde UI se cambie a tipo CORE
+    if update_data.get("tipo_conexion") == "CORE":
+        raise HTTPException(status_code=403, detail="No se puede cambiar el tipo de conexión a CORE desde UI")
+    
     # Actualizar timestamp
     update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
     
@@ -969,6 +1003,14 @@ async def delete_server(server_id: str, current_user: Dict = Depends(get_current
     if current_user['role'] != 'Administrador':
         raise HTTPException(status_code=403, detail="No autorizado")
     
+    # ============ PROTECCIÓN CORE: No permitir eliminación desde UI estándar ============
+    existing = await db.servers.find_one({"id": server_id})
+    if existing and (existing.get("tipo_conexion") == "CORE" or existing.get("es_eliminable_ui") == False):
+        raise HTTPException(
+            status_code=403, 
+            detail="Esta conexión es del sistema central (CORE) y no puede ser eliminada desde la interfaz"
+        )
+    
     await db.servers.update_one({"id": server_id}, {"$set": {"active": False}})
     return {"message": "Servidor desactivado"}
 
