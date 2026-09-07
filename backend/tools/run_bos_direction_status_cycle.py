from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from core.bos_direction_status_cycle import run_direction_status_cycle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run one BOS Direction status publication cycle')
    parser.add_argument('--results-dir', required=True)
    parser.add_argument('--status-root', required=True)
    parser.add_argument('--generated-at-utc', required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_direction_status_cycle(args.results_dir, args.status_root, args.generated_at_utc)
    snapshot = result['snapshot']
    print(f"schema={snapshot['schema']} percent_complete={snapshot['percent_complete']} certified={snapshot['certified']} history={result['history_file']} latest={result['latest_file']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
