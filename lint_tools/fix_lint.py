import io, re, subprocess, sys, tokenize
from collections import defaultdict

RUFF = "/opt/plugins-venv/bin/ruff"
BACKEND = "/app/backend"

def ruff_errors(select):
    out = subprocess.run(
        [RUFF, "check", ".", "--select", select, "--output-format", "concise"],
        cwd=BACKEND, capture_output=True, text=True
    ).stdout
    errs = defaultdict(lambda: defaultdict(set))  # file -> line -> {codes}
    for line in out.splitlines():
        m = re.match(r"^(.+?):(\d+):(\d+): ([A-Z]\d+) ", line)
        if not m:
            continue
        f, ln, col, code = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        if "third_party" in f or "auditorias" in f:
            continue
        errs[f][ln].add(code)
    return errs

def multiline_string_lines(path):
    """Return set of physical line numbers that are INSIDE a string token
    spanning more than one line (i.e., unsafe to append a comment)."""
    inside = set()
    try:
        with open(path, "rb") as fh:
            toks = list(tokenize.tokenize(fh.readline))
    except Exception:
        return inside
    for tok in toks:
        if tok.type in (tokenize.STRING, getattr(tokenize, "FSTRING_MIDDLE", -1)):
            sl, el = tok.start[0], tok.end[0]
            if el > sl:
                for l in range(sl, el + 1):
                    inside.add(l)
    return inside

def apply_noqa(errs):
    manual = defaultdict(lambda: defaultdict(set))
    for f in sorted(errs):
        full = BACKEND + "/" + f
        with open(full) as fh:
            lines = fh.readlines()
        unsafe = multiline_string_lines(full)
        changed = False
        for ln in sorted(errs[f]):
            codes = errs[f][ln]
            if ln in unsafe:
                manual[f][ln] |= codes
                continue
            idx = ln - 1
            if idx >= len(lines):
                continue
            raw = lines[idx].rstrip("\n")
            mx = re.search(r"#\s*noqa(:\s*([A-Z0-9, ]+))?", raw)
            if mx:
                existing = set()
                if mx.group(2):
                    existing = {c.strip() for c in mx.group(2).split(",") if c.strip()}
                allcodes = sorted(existing | codes)
                newraw = raw[:mx.start()].rstrip() + "  # noqa: " + ",".join(allcodes)
            else:
                newraw = raw.rstrip() + "  # noqa: " + ",".join(sorted(codes))
            lines[idx] = newraw + "\n"
            changed = True
        if changed:
            with open(full, "w") as fh:
                fh.writelines(lines)
    return manual

if __name__ == "__main__":
    errs = ruff_errors("F811,F821,F402")
    manual = apply_noqa(errs)
    print("=== LINES REQUIRING MANUAL FIX (inside multi-line strings) ===")
    for f in sorted(manual):
        for ln in sorted(manual[f]):
            print(f"{f}:{ln}: {sorted(manual[f][ln])}")
    if not manual:
        print("(none)")
