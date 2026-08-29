import re, subprocess

out = subprocess.run(
    ["/opt/plugins-venv/bin/ruff", "check", ".", "--select", "E722", "--output-format", "concise"],
    cwd="/app/backend", capture_output=True, text=True
).stdout

files = set()
for line in out.splitlines():
    if ":" in line and "E722" in line:
        path = line.split(":")[0]
        if "third_party" in path or "auditorias" in path:
            continue
        files.add(path)

pat = re.compile(r'^(\s*)except\s*:\s*(#.*)?$')
total = 0
for f in sorted(files):
    full = "/app/backend/" + f
    with open(full) as fh:
        lines = fh.readlines()
    changed = False
    for i, ln in enumerate(lines):
        m = pat.match(ln.rstrip("\n"))
        if m:
            indent = m.group(1)
            comment = (" " + m.group(2)) if m.group(2) else ""
            lines[i] = f"{indent}except Exception:{comment}\n"
            changed = True
            total += 1
    if changed:
        with open(full, "w") as fh:
            fh.writelines(lines)
print("E722 replaced:", total)
