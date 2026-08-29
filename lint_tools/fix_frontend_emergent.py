import sys, asyncio, re, os
sys.path.insert(0, '/opt/plugins-venv/lib/python3.11/site-packages')
from linters.lint_tools import run_javascript_oxlint_linter

FRONT = '/app/frontend'

def get_errors():
    r = asyncio.run(run_javascript_oxlint_linter(['src', 'plugins', 'scripts'], trigger='manual', exclude_patterns=None, fix=False))
    return r.errors

def relpath(p):
    # errors come as 'frontend/src/..' ; cwd is /app/frontend
    if p.startswith('frontend/'):
        p = p[len('frontend/'):]
    return os.path.join(FRONT, p)

def fix_safe_array(errors):
    changed = set()
    # group receiver.method per file
    per_file = {}
    for e in errors:
        if 'safe-array-method-call' not in e:
            continue
        loc = re.search(r'(frontend/\S+?):(\d+):(\d+)', e)
        expr = re.search(r"'([^']+?)\.(\w+)\(\)'", e)
        if not loc or not expr:
            continue
        f = relpath(loc.group(1))
        receiver, method = expr.group(1), expr.group(2)
        per_file.setdefault(f, set()).add((receiver, method))
    for f, calls in per_file.items():
        if not os.path.exists(f):
            continue
        src = open(f, encoding='utf-8').read()
        for receiver, method in calls:
            needle = f"{receiver}.{method}("
            wrapped = f"({receiver} || []).{method}("
            # regex: not preceded by word char/dot/$, exact receiver.method(
            pat = re.compile(r'(?<![\w$.])' + re.escape(needle))
            # avoid re-wrapping: skip if already wrapped form present at that spot
            def repl(m):
                return wrapped
            newsrc, n = pat.subn(repl, src)
            if n:
                src = newsrc
        open(f, 'w', encoding='utf-8').write(src)
        changed.add(f)
    return changed

def fix_data_testid(errors):
    changed = set()
    # collect per file: list of (line, col, tag)
    per_file = {}
    for e in errors:
        if 'require-data-testid' not in e:
            continue
        loc = re.search(r'(frontend/\S+?):(\d+):(\d+)', e)
        tagm = re.search(r'<(\w+)>', e)
        if not loc or not tagm:
            continue
        f = relpath(loc.group(1))
        per_file.setdefault(f, []).append((int(loc.group(2)), int(loc.group(3)), tagm.group(1)))
    for f, items in per_file.items():
        if not os.path.exists(f):
            continue
        lines = open(f, encoding='utf-8').read().splitlines(keepends=True)
        base = os.path.splitext(os.path.basename(f))[0].lower()
        base = re.sub(r'[^a-z0-9]+', '-', base).strip('-')
        # process from bottom to top to preserve offsets
        for line, col, tag in sorted(items, key=lambda x: (-x[0], -x[1])):
            idx = line - 1
            if idx >= len(lines):
                continue
            ln = lines[idx]
            tagtoken = f"<{tag}"
            pos = ln.find(tagtoken, max(0, col - 1))
            if pos == -1:
                pos = ln.find(tagtoken)
            if pos == -1:
                continue
            insert_at = pos + len(tagtoken)
            # skip if already has data-testid right after (idempotent-ish)
            testid = f'{base}-{tag}-{line}'
            attr = f' data-testid="{testid}"'
            ln = ln[:insert_at] + attr + ln[insert_at:]
            lines[idx] = ln
        open(f, 'w', encoding='utf-8').write(''.join(lines))
        changed.add(f)
    return changed

def main():
    for _ in range(4):
        errors = get_errors()
        sa = [e for e in errors if 'safe-array-method-call' in e]
        dt = [e for e in errors if 'require-data-testid' in e]
        print(f"pass: safe-array={len(sa)} data-testid={len(dt)} total={len(errors)}")
        if not sa and not dt:
            break
        c1 = fix_safe_array(errors)
        c2 = fix_data_testid(errors)
        print("  files changed:", len(c1 | c2))
    # final report
    errors = get_errors()
    print("REMAINING TOTAL:", len(errors))
    for e in errors:
        print("REMAIN:", e[:200])

main()
