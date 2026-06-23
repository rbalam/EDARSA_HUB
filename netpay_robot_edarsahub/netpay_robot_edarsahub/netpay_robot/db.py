from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterable
try:
    import pymssql
except ModuleNotFoundError:  # permite validar layouts sin instalar driver SQL
    pymssql = None

from .settings import Settings


@contextmanager
def sql_connection(settings: Settings):
    if not settings.edarsahub_sql_host:
        raise RuntimeError('EDARSAHUB_SQL_HOST no configurado')
    if pymssql is None:
        raise RuntimeError('pymssql no está instalado. Instala requirements.txt en el backend EDARSAHUB.')
    conn = pymssql.connect(
        server=settings.edarsahub_sql_host,
        user=settings.edarsahub_sql_user,
        password=settings.edarsahub_sql_password,
        database=settings.edarsahub_sql_database,
        port=settings.edarsahub_sql_port,
        as_dict=True,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class EdarsaHubRepository:
    def __init__(self, settings: Settings):
        self.settings = settings

    def create_execution(self, *, report_type: str, date_from: str, date_to: str, source: str = 'PORTAL_ROBOT') -> int | None:
        # Stub seguro. Integrar con core.db.execute_sql_query si el proyecto ya tiene repositorio centralizado.
        # No abre conexiones si SQL no está configurado.
        if not self.settings.edarsahub_sql_host:
            return None
        with sql_connection(self.settings) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Finanzas_NetPayRobotEjecuciones
                (RobotConfigID, ConectorID, UnidadNegocioID, TipoReporte, FechaDesde, FechaHasta, Estatus, FechaInicio)
                VALUES (NULL, NULL, NULL, %s, %s, %s, 'INICIADO', SYSDATETIME());
                SELECT SCOPE_IDENTITY() AS id;
                """,
                (report_type, date_from, date_to),
            )
            row = cur.fetchone()
            return int(row['id']) if row and row.get('id') is not None else None

    def log_event(self, execution_id: int | None, level: str, code: str, message: str, detail: str | None = None) -> None:
        if not execution_id or not self.settings.edarsahub_sql_host:
            print(f'[{level}] {code}: {message}')
            return
        with sql_connection(self.settings) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Finanzas_NetPayRobotEventosLog
                (EjecucionID, FechaEvento, Nivel, CodigoEvento, Mensaje, DetalleTecnicoSeguro)
                VALUES (%s, SYSDATETIME(), %s, %s, %s, %s)
                """,
                (execution_id, level, code, message, detail),
            )

    def register_file(self, execution_id: int | None, path: str, sha256: str, report_type: str) -> None:
        if not execution_id or not self.settings.edarsahub_sql_host:
            print(f'[FILE] {report_type}: {path} sha256={sha256}')
            return
        with sql_connection(self.settings) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO Finanzas_NetPayRobotArchivos
                (EjecucionID, UnidadNegocioID, TipoReporte, NombreArchivoOriginal, RutaArchivoSeguro,
                 Extension, HashArchivo, FechaDescarga)
                VALUES (%s, NULL, %s, %s, %s, %s, CONVERT(varbinary(32), %s, 2), SYSDATETIME())
                """,
                (execution_id, report_type, path.split('/')[-1], path, path.split('.')[-1], sha256),
            )


    def mark_file_validated(
        self,
        execution_id: int | None,
        sha256: str,
        *,
        status: str = 'VALIDADO',
        layout: str | None = None,
    ) -> None:
        if not execution_id or not self.settings.edarsahub_sql_host:
            return
        with sql_connection(self.settings) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE Finanzas_NetPayRobotArchivos
                SET EstatusValidacion=%s,
                    LayoutDetectado=COALESCE(%s, LayoutDetectado)
                WHERE EjecucionID=%s
                  AND HashArchivo=CONVERT(varbinary(32), %s, 2)
                """,
                (status, layout, execution_id, sha256),
            )

    def finish_execution(
        self,
        execution_id: int | None,
        *,
        status: str,
        records: int | None = None,
        total_monto_trx=None,
        total_monto_deposito=None,
        error_code: str | None = None,
        error_message: str | None = None,
        file_path: str | None = None,
        sha256: str | None = None,
    ) -> None:
        if not execution_id or not self.settings.edarsahub_sql_host:
            return

        clean_error = error_message[:3900] if error_message else None
        with sql_connection(self.settings) as conn:
            cur = conn.cursor()
            if sha256:
                cur.execute(
                    """
                    UPDATE Finanzas_NetPayRobotEjecuciones
                    SET FechaFin=SYSDATETIME(),
                        Estatus=%s,
                        RegistrosDescargados=COALESCE(%s, RegistrosDescargados),
                        TotalMontoTrx=COALESCE(%s, TotalMontoTrx),
                        TotalMontoDeposito=COALESCE(%s, TotalMontoDeposito),
                        ErrorCodigo=%s,
                        ErrorMensaje=%s,
                        RutaArchivoOriginal=COALESCE(%s, RutaArchivoOriginal),
                        HashArchivo=CONVERT(varbinary(32), %s, 2)
                    WHERE EjecucionID=%s
                    """,
                    (
                        status,
                        records,
                        total_monto_trx,
                        total_monto_deposito,
                        error_code,
                        clean_error,
                        file_path,
                        sha256,
                        execution_id,
                    ),
                )
            else:
                cur.execute(
                    """
                    UPDATE Finanzas_NetPayRobotEjecuciones
                    SET FechaFin=SYSDATETIME(),
                        Estatus=%s,
                        RegistrosDescargados=COALESCE(%s, RegistrosDescargados),
                        TotalMontoTrx=COALESCE(%s, TotalMontoTrx),
                        TotalMontoDeposito=COALESCE(%s, TotalMontoDeposito),
                        ErrorCodigo=%s,
                        ErrorMensaje=%s,
                        RutaArchivoOriginal=COALESCE(%s, RutaArchivoOriginal)
                    WHERE EjecucionID=%s
                    """,
                    (
                        status,
                        records,
                        total_monto_trx,
                        total_monto_deposito,
                        error_code,
                        clean_error,
                        file_path,
                        execution_id,
                    ),
                )


    def _scalar(self, cur, sql: str, params: tuple = ()) -> int | None:
        cur.execute(sql, params)
        row = cur.fetchone()
        if not row:
            return None
        val = next(iter(row.values()))
        return int(val) if val is not None else None

    def _hash_hex(self, value) -> str | None:
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.hex()
        s = str(value).strip()
        if not s:
            return None
        return s

    def _d(self, row: dict, *names, default=0):
        from decimal import Decimal, InvalidOperation
        for name in names:
            v = row.get(name)
            if v is None or v == '':
                continue
            if isinstance(v, Decimal):
                return v
            if isinstance(v, (int, float)):
                return Decimal(str(v)).quantize(Decimal('0.01'))
            s = str(v).strip().replace('$', '').replace(',', '').replace('%', '')
            if s in ('', '-'):
                return Decimal(str(default)).quantize(Decimal('0.01'))
            try:
                return Decimal(s).quantize(Decimal('0.01'))
            except InvalidOperation:
                continue
        return Decimal(str(default)).quantize(Decimal('0.01'))

    def _s(self, row: dict, *names):
        for name in names:
            v = row.get(name)
            if v is not None and str(v).strip() != '':
                return str(v).strip()
        return None

    def _date(self, row: dict, *names):
        from datetime import datetime, date
        for name in names:
            v = row.get(name)
            if not v:
                continue
            if isinstance(v, date) and not isinstance(v, datetime):
                return v
            if isinstance(v, datetime):
                return v.date()
            s = str(v).strip()
            for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(s, fmt).date()
                except ValueError:
                    pass
        return None

    def _time(self, row: dict, *names):
        from datetime import datetime, time
        for name in names:
            v = row.get(name)
            if not v:
                continue
            if isinstance(v, time):
                return v
            if isinstance(v, datetime):
                return v.time()
            s = str(v).strip()
            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    return datetime.strptime(s, fmt).time()
                except ValueError:
                    pass
        return None

    def persist_parsed_rows(
        self,
        *,
        execution_id: int | None,
        report_type: str,
        file_path: str,
        sha256: str,
        date_from: str,
        date_to: str,
        parsed_rows,
    ) -> None:
        """
        Persiste Excel NetPay en EDARSAHUB SQL.
        Excel = evidencia.
        SQL = fuente única de verdad.
        No crea tablas. Usa schema existente Finanzas_Adquirente*.
        """
        import json
        from decimal import Decimal
        from datetime import date, datetime, time

        if not self.settings.edarsahub_sql_host:
            print("[SQL_SKIP] EDARSAHUB_SQL_HOST no configurado; solo se validó Excel.")
            return

        def json_default(o):
            if isinstance(o, Decimal):
                return str(o)
            if isinstance(o, (date, datetime, time)):
                return o.isoformat()
            if isinstance(o, bytes):
                return o.hex()
            return str(o)

        total_rows = sum(len(sheet.rows) for sheet in parsed_rows)
        total_amount = Decimal("0.00")
        for sheet in parsed_rows:
            if sheet.totals:
                total_amount += sheet.totals.get("approved_monto_trx", Decimal("0.00"))
                total_amount += sheet.totals.get("monto_deposito", Decimal("0.00"))

        with sql_connection(self.settings) as conn:
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO Finanzas_AdquirenteImportaciones
                (UnidadNegocioID, AdquirenteID, FuenteIngesta, TipoReporte,
                 NombreArchivoOriginal, RutaArchivoSeguro, HashArchivo,
                 FechaReporteDesde, FechaReporteHasta, TotalRegistros, TotalImportado,
                 Estatus, Observaciones, CreadoPorUsuarioID, FechaCreacion)
                VALUES
                (NULL, NULL, %s, %s,
                 %s, %s, CONVERT(varbinary(32), %s, 2),
                 %s, %s, %s, %s,
                 'CARGADO', %s, NULL, SYSDATETIME());
                SELECT SCOPE_IDENTITY() AS id;
                """,
                (
                    "PORTAL_ROBOT",
                    report_type,
                    file_path.split("/")[-1],
                    file_path,
                    sha256,
                    date_from,
                    date_to,
                    int(total_rows),
                    total_amount,
                    f"EjecucionID={execution_id}",
                ),
            )
            row = cur.fetchone()
            importacion_id = int(row["id"])

            inserted_stage = 0
            inserted_final = 0
            skipped_dup = 0

            for sheet in parsed_rows:
                for idx, r in enumerate(sheet.rows, start=1):
                    hash_hex = self._hash_hex(r.get("HashRegistro"))
                    registro_json = json.dumps(r, ensure_ascii=False, default=json_default)

                    cur.execute(
                        """
                        INSERT INTO Finanzas_AdquirenteImportacionDetalle
                        (ImportacionID, NumeroFila, Hoja, RegistroJson, HashRegistro, Estatus, ErrorValidacion, FechaCreacion)
                        VALUES (%s, %s, %s, %s, CONVERT(varbinary(32), %s, 2), 'STAGING', NULL, SYSDATETIME())
                        """,
                        (importacion_id, idx, sheet.sheet_name, registro_json, hash_hex),
                    )
                    inserted_stage += 1

                    if report_type == "DETALLE_TRANSACCIONES":
                        # PATCH_CONTADOR_DUPLICADOS_NETPAY: contar duplicados e insertados sin depender de rowcount en batch IF/BEGIN
                        cur.execute(
                            """
                            SELECT COUNT(*) AS existe
                            FROM Finanzas_AdquirenteTransacciones
                            WHERE HashRegistro = CONVERT(varbinary(32), %s, 2)
                            """,
                            (hash_hex,),
                        )
                        existe_row = cur.fetchone()
                        if existe_row and int(existe_row.get("existe", 0) or 0) > 0:
                            skipped_dup += 1
                            continue

                        cur.execute(
                            """
                            INSERT INTO Finanzas_AdquirenteTransacciones
                                (ImportacionID, UnidadNegocioID, AdquirenteID, FuenteIngesta,
                                 FechaTrx, HoraTrx, FechaOperativa,
                                 MontoTrx, VentaNeta, Propina, RetiroEfectivo,
                                 EstatusTrx, CodigoRespuesta, Motivo,
                                 NombreEmpresa, Sucursal, AliasProducto, StoreID, Producto,
                                 Banco, Marca, TipoVenta, TipoTarjeta,
                                 OrderID, CodigoAutorizacion, Referencia, Comentario, Cajero,
                                 HashRegistro, Estatus, FechaCreacion)
                                VALUES
                                (%s, NULL, NULL, 'PORTAL_ROBOT',
                                 %s, %s, %s,
                                 %s, %s, %s, %s,
                                 %s, %s, %s,
                                 %s, %s, %s, %s, %s,
                                 %s, %s, %s, %s,
                                 %s, %s, %s, %s, %s,
                                 CONVERT(varbinary(32), %s, 2), 'PENDIENTE_CONCILIAR', SYSDATETIME())
                            """,
                            (
                                importacion_id,
                                self._date(r, "Fecha de TRX", "Fecha Trx", "Fecha de Trx"),
                                self._time(r, "Hora de TRX", "Hora de Trx", "Hora Trx"),
                                self._date(r, "Fecha de TRX", "Fecha Trx", "Fecha de Trx"),
                                self._d(r, "Monto de trx", "Monto de Trx", "Monto Trx"),
                                self._d(r, "Venta Neta"),
                                self._d(r, "Propina"),
                                self._d(r, "Retiro Efectivo"),
                                self._s(r, "Estatus de trx", "Estatus Trx"),
                                self._s(r, "Código de respuesta", "CodigoRespuesta"),
                                self._s(r, "Motivo"),
                                self._s(r, "Nombre Empresa", "Comercio"),
                                self._s(r, "Sucursal"),
                                self._s(r, "Alias Producto"),
                                self._s(r, "Store ID", "StoreID"),
                                self._s(r, "Producto"),
                                self._s(r, "Banco"),
                                self._s(r, "Marca"),
                                self._s(r, "Tipo de Venta"),
                                self._s(r, "Tipo de Tarjeta"),
                                self._s(r, "Order ID", "OrderID"),
                                self._s(r, "Código de Autorización", "CodigoAutorizacion"),
                                self._s(r, "Referencia"),
                                self._s(r, "Comentario"),
                                self._s(r, "Cajero"),
                                hash_hex,
                            ),
                        )
                        inserted_final += 1

                    elif report_type == "DETALLE_DEPOSITOS_MOVIMIENTOS" and sheet.sheet_name != "Resumen":
                        # Evita insertar filas completamente vacías del Excel NetPay.
                        # Staging conserva la evidencia, pero la tabla canónica solo recibe registros operativos.
                        fecha_deposito = self._date(r, "Fecha de depósito", "Fecha Deposito", "FechaDeposito")
                        fecha_trx = self._date(r, "Fecha Trx", "Fecha de Trx")
                        clave_rastreo = self._s(r, "Clave Rastreo")
                        order_id = self._s(r, "Order ID", "OrderID")
                        monto_deposito = self._d(r, "Monto Depósito", "Monto Deposito")
                        monto_trx = self._d(r, "Monto de Trx", "Monto Trx")
                        propina = self._d(r, "Propina")

                        if (
                            fecha_deposito is None
                            and fecha_trx is None
                            and not clave_rastreo
                            and not order_id
                            and monto_deposito == Decimal("0.00")
                            and monto_trx == Decimal("0.00")
                            and propina == Decimal("0.00")
                        ):
                            continue

                        cur.execute(
                            """
                            IF NOT EXISTS (
                                SELECT 1 FROM Finanzas_AdquirenteDepositos
                                WHERE HashRegistro = CONVERT(varbinary(32), %s, 2)
                            )
                            BEGIN
                                INSERT INTO Finanzas_AdquirenteDepositos
                                (ImportacionID, UnidadNegocioID, AdquirenteID, FuenteIngesta,
                                 FechaDeposito, FechaTrx, HoraTrx, ClaveRastreo, CuentaDeposito,
                                 NombreEmpresa, Sucursal, StoreID, Producto,
                                 MontoTrx, VentaNeta, Propina, MontoDeposito,
                                 ComisionBasePorcentaje, ComisionBaseImporte,
                                 SobreTasaPorcentaje, SobreTasaImporte,
                                 ComisionTotal, IVAComisiones, ComisionesMasIVA,
                                 Banco, Marca, TipoVenta, TipoTarjeta,
                                 CodigoAutorizacion, OrderID, ReferenciaDepositoStoreID, Referencia,
                                 HashRegistro, Estatus, FechaCreacion)
                                VALUES
                                (%s, NULL, NULL, 'PORTAL_ROBOT',
                                 %s, %s, %s, %s, %s,
                                 %s, %s, %s, %s,
                                 %s, %s, %s, %s,
                                 %s, %s,
                                 %s, %s,
                                 %s, %s, %s,
                                 %s, %s, %s, %s,
                                 %s, %s, %s, %s,
                                 CONVERT(varbinary(32), %s, 2), 'PENDIENTE_BANCO', SYSDATETIME())
                            END
                            """,
                            (
                                hash_hex,
                                importacion_id,
                                self._date(r, "Fecha de depósito", "Fecha Deposito", "FechaDeposito"),
                                self._date(r, "Fecha Trx", "Fecha de Trx"),
                                self._time(r, "Hora de Trx", "Hora Trx"),
                                self._s(r, "Clave Rastreo"),
                                self._s(r, "Cuenta Depósito", "Cuenta Deposito"),
                                self._s(r, "Nombre Empresa"),
                                self._s(r, "Sucursal"),
                                self._s(r, "Store ID", "StoreID"),
                                self._s(r, "Producto"),
                                self._d(r, "Monto de Trx", "Monto Trx"),
                                self._d(r, "Venta Neta"),
                                self._d(r, "Propina"),
                                self._d(r, "Monto Depósito", "Monto Deposito"),
                                self._d(r, "Comisión Base (%)"),
                                self._d(r, "Comisión Base ($)"),
                                self._d(r, "Sobre tasa (%)"),
                                self._d(r, "Sobre tasa ($)"),
                                self._d(r, "Comisión Total ($)"),
                                self._d(r, "IVA Comisiones (16%)"),
                                self._d(r, "Comisiones + IVA"),
                                self._s(r, "Banco"),
                                self._s(r, "Marca"),
                                self._s(r, "Tipo de Venta"),
                                self._s(r, "Tipo de Tarjeta"),
                                self._s(r, "Código de Autorización"),
                                self._s(r, "Order ID", "OrderID"),
                                self._s(r, "Referencia Deposito y Store ID"),
                                self._s(r, "Referencia"),
                                hash_hex,
                            ),
                        )
                        inserted_final += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0

            print(
                f"[SQL_OK] importacion_id={importacion_id} "
                f"staging_rows={inserted_stage} final_inserted={inserted_final} final_duplicate_skipped={skipped_dup} "
                f"tipo_reporte={report_type}"
            )


    def get_active_netpay_credentials(self) -> dict | None:
        """
        Lee credenciales NetPay canonizadas desde SQL.
        Tabla: Finanzas_AdquirenteConectorCredenciales.
        Fallback a .env se maneja en pipeline.py.
        """
        if not self.settings.edarsahub_sql_host:
            return None

        connector_id = getattr(self.settings, "netpay_connector_id", 0) or 0

        with sql_connection(self.settings) as conn:
            cur = conn.cursor()

            if connector_id:
                cur.execute(
                    """
                    SELECT TOP 1
                        cr.CredencialID,
                        cr.ConectorID,
                        cr.Usuario,
                        cr.SecretoCifrado,
                        cr.MetadataJsonSeguro
                    FROM Finanzas_AdquirenteConectorCredenciales cr
                    INNER JOIN Finanzas_AdquirenteConectores co
                        ON co.ConectorID = cr.ConectorID
                    WHERE
                        cr.Activo = 1
                        AND co.Activo = 1
                        AND cr.ConectorID = %s
                    ORDER BY cr.CredencialID DESC
                    """,
                    (connector_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT TOP 1
                        cr.CredencialID,
                        cr.ConectorID,
                        cr.Usuario,
                        cr.SecretoCifrado,
                        cr.MetadataJsonSeguro
                    FROM Finanzas_AdquirenteConectorCredenciales cr
                    INNER JOIN Finanzas_AdquirenteConectores co
                        ON co.ConectorID = cr.ConectorID
                    WHERE
                        cr.Activo = 1
                        AND co.Activo = 1
                        AND (
                            UPPER(co.NombreConector) LIKE '%NETPAY%'
                            OR UPPER(co.TipoConector) LIKE '%PORTAL%'
                        )
                    ORDER BY cr.CredencialID DESC
                    """
                )

            row = cur.fetchone()
            if not row:
                return None

            secret = row.get("SecretoCifrado")
            if isinstance(secret, bytes):
                try:
                    secret = secret.decode("utf-8")
                except UnicodeDecodeError:
                    secret = secret.hex()

            return {
                "credencial_id": row.get("CredencialID"),
                "conector_id": row.get("ConectorID"),
                "usuario": row.get("Usuario"),
                "secreto_cifrado": secret,
                "metadata": row.get("MetadataJsonSeguro"),
            }
