"""
Meridian probe runner. Executed in an isolated subprocess (python -I).

Usage:  python -I runner.py <sandbox-dir>

The sandbox contains:
  spec.json     probe specification
  producer/     clean tree of the producer at its deployed commit
  consumer/     clean tree of the consumer at its deployed commit

The runner only reports observations as JSON lines. It never decides PASS or
FAIL; the Meridian engine evaluates the observations deterministically.
"""

import importlib.util
import json
import sys
import time
import traceback
from pathlib import Path


def emit(**record):
    record["t"] = round(time.perf_counter(), 4)
    print(json.dumps(record), flush=True)


def load(root: Path, entrypoint: str, alias: str):
    rel, func = entrypoint.split(":")
    module_path = root / rel
    sys.path.insert(0, str(module_path.parent))
    spec = importlib.util.spec_from_file_location(alias, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.path.pop(0)
    return getattr(module, func)


def main() -> int:
    sandbox = Path(sys.argv[1]).resolve()
    spec = json.loads((sandbox / "spec.json").read_text(encoding="utf-8"))
    p, c = spec["producer"], spec["consumer"]

    try:
        produce = load(sandbox / "producer", p["entrypoint"], "meridian_producer")
        emit(step="load-producer", status="ok",
             detail=f"{p['component']} {p['label']} @ {p['commit']} :: {p['entrypoint']}")
        consume = load(sandbox / "consumer", c["entrypoint"], "meridian_consumer")
        emit(step="load-consumer", status="ok",
             detail=f"{c['component']} {c['version']} @ {c['commit']} :: {c['entrypoint']}")
    except Exception as exc:  # noqa: BLE001 - report, never crash silently
        emit(step="load", status="error", detail=f"{type(exc).__name__}: {exc}",
             trace=traceback.format_exc(limit=3))
        return 3

    for fixture in spec["fixtures"]:
        record = {"step": "fixture", "fixture": fixture["id"]}
        try:
            message = produce(dict(fixture["event"]), dict(p.get("config") or {}))
            record["producer"] = message
        except Exception as exc:  # noqa: BLE001
            record["producer_error"] = f"{type(exc).__name__}: {exc}"
            emit(**record)
            continue
        if message.get("outcome") == "DELIVER" and message.get("record") is not None:
            try:
                record["consumer"] = consume(message["record"])
            except Exception as exc:  # noqa: BLE001
                record["consumer_error"] = f"{type(exc).__name__}: {exc}"
        emit(**record)

    emit(step="done", status="ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
