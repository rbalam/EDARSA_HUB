"""Servicios de dominio para Economía."""

import json
import uuid
import httpx

from .response_decoder import decode_http_response
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from .repository import EconomiaRepository
from core.sql_first.db import sql_connection


class EconomiaService:
    @staticmethod
    async def resolver_conexion_proveedor(
        serie_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Resuelve proveedor y secreto mediante fuentes canónicas.

        No importa modules.api_connections y evita ejecutar su
        package __init__ con efectos laterales legacy.
        """
        proveedor = (
            EconomiaRepository.resolver_proveedor_serie(
                serie_id
            )
        )

        if not proveedor:
            return None

        api_key = ""
        encrypted = proveedor.get("api_key_encrypted")

        if encrypted:
            from core.secret_manager import (
                decrypt_secret,
                is_encrypted_secret,
            )

            api_key = (
                decrypt_secret(encrypted)
                if is_encrypted_secret(encrypted)
                else encrypted
            )

        conexion = None

        if proveedor.get("conexion_id"):
            conexion = {
                "id": proveedor.get("conexion_id"),
                "api_url": proveedor.get("conexion_url"),
                "url": proveedor.get("conexion_url"),
                "tipo_conexion": proveedor.get(
                    "tipo_conexion"
                ),
                "system_type": proveedor.get(
                    "system_type"
                ),
                "activo": bool(
                    proveedor.get("conexion_activa")
                ),
            }

        return {
            "proveedor": proveedor,
            "conexion": conexion,
            "api_key": api_key,
        }

    @staticmethod
    async def resolver_contrato_http_proveedor(
        serie_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Construye el contrato HTTP configurable de una serie.

        No ejecuta HTTP.
        No contiene lógica específica por proveedor.
        """
        resolved = await (
            EconomiaService.resolver_conexion_proveedor(
                serie_id
            )
        )

        if not resolved:
            return None

        proveedor = resolved["proveedor"]
        conexion = resolved.get("conexion")
        api_key = resolved.get("api_key", "")

        metadata_raw = proveedor.get("metadata_json")

        if metadata_raw in (None, ""):
            metadata = {}
        elif isinstance(metadata_raw, dict):
            metadata = metadata_raw
        else:
            try:
                metadata = json.loads(metadata_raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "MetadataJSON de serie económica inválido"
                ) from exc

        base_url = metadata.get("base_url") or ""

        if base_url and not isinstance(base_url, str):
            raise ValueError(
                "base_url de serie económica inválida"
            )

        base_url = str(base_url).strip()

        if conexion and not base_url:
            base_url = (
                conexion.get("api_url")
                or conexion.get("url")
                or ""
            )

        if not base_url:
            base_url = proveedor.get("url_publica") or ""

        return {
            "serie_id": proveedor.get("serie_id"),
            "codigo_canonico": proveedor.get(
                "codigo_canonico"
            ),
            "codigo_proveedor": proveedor.get(
                "codigo_proveedor"
            ),
            "proveedor_codigo": proveedor.get(
                "proveedor_codigo"
            ),
            "proveedor_tipo": proveedor.get(
                "proveedor_tipo"
            ),
            "base_url": base_url,
            "requiere_autenticacion": bool(
                proveedor.get(
                    "requiere_autenticacion"
                )
            ),
            "permite_backfill": bool(
                proveedor.get(
                    "permite_backfill"
                )
            ),
            "api_key": api_key,
            "metadata": metadata,
        }

    @staticmethod
    async def consultar_proveedor_http(
        serie_id: int,
        *,
        params_extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Ejecuta GET contra proveedor económico configurado.

        URL, endpoint, parámetros, headers y autenticación
        provienen del contrato canónico/MetadataJSON.
        """
        contrato = await (
            EconomiaService.resolver_contrato_http_proveedor(
                serie_id
            )
        )

        if not contrato:
            raise ValueError(
                "Serie económica o proveedor no encontrado"
            )

        base_url = (contrato.get("base_url") or "").rstrip("/")
        metadata = contrato.get("metadata") or {}
        endpoint = metadata.get("endpoint")

        if not base_url:
            raise ValueError(
                "Proveedor económico sin URL configurada"
            )

        if not endpoint:
            raise ValueError(
                "Serie económica sin endpoint configurado"
            )

        codigo = contrato.get("codigo_proveedor") or ""

        params = dict(metadata.get("params") or {})

        if params_extra:
            params.update(params_extra)

        headers = dict(metadata.get("headers") or {})

        auth = metadata.get("auth") or {}
        api_key = contrato.get("api_key") or ""

        if "requires_auth" in metadata:
            requires_auth_override = metadata.get(
                "requires_auth"
            )

            if not isinstance(
                requires_auth_override,
                bool,
            ):
                raise ValueError(
                    "requires_auth debe ser booleano"
                )

            requiere_auth = requires_auth_override
        else:
            requiere_auth = bool(
                contrato.get("requiere_autenticacion")
            )

        placement = auth.get("placement", "header")
        prefix = auth.get("prefix") or ""

        if requiere_auth and not api_key:
            raise ValueError(
                "Proveedor requiere autenticación "
                "sin credencial configurada"
            )

        format_values = {
            "codigo": codigo,
        }

        if requiere_auth:
            if placement == "header":
                header_name = auth.get("name") or auth.get(
                    "header"
                )

                if not header_name:
                    raise ValueError(
                        "Autenticación header incompleta"
                    )

                headers[header_name] = (
                    f"{prefix}{api_key}"
                )

            elif placement == "query":
                param_name = auth.get("name")

                if not param_name:
                    raise ValueError(
                        "Autenticación query incompleta"
                    )

                params[param_name] = (
                    f"{prefix}{api_key}"
                )

            elif placement == "path":
                placeholder = auth.get(
                    "placeholder",
                    "api_key",
                )

                if not isinstance(placeholder, str) or not placeholder:
                    raise ValueError(
                        "Autenticación path incompleta"
                    )

                format_values[placeholder] = (
                    f"{prefix}{api_key}"
                )

            else:
                raise ValueError(
                    "Tipo de autenticación no soportado"
                )

        try:
            endpoint = endpoint.format(
                **format_values
            )
        except (KeyError, ValueError) as exc:
            raise ValueError(
                "Endpoint económico inválido"
            ) from exc

        url = (
            base_url
            + "/"
            + endpoint.lstrip("/")
        )

        timeout = metadata.get(
            "timeout_seconds",
            30,
        )

        if not isinstance(timeout, (int, float)):
            raise ValueError(
                "timeout_seconds inválido"
            )

        if timeout <= 0 or timeout > 120:
            raise ValueError(
                "timeout_seconds fuera de rango"
            )

        async with httpx.AsyncClient(
            timeout=float(timeout)
        ) as client:
            response = await client.get(
                url,
                params=params,
                headers=headers,
            )

            response.raise_for_status()

            response_format = metadata.get(
                "response_format",
                "json",
            )

            data = decode_http_response(
                response,
                response_format,
            )

            return {
                "serie_id": serie_id,
                "status_code": response.status_code,
                "data": data,
            }

    @staticmethod
    def normalizar_observaciones(
        serie_id: int,
        data: Any,
        metadata: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Convierte payload externo a observaciones económicas canónicas.

        El mapping proviene exclusivamente de MetadataJSON.
        """
        config = metadata.get("normalizacion") or {}

        items_path = config.get("items_path")
        fecha_field = config.get("fecha_field")
        valor_field = config.get("valor_field")

        if not fecha_field or not valor_field:
            raise ValueError(
                "Configuración de normalización incompleta"
            )

        def resolve_path(value, path):
            if not path:
                return value

            current = value

            for part in path.split("."):
                if isinstance(current, dict):
                    if part not in current:
                        raise ValueError(
                            f"Campo requerido no encontrado: {part}"
                        )

                    current = current[part]
                    continue

                if isinstance(current, list):
                    try:
                        index = int(part)
                    except (TypeError, ValueError) as exc:
                        raise ValueError(
                            "Índice de lista inválido en normalización"
                        ) from exc

                    if index < 0 or index >= len(current):
                        raise ValueError(
                            "Índice fuera de rango en normalización"
                        )

                    current = current[index]
                    continue

                raise ValueError(
                    "Ruta de normalización inválida"
                )

            return current

        items = resolve_path(data, items_path)

        if not isinstance(items, list):
            raise ValueError(
                "La colección de observaciones no es una lista"
            )

        result = []

        for item in items:
            if not isinstance(item, dict):
                raise ValueError(
                    "Observación económica inválida"
                )

            fecha_raw = resolve_path(
                item,
                fecha_field,
            )
            valor_raw = resolve_path(
                item,
                valor_field,
            )

            fecha_format = config.get("fecha_format")

            try:
                if fecha_format:
                    from datetime import datetime

                    fecha_periodo = datetime.strptime(
                        str(fecha_raw),
                        fecha_format,
                    ).date()
                else:
                    fecha_periodo = date.fromisoformat(
                        str(fecha_raw)
                    )
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "Fecha económica inválida"
                ) from exc

            try:
                valor = Decimal(str(valor_raw))
            except (InvalidOperation, TypeError, ValueError) as exc:
                raise ValueError(
                    "Valor económico inválido"
                ) from exc

            observacion = {
                "serie_id": serie_id,
                "fecha_periodo": fecha_periodo,
                "valor": valor,
                "periodo_codigo": None,
                "fuente_dato_id": None,
                "preliminar": False,
                "estimado": False,
            }

            optional = (
                ("periodo_field", "periodo_codigo"),
                ("fuente_id_field", "fuente_dato_id"),
                ("preliminar_field", "preliminar"),
                ("estimado_field", "estimado"),
            )

            for config_key, output_key in optional:
                field = config.get(config_key)

                if field:
                    observacion[output_key] = resolve_path(
                        item,
                        field,
                    )

            observacion["preliminar"] = bool(
                observacion["preliminar"]
            )
            observacion["estimado"] = bool(
                observacion["estimado"]
            )

            result.append(observacion)

        return result

    @staticmethod
    async def consultar_observaciones_proveedor(
        serie_id: int,
    ) -> List[Dict[str, Any]]:
        contrato = await (
            EconomiaService.resolver_contrato_http_proveedor(
                serie_id
            )
        )

        if not contrato:
            raise ValueError(
                "Serie económica o proveedor no encontrado"
            )

        response = await (
            EconomiaService.consultar_proveedor_http(
                serie_id
            )
        )

        return EconomiaService.normalizar_observaciones(
            serie_id=serie_id,
            data=response["data"],
            metadata=contrato.get("metadata") or {},
        )

    @staticmethod
    async def sincronizar_serie(
        serie_id: int,
        *,
        sync_run_id=None,
    ) -> Dict[str, Any]:
        """
        Ejecuta el flujo canónico:
        proveedor HTTP -> normalización -> persistencia versionada.
        """

        if sync_run_id is None:
            sync_run_id = str(uuid.uuid4())

        observaciones = await (
            EconomiaService.consultar_observaciones_proveedor(
                serie_id
            )
        )

        insertados = 0
        sin_cambio = 0
        revisiones = 0

        resultados = []

        if not observaciones:
            return {
                "serie_id": serie_id,
                "observaciones": 0,
                "insertados": 0,
                "sin_cambio": 0,
                "revisiones": 0,
                "resultados": [],
            }

        with sql_connection() as conn:
            try:
                for obs in observaciones:
                    result = (
                        EconomiaRepository.persistir_valor_versionado(
                            serie_id=obs["serie_id"],
                            fecha_periodo=obs["fecha_periodo"],
                            valor=obs["valor"],
                            periodo_codigo=obs.get(
                                "periodo_codigo"
                            ),
                            preliminar=bool(
                                obs.get("preliminar")
                            ),
                            estimado=bool(
                                obs.get("estimado")
                            ),
                            fuente_dato_id=obs.get(
                                "fuente_dato_id"
                            ),
                            sync_run_id=sync_run_id,
                            connection=conn,
                        )
                    )

                    resultados.append(result)

                    if result["insertado"]:
                        insertados += 1

                        if result["es_revision"]:
                            revisiones += 1
                    else:
                        sin_cambio += 1

                conn.commit()
            except Exception:
                conn.rollback()
                raise

        return {
            "serie_id": serie_id,
            "observaciones": len(observaciones),
            "insertados": insertados,
            "sin_cambio": sin_cambio,
            "revisiones": revisiones,
            "resultados": resultados,
        }

    @staticmethod
    async def backfill_serie(
        serie_id: int,
        desde: date,
        hasta: date,
        *,
        sync_run_id=None,
    ) -> Dict[str, Any]:
        """
        Ejecuta backfill económico configurable por MetadataJSON.

        No contiene nombres de parámetros específicos de proveedor.
        """

        if sync_run_id is None:
            sync_run_id = str(uuid.uuid4())

        if hasta < desde:
            raise ValueError(
                "Rango de backfill inválido"
            )

        contrato = await (
            EconomiaService.resolver_contrato_http_proveedor(
                serie_id
            )
        )

        if not contrato:
            raise ValueError(
                "Serie económica o proveedor no encontrado"
            )

        if not contrato.get("permite_backfill"):
            raise ValueError(
                "Proveedor económico no permite backfill"
            )

        metadata = contrato.get("metadata") or {}
        config = metadata.get("backfill") or {}

        desde_param = config.get("desde_param")
        hasta_param = config.get("hasta_param")
        formato = config.get("date_format")

        if not desde_param or not hasta_param or not formato:
            raise ValueError(
                "Configuración de backfill incompleta"
            )

        max_days = config.get("max_days")

        if not isinstance(max_days, int) or max_days <= 0:
            raise ValueError(
                "max_days de backfill inválido"
            )

        rango_days = (hasta - desde).days + 1

        if rango_days > max_days:
            raise ValueError(
                "Rango de backfill excede máximo configurado"
            )

        params_extra = {
            desde_param: desde.strftime(formato),
            hasta_param: hasta.strftime(formato),
        }

        response = await (
            EconomiaService.consultar_proveedor_http(
                serie_id,
                params_extra=params_extra,
            )
        )

        observaciones = (
            EconomiaService.normalizar_observaciones(
                serie_id=serie_id,
                data=response["data"],
                metadata=metadata,
            )
        )

        insertados = 0
        sin_cambio = 0
        revisiones = 0

        with sql_connection() as conn:
            try:
                for obs in observaciones:
                    result = (
                        EconomiaRepository.persistir_valor_versionado(
                            serie_id=obs["serie_id"],
                            fecha_periodo=obs["fecha_periodo"],
                            valor=obs["valor"],
                            periodo_codigo=obs.get(
                                "periodo_codigo"
                            ),
                            preliminar=bool(
                                obs.get("preliminar")
                            ),
                            estimado=bool(
                                obs.get("estimado")
                            ),
                            fuente_dato_id=obs.get(
                                "fuente_dato_id"
                            ),
                            sync_run_id=sync_run_id,
                            connection=conn,
                        )
                    )

                    if result["insertado"]:
                        insertados += 1

                        if result["es_revision"]:
                            revisiones += 1
                    else:
                        sin_cambio += 1

                conn.commit()
            except Exception:
                conn.rollback()
                raise

        return {
            "serie_id": serie_id,
            "desde": desde,
            "hasta": hasta,
            "observaciones": len(observaciones),
            "insertados": insertados,
            "sin_cambio": sin_cambio,
            "revisiones": revisiones,
        }

    @staticmethod
    def listar_series(
        activo: Optional[bool] = True,
        limite: int = 500,
    ) -> List[Dict[str, Any]]:
        return EconomiaRepository.listar_series(
            activo=activo,
            limite=limite,
        )

    @staticmethod
    def obtener_serie(
        serie_id: str,
    ) -> Optional[Dict[str, Any]]:
        return EconomiaRepository.obtener_serie(serie_id)

    @staticmethod
    def listar_valores(
        serie_id: str,
        desde=None,
        hasta=None,
        limite: int = 500,
    ) -> List[Dict[str, Any]]:
        return EconomiaRepository.listar_valores(
            serie_id=serie_id,
            desde=desde,
            hasta=hasta,
            limite=limite,
        )

    @staticmethod
    def listar_contextos_activos() -> List[Dict[str, Any]]:
        return EconomiaRepository.listar_contextos_activos()
