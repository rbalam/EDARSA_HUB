"""
Parser de host SQL.
No abre conexiones.
"""

def parse_sql_host(host_value, default_port=1433):
    if not host_value:
        return None, default_port

    text = str(host_value).strip()

    if "," in text:
        host, port = text.rsplit(",", 1)
        try:
            return host.strip(), int(port.strip())
        except Exception:
            return host.strip(), default_port

    if ":" in text:
        host, port = text.rsplit(":", 1)
        try:
            return host.strip(), int(port.strip())
        except Exception:
            return host.strip(), default_port

    return text, default_port

def build_host_port(host, port=1433):
    host, parsed_port = parse_sql_host(host, port)
    return host, parsed_port
