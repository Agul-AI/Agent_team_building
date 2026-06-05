"""Console entry point for the local API skeleton."""

from __future__ import annotations

import argparse

from team_factory.api.app import serve


def main(argv: list[str] | None = None) -> int:
    """Run the local API skeleton."""

    parser = argparse.ArgumentParser(description="Serve the local Agent Team Factory API skeleton.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--spec-root", default=".")
    parser.add_argument("--audit-log", default="examples/artifacts/api_audit.jsonl")
    parser.add_argument("--eval-output-dir", default="examples/artifacts/evaluation_reports")
    args = parser.parse_args(argv)
    serve(
        host=args.host,
        port=args.port,
        spec_root=args.spec_root,
        audit_log_path=args.audit_log,
        eval_output_dir=args.eval_output_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
