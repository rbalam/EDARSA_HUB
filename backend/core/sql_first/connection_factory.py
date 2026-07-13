from core.config.edarsahub_config import get_edarsahub_sql_config

ODBC_DRIVER_NAME = "ODBC Driver 17 for SQL Server"


def _connect_edarsahub_pymssql(
    cfg,
    *,
    timeout: int = 30,
    login_timeout: int = 10,
    autocommit: bool = False,
    tds_version: str | None = None,
):
    import pymssql

    connect_kwargs = {
        "server": cfg.host,
        "port": cfg.port,
        "user": cfg.user,
        "password": cfg.password,
        "database": cfg.database,
        "login_timeout": login_timeout,
        "timeout": timeout,
        "autocommit": autocommit,
    }

    if tds_version is not None:
        connect_kwargs["tds_version"] = tds_version

    return pymssql.connect(**connect_kwargs)


def get_edarsahub_connection(profile: str = "default"):
    """
    Abre una conexion canonica a EDARSAHUB.

    Solo usa pymssql como fallback cuando pyodbc no puede importarse
    o cuando el driver ODBC requerido no esta instalado.

    Los errores reales de conexion pyodbc se propagan sin fallback.
    """
    cfg = get_edarsahub_sql_config(profile)

    try:
        import pyodbc
    except ImportError:
        return _connect_edarsahub_pymssql(
            cfg,
            tds_version="7.0",
        )

    installed_drivers = set(pyodbc.drivers())

    if ODBC_DRIVER_NAME not in installed_drivers:
        return _connect_edarsahub_pymssql(
            cfg,
            tds_version="7.0",
        )

    return pyodbc.connect(
        f"DRIVER={{{ODBC_DRIVER_NAME}}};"
        f"SERVER={cfg.host},{cfg.port};"
        f"DATABASE={cfg.database};"
        f"UID={cfg.user};"
        f"PWD={cfg.password};"
        "TrustServerCertificate=yes;Encrypt=no;"
    )


def get_edarsahub_pymssql_connection(
    timeout: int = 30,
    login_timeout: int = 10,
    autocommit: bool = False,
):
    """
    Conexion EDARSAHUB centralizada via pymssql.

    Se conserva para modulos legacy que usan cursor(as_dict=True).
    """
    cfg = get_edarsahub_sql_config()

    return _connect_edarsahub_pymssql(
        cfg,
        timeout=timeout,
        login_timeout=login_timeout,
        autocommit=autocommit,
    )

def get_external_sql_connection(config: dict):
    """
    Conexión centralizada a servidores externos.
    No lee secretos de variables.
    No imprime secretos.
    """
    if not config:
        raise ValueError("Config externa requerida")

    host = config.get("host") or config.get("server") or config.get("servidor")
    port = int(config.get("port") or config.get("puerto") or 1433)
    database = config.get("database_name") or config.get("database") or config.get("base_datos") or config.get("bd")
    username = config.get("username") or config.get("usuario") or config.get("user")
    password = config.get("password_decrypted") or config.get("password") or config.get("pwd")

    if not host or not database or not username or not password:
        raise ValueError("Config externa incompleta: host/database/username/password requeridos")

    try:
        import pymssql
        return pymssql.connect(
            server=host,
            port=port,
            user=username,
            password=password,
            database=database,
            login_timeout=10,
            timeout=30,
            tds_version="7.0",
        )
    except Exception:
        import pyodbc
        return pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={host},{port};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            "TrustServerCertificate=yes;Encrypt=no;"
        )
