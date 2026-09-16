from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

CONFIG_TABLE = 'dbo.Sistema_NotificacionesConfig'
QUEUE_TABLE = 'dbo.Operativo_Notificaciones_Queue'
LOG_TABLE = 'dbo.Operativo_Notificaciones_Log'


def _value(value):
    return getattr(value, 'value', value)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=lambda obj: getattr(obj, 'value', str(obj)))


class NotificationRepository:
    def __init__(self, db=None):
        self.db = db

    def _conn(self):
        return get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)

    def _rows(self, sql: str, params: tuple = ()) -> List[Dict]:
        conn = self._conn()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(sql, params)
            return cur.fetchall() or []
        finally:
            conn.close()

    def _doc(self, obj: Any) -> Dict:
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return dict(obj)
        if hasattr(obj, 'model_dump'):
            return obj.model_dump(mode='json')
        if hasattr(obj, 'dict'):
            return obj.dict()
        return dict(getattr(obj, '__dict__', {}) or {})

    def _decode_config(self, row: Dict) -> Dict:
        try:
            doc = json.loads(row.get('PayloadMongo') or '{}')
        except (TypeError, ValueError, json.JSONDecodeError):
            doc = {}
        if not isinstance(doc, dict):
            doc = {}
        doc.setdefault('id', str(row.get('Id')))
        doc['_sql_id'] = str(row.get('Id'))
        doc['_sql_collection'] = row.get('ColeccionOrigen')
        if 'activo' not in doc:
            doc['activo'] = bool(row.get('Activo'))
        return doc

    def _kind(self, row: Dict, doc: Dict) -> str:
        source = str(row.get('ColeccionOrigen') or '').lower()
        if 'template' in source or ('template_texto' in doc and 'codigo' in doc):
            return 'template'
        if 'provider' in source or ('provider' in doc and 'evento' not in doc and 'template_codigo' not in doc):
            return 'provider'
        if 'config' in source or 'evento' in doc:
            return 'config'
        return 'unknown'

    def _all_config_rows(self) -> List[Dict]:
        return self._rows(f"SELECT Id,MongoId,ColeccionOrigen,PayloadMongo,MigradoDesdeMongo,Activo,FechaCreacion,FechaActualizacion FROM {CONFIG_TABLE}")

    def _documents(self, kind: str) -> List[Dict]:
        items = []
        for row in self._all_config_rows():
            doc = self._decode_config(row)
            if self._kind(row, doc) == kind:
                items.append(doc)
        return items

    def _find_document(self, kind: str, document_id: str) -> Optional[Dict]:
        needle = str(document_id)
        for doc in self._documents(kind):
            if needle in {str(doc.get('id')), str(doc.get('_sql_id'))}:
                return doc
        return None

    def _insert_document(self, kind: str, obj: Any) -> Dict:
        doc = self._doc(obj)
        document_id = str(doc.get('id') or uuid.uuid4())
        try:
            sql_id = str(uuid.UUID(document_id))
        except (ValueError, TypeError, AttributeError):
            sql_id = str(uuid.uuid4())
        doc['id'] = document_id
        active = 1 if bool(doc.get('activo', True)) else 0
        collection = {'config':'notification_config','provider':'notification_provider_config','template':'notification_templates'}[kind]
        mongo_id = f'sqlfirst:{kind}:{document_id}'[:200]
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(f"INSERT INTO {CONFIG_TABLE} (Id,MongoId,ColeccionOrigen,PayloadMongo,MigradoDesdeMongo,Activo,FechaMigracion,FechaCreacion) VALUES (%s,%s,%s,%s,0,%s,GETDATE(),GETDATE())", (sql_id,mongo_id,collection,_json(doc),active))
            conn.commit()
        except Exception:
            conn.rollback(); raise
        finally:
            conn.close()
        return doc

    def _update_document(self, kind: str, document_id: str, updates: Dict) -> Optional[Dict]:
        current = self._find_document(kind, document_id)
        if not current:
            return None
        sql_id = current.pop('_sql_id', None)
        current.pop('_sql_collection', None)
        current.update({k:_value(v) for k,v in updates.items()})
        active = 1 if bool(current.get('activo', True)) else 0
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(f"UPDATE {CONFIG_TABLE} SET PayloadMongo=%s,Activo=%s,FechaActualizacion=GETDATE() WHERE Id=%s", (_json(current),active,sql_id))
            if cur.rowcount != 1:
                conn.rollback(); return None
            conn.commit()
        except Exception:
            conn.rollback(); raise
        finally:
            conn.close()
        return current

    def _deactivate_document(self, kind: str, document_id: str) -> bool:
        return self._update_document(kind, document_id, {'activo':False}) is not None

    async def get_config(self, canal: str, modulo: str, evento: str) -> Optional[Dict]:
        canal = str(_value(canal) or '').lower(); modulo = str(modulo or '').lower(); evento = str(_value(evento) or '').lower()
        for doc in self._documents('config'):
            if str(_value(doc.get('canal')) or '').lower()==canal and str(doc.get('modulo') or '').lower()==modulo and str(_value(doc.get('evento')) or '').lower()==evento and doc.get('activo',True):
                return doc
        return None

    async def get_all_configs(self, modulo:Optional[str]=None, canal:Optional[str]=None, activo:Optional[bool]=None) -> List[Dict]:
        items=self._documents('config')
        if modulo is not None: items=[x for x in items if str(x.get('modulo') or '').lower()==str(modulo).lower()]
        if canal is not None: items=[x for x in items if str(_value(x.get('canal')) or '').lower()==str(canal).lower()]
        if activo is not None: items=[x for x in items if bool(x.get('activo',True))==bool(activo)]
        return items

    async def create_config(self, config) -> Dict: return self._insert_document('config',config)
    async def update_config(self, config_id:str, updates:Dict) -> Optional[Dict]: return self._update_document('config',config_id,updates)
    async def delete_config(self, config_id:str) -> bool: return self._deactivate_document('config',config_id)

    async def get_all_provider_configs(self, canal:Optional[str]=None, activo:Optional[bool]=None) -> List[Dict]:
        items=self._documents('provider')
        if canal is not None: items=[x for x in items if str(_value(x.get('canal')) or '').lower()==str(canal).lower()]
        if activo is not None: items=[x for x in items if bool(x.get('activo',True))==bool(activo)]
        return items

    async def get_provider_config(self, canal:str, provider:str) -> Optional[Dict]:
        for doc in await self.get_all_provider_configs(canal=canal,activo=True):
            if str(doc.get('provider') or '').lower()==str(provider).lower(): return doc
        return None

    async def get_active_provider(self, canal:str) -> Optional[Dict]:
        items=await self.get_all_provider_configs(canal=canal,activo=True); return items[0] if items else None
    async def create_provider_config(self, config) -> Dict: return self._insert_document('provider',config)
    async def update_provider_config(self, config_id:str, updates:Dict) -> Optional[Dict]: return self._update_document('provider',config_id,updates)

    async def get_template(self, canal:str, codigo:str) -> Optional[Dict]:
        for doc in self._documents('template'):
            if str(_value(doc.get('canal')) or '').lower()==str(canal).lower() and str(doc.get('codigo') or '').lower()==str(codigo).lower() and doc.get('activo',True): return doc
        return None
    async def get_template_by_id(self, template_id:str) -> Optional[Dict]: return self._find_document('template',template_id)
    async def get_all_templates(self, canal:Optional[str]=None, activo:Optional[bool]=None) -> List[Dict]:
        items=self._documents('template')
        if canal is not None: items=[x for x in items if str(_value(x.get('canal')) or '').lower()==str(canal).lower()]
        if activo is not None: items=[x for x in items if bool(x.get('activo',True))==bool(activo)]
        return items
    async def create_template(self, template) -> Dict: return self._insert_document('template',template)
    async def update_template(self, template_id:str, updates:Dict) -> Optional[Dict]: return self._update_document('template',template_id,updates)
    async def delete_template(self, template_id:str) -> bool: return self._deactivate_document('template',template_id)

    async def enqueue(self, item) -> Dict:
        doc=self._doc(item); qid=str(doc.get('id') or uuid.uuid4()); doc['id']=qid
        conn=self._conn()
        try:
            cur=conn.cursor(); cur.execute(f"INSERT INTO {QUEUE_TABLE} (ID,Canal,Modulo,EventoNegocio,ReferenciaID,WorkflowID,TareaID,Prioridad,DestinatariosJSON,TemplateCodigo,PayloadJSON,PayloadRenderizado,Estado,Intentos,ProximoIntentoUTC,CreatedAtUTC) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,SYSUTCDATETIME())",(qid,str(_value(doc.get('canal') or 'whatsapp')),doc.get('modulo') or 'inventarios',str(_value(doc.get('evento_negocio') or 'NOTIFICACION')),doc.get('referencia_id'),doc.get('workflow_id'),doc.get('tarea_id'),int(doc.get('prioridad') or 3),_json(doc.get('destinatarios') or []),doc.get('template_codigo'),_json(doc.get('payload') or {}),doc.get('payload_renderizado'),str(_value(doc.get('estado') or 'pendiente')),int(doc.get('intentos') or 0),doc.get('proximo_intento'))); conn.commit()
        except Exception:
            conn.rollback(); raise
        finally: conn.close()
        return doc

    def _queue_doc(self,row:Dict)->Dict:
        def loads(value,default):
            try: return json.loads(value) if value else default
            except Exception: return default
        return {'id':str(row.get('ID')),'canal':row.get('Canal'),'modulo':row.get('Modulo'),'evento_negocio':row.get('EventoNegocio'),'referencia_id':row.get('ReferenciaID'),'workflow_id':row.get('WorkflowID'),'tarea_id':row.get('TareaID'),'prioridad':row.get('Prioridad'),'destinatarios':loads(row.get('DestinatariosJSON'),[]),'template_codigo':row.get('TemplateCodigo'),'payload':loads(row.get('PayloadJSON'),{}),'payload_renderizado':row.get('PayloadRenderizado'),'estado':row.get('Estado'),'intentos':row.get('Intentos') or 0,'proximo_intento':row.get('ProximoIntentoUTC'),'locked_at':row.get('LockedAtUTC'),'locked_by':row.get('LockedBy'),'created_at':row.get('CreatedAtUTC'),'updated_at':row.get('UpdatedAtUTC'),'error':row.get('ErrorMensaje')}

    async def get_pending_items(self,limit:int=50)->List[Dict]:
        safe=max(1,min(int(limit),200)); rows=self._rows(f"SELECT TOP ({safe}) * FROM {QUEUE_TABLE} WHERE Estado='pendiente' AND (ProximoIntentoUTC IS NULL OR ProximoIntentoUTC<=SYSUTCDATETIME()) AND (LockedAtUTC IS NULL OR LockedAtUTC<DATEADD(minute,-10,SYSUTCDATETIME())) ORDER BY Prioridad ASC,CreatedAtUTC ASC"); return [self._queue_doc(r) for r in rows]

    async def lock_item(self,queue_id:str,worker_id:str)->bool:
        conn=self._conn()
        try:
            cur=conn.cursor(); cur.execute(f"UPDATE {QUEUE_TABLE} WITH (ROWLOCK,UPDLOCK) SET LockedAtUTC=SYSUTCDATETIME(),LockedBy=%s,UpdatedAtUTC=SYSUTCDATETIME() WHERE ID=%s AND Estado='pendiente' AND (LockedAtUTC IS NULL OR LockedAtUTC<DATEADD(minute,-10,SYSUTCDATETIME()))",(str(worker_id)[:100],queue_id)); ok=cur.rowcount==1; conn.commit(); return ok
        except Exception:
            conn.rollback(); raise
        finally: conn.close()

    async def update_queue_item(self,queue_id:str,updates:Dict)->bool:
        mapping={'proximo_intento':'ProximoIntentoUTC','estado':'Estado','locked_at':'LockedAtUTC','locked_by':'LockedBy','intentos':'Intentos','payload_renderizado':'PayloadRenderizado','error':'ErrorMensaje'}; parts=[]; params=[]
        for key,col in mapping.items():
            if key in updates: parts.append(f"{col}=%s"); params.append(_value(updates[key]))
        if not parts: return False
        parts.append('UpdatedAtUTC=SYSUTCDATETIME()'); params.append(queue_id); conn=self._conn()
        try:
            cur=conn.cursor(); cur.execute(f"UPDATE {QUEUE_TABLE} SET {','.join(parts)} WHERE ID=%s",tuple(params)); ok=cur.rowcount==1; conn.commit(); return ok
        except Exception:
            conn.rollback(); raise
        finally: conn.close()

    async def mark_sent(self,queue_id:str)->bool: return await self.update_queue_item(queue_id,{'estado':'enviado','locked_at':None,'locked_by':None})
    async def mark_failed(self,queue_id:str,error:str)->bool: return await self.update_queue_item(queue_id,{'estado':'fallido','error':str(error)[:1000],'locked_at':None,'locked_by':None})
    async def get_queue_stats(self)->Dict:
        rows=self._rows(f"SELECT Estado,COUNT_BIG(*) total,SUM(CASE WHEN LockedAtUTC IS NOT NULL THEN 1 ELSE 0 END) locked FROM {QUEUE_TABLE} GROUP BY Estado"); result={str(r.get('Estado') or 'sin_estado'):int(r.get('total') or 0) for r in rows}; result['locked']=sum(int(r.get('locked') or 0) for r in rows); return result

    async def create_log(self,log)->Dict:
        doc=self._doc(log); log_id=str(doc.get('id') or uuid.uuid4()); metadata=_json(doc); conn=self._conn()
        try:
            cur=conn.cursor(); cur.execute('SET XACT_ABORT ON'); cur.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE'); cur.execute('BEGIN TRANSACTION'); cur.execute(f"SELECT ISNULL(MAX(ID),0)+1 FROM {LOG_TABLE} WITH (UPDLOCK,HOLDLOCK)"); next_id=int(cur.fetchone()[0]); cur.execute(f"INSERT INTO {LOG_TABLE} (ID,NotificacionID,TipoEvento,WorkflowID,TareaID,Destinatario,DestinatarioEmail,Titulo,Mensaje,Estado,Canal,FechaEnvio,ErrorMensaje,MetadatosJSON) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,GETUTCDATE(),%s,%s)",(next_id,log_id,str(_value(doc.get('evento_negocio') or doc.get('evento') or 'NOTIFICACION'))[:50],doc.get('workflow_id'),doc.get('tarea_id'),doc.get('destinatario'),doc.get('destinatario_email'),doc.get('titulo'),doc.get('payload_renderizado') or doc.get('mensaje'),str(_value(doc.get('estado_envio') or doc.get('estado') or 'enviado'))[:50],str(_value(doc.get('canal') or 'email'))[:50],doc.get('error_detalle') or doc.get('error_mensaje'),metadata)); conn.commit()
        except Exception:
            conn.rollback(); raise
        finally: conn.close()
        doc['id']=log_id; return doc

    async def get_logs(self,workflow_id:Optional[str]=None,referencia_id:Optional[str]=None,evento_negocio:Optional[str]=None,destinatario:Optional[str]=None,estado_envio:Optional[str]=None,fecha_desde:Optional[str]=None,fecha_hasta:Optional[str]=None,limit:int=100,skip:int=0,**kwargs)->List[Dict]:
        where=[]; params=[]
        for column,value in [('WorkflowID',workflow_id),('TipoEvento',evento_negocio),('Estado',estado_envio)]:
            if value is not None: where.append(f'{column}=%s'); params.append(value)
        if destinatario: where.append('(Destinatario LIKE %s OR DestinatarioEmail LIKE %s)'); params += [f'%{destinatario}%',f'%{destinatario}%']
        if fecha_desde: where.append('FechaEnvio>=%s'); params.append(fecha_desde)
        if fecha_hasta: where.append('FechaEnvio<=%s'); params.append(fecha_hasta)
        safe=max(1,min(int(limit)+int(skip),500)); clause=(' WHERE '+' AND '.join(where)) if where else ''; rows=self._rows(f"SELECT TOP ({safe}) NotificacionID id,TipoEvento evento_negocio,WorkflowID workflow_id,TareaID tarea_id,Destinatario destinatario,DestinatarioEmail destinatario_email,Titulo titulo,Mensaje payload_renderizado,Estado estado_envio,Canal canal,FechaEnvio fecha_envio,ErrorMensaje error_detalle,MetadatosJSON metadatos_json FROM {LOG_TABLE}{clause} ORDER BY FechaEnvio DESC",tuple(params)); return rows[int(skip):]
    async def count_logs(self,filtro:Dict=None)->int:
        row=self._rows(f"SELECT COUNT_BIG(*) total FROM {LOG_TABLE}"); return int((row[0] if row else {}).get('total') or 0)
    async def get_log_stats(self,modulo:Optional[str]=None)->Dict:
        rows=self._rows(f"SELECT Canal,Estado,COUNT_BIG(*) total FROM {LOG_TABLE} GROUP BY Canal,Estado"); stats={}
        for r in rows:
            canal=r.get('Canal') or 'SIN_CANAL'; stats.setdefault(canal,{'total':0,'por_estado':{}}); stats[canal]['total']+=int(r.get('total') or 0); stats[canal]['por_estado'][r.get('Estado') or 'SIN_ESTADO']=int(r.get('total') or 0)
        return stats
    async def check_duplicate(self,destinatario:str,evento:str,dedup_key:str,ventana_minutos:int=60)->bool:
        rows=self._rows(f"SELECT TOP 1 NotificacionID FROM {LOG_TABLE} WHERE TipoEvento=%s AND (Destinatario=%s OR DestinatarioEmail=%s) AND FechaEnvio>=DATEADD(minute,-%s,GETUTCDATE()) ORDER BY FechaEnvio DESC",(str(_value(evento)),destinatario,destinatario,int(ventana_minutos))); return bool(rows)


def get_notification_repository(db=None)->NotificationRepository:
    return NotificationRepository(db)
