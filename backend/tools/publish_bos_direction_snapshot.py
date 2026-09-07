from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from core.bos_direction_snapshot_publisher import publish_direction_snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Publish BOS V1.0 Direction status snapshot')
    parser.add_argument('--results-dir', required=True)
    parser.add_argument('--output-file', required=True)
    parser.add_argument('--generated-at-utc', required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshot = publish_direction_snapshot(
        results_dir=args.results_dir,
        output_file=args.output_file,
        generated_at_utc=args.generated_at_utc,
    )
    print(f"schema={snapshot['schema']} percent_complete={snapshot['percent_complete']} certified={snapshot['certified']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
